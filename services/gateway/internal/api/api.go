package api

import (
	"encoding/json"
	"fmt"
	"io"
	"kestrel-terminal/gateway/internal/host"
	"kestrel-terminal/gateway/internal/store"
	"kestrel-terminal/gateway/internal/terminal"
	"kestrel-terminal/gateway/internal/workspace"
	"net/http"
	"strconv"
	"sync"
	"time"
)

type API struct {
	Store       *store.Store
	Credentials CredentialWriter
	Workspace   workspace.Workspace
	Valid       func(*http.Request) bool
	StartRun    func(store.Run)
	StopRun     func(string)
	Inspect     func(string, string, json.RawMessage) error
	Engine      *Runner
	Terminal    *terminal.Manager
	paperMu     sync.Mutex
	routingMu   sync.Mutex
}

type CredentialWriter interface {
	Set(provider, service string, credential []byte) error
	Delete(provider, service string) error
}

type CredentialPresence interface {
	HasProvider(provider string) (bool, error)
}

type CredentialReader interface {
	Get(provider, service string) ([]byte, error)
}

func JSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(value)
}
func Read(w http.ResponseWriter, r *http.Request, v any) bool {
	r.Body = http.MaxBytesReader(w, r.Body, 2*1024*1024)
	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(v); err != nil {
		JSON(w, 400, map[string]string{"error": "invalid request"})
		return false
	}
	if decoder.Decode(new(any)) != io.EOF {
		JSON(w, 400, map[string]string{"error": "request must contain one JSON value"})
		return false
	}
	return true
}
func Fail(w http.ResponseWriter, err error) { JSON(w, 400, map[string]string{"error": err.Error()}) }
func (a *API) Routes(m *http.ServeMux) {
	a.fundRoutes(m)
	a.paperRoutes(m)
	a.portfolioRoutes(m)
	a.recoveryRoutes(m)
	a.artifactRoutes(m)
	a.reportRoutes(m)
	a.terminalRoutes(m)
	a.providerRoutes(m)
	a.instrumentAliasRoutes(m)
	m.HandleFunc("GET /api/v1/workspaces/{kind}", func(w http.ResponseWriter, r *http.Request) {
		files, err := a.Workspace.List(r.PathValue("kind"))
		if err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, files)
	})
	m.HandleFunc("GET /api/v1/workspaces/{kind}/file", func(w http.ResponseWriter, r *http.Request) {
		text, err := a.Workspace.Read(r.PathValue("kind"), r.URL.Query().Get("path"))
		if err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, map[string]string{"content": text})
	})
	m.HandleFunc("PUT /api/v1/workspaces/{kind}/file", func(w http.ResponseWriter, r *http.Request) {
		var v struct {
			Path, Content string
			Directory     bool
		}
		if !Read(w, r, &v) {
			return
		}
		if err := a.Workspace.Write(r.PathValue("kind"), v.Path, v.Content, v.Directory); err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, map[string]string{"status": "saved"})
	})
	m.HandleFunc("POST /api/v1/workspaces/{kind}/rename", func(w http.ResponseWriter, r *http.Request) {
		var v struct{ From, To string }
		if !Read(w, r, &v) {
			return
		}
		if err := a.Workspace.Rename(r.PathValue("kind"), v.From, v.To); err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, map[string]string{"status": "renamed"})
	})
	m.HandleFunc("DELETE /api/v1/workspaces/{kind}/file", func(w http.ResponseWriter, r *http.Request) {
		if err := a.Workspace.Delete(r.PathValue("kind"), r.URL.Query().Get("path")); err != nil {
			Fail(w, err)
			return
		}
		w.WriteHeader(204)
	})
	m.HandleFunc("GET /api/v1/workspaces/{kind}/mount", func(w http.ResponseWriter, r *http.Request) {
		kind := r.PathValue("kind")
		path, ok := a.Workspace.GetMount(kind)
		JSON(w, 200, map[string]any{"kind": kind, "path": path, "mounted": ok})
	})
	m.HandleFunc("POST /api/v1/workspaces/{kind}/mount", func(w http.ResponseWriter, r *http.Request) {
		kind := r.PathValue("kind")
		var v struct{ Path string }
		if !Read(w, r, &v) {
			return
		}
		mountedPath, err := a.Workspace.Mount(kind, v.Path)
		if err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, map[string]any{"kind": kind, "path": mountedPath, "mounted": true})
	})
	m.HandleFunc("DELETE /api/v1/workspaces/{kind}/mount", func(w http.ResponseWriter, r *http.Request) {
		kind := r.PathValue("kind")
		if err := a.Workspace.Unmount(kind); err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, map[string]any{"kind": kind, "mounted": false})
	})
	m.HandleFunc("GET /api/v1/runs", func(w http.ResponseWriter, r *http.Request) {
		runs, err := a.Store.Runs(r.URL.Query().Get("kind"))
		if err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, runs)
	})
	m.HandleFunc("POST /api/v1/runs", func(w http.ResponseWriter, r *http.Request) {
		if a.StartRun == nil {
			JSON(w, 503, map[string]string{"error": "runner not installed"})
			return
		}
		var v struct {
			Kind, File string
			Params     json.RawMessage
		}
		if !Read(w, r, &v) {
			return
		}
		if len(v.Params) == 0 {
			v.Params = json.RawMessage(`{}`)
		}
		var object map[string]any
		if json.Unmarshal(v.Params, &object) != nil || object == nil {
			JSON(w, 400, map[string]string{"error": "parameters must be an object"})
			return
		}
		if a.Inspect != nil {
			source, err := a.Workspace.Read(v.Kind, v.File)
			if err != nil {
				Fail(w, err)
				return
			}
			if err = a.Inspect(v.Kind, source, v.Params); err != nil {
				Fail(w, err)
				return
			}
		}
		prepared := store.Run{Kind: v.Kind, Params: v.Params}
		if err := a.prepareStrategy(&prepared); err != nil {
			Fail(w, err)
			return
		}
		v.Params = prepared.Params
		snapshot, err := a.Workspace.Snapshot(v.Kind, v.File, v.Params)
		if err != nil {
			Fail(w, err)
			return
		}
		if err = a.validateBacktest(v.Kind, snapshot, v.Params); err != nil {
			Fail(w, err)
			return
		}
		run := store.Run{ID: host.Token(), Kind: v.Kind, File: v.File, Snapshot: snapshot, Params: v.Params}
		if err = a.bindStrategy(run); err != nil {
			Fail(w, err)
			return
		}
		if err = a.Store.CreateRun(run); err != nil {
			a.FinishPaper(run)
			Fail(w, err)
			return
		}
		run, _ = a.Store.Run(run.ID)
		a.StartRun(run)
		JSON(w, 202, run)
	})
	m.HandleFunc("GET /api/v1/runs/{id}", func(w http.ResponseWriter, r *http.Request) {
		v, err := a.Store.Run(r.PathValue("id"))
		if err != nil {
			http.NotFound(w, r)
			return
		}
		JSON(w, 200, v)
	})
	m.HandleFunc("POST /api/v1/runs/{id}/stop", func(w http.ResponseWriter, r *http.Request) {
		if a.StopRun == nil {
			JSON(w, 503, map[string]string{"error": "runner not installed"})
			return
		}
		a.StopRun(r.PathValue("id"))
		w.WriteHeader(202)
	})
	m.HandleFunc("GET /api/v1/runs/{id}/events", a.events)
}
func (a *API) events(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	if _, err := a.Store.Run(id); err != nil {
		http.NotFound(w, r)
		return
	}
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "stream unavailable", 500)
		return
	}
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("X-Accel-Buffering", "no")
	after, _ := strconv.ParseInt(r.Header.Get("Last-Event-ID"), 10, 64)
	ticker := time.NewTicker(250 * time.Millisecond)
	defer ticker.Stop()
	for {
		if a.Valid != nil && !a.Valid(r) {
			return
		}
		events, err := a.Store.Events(id, after)
		if err != nil {
			return
		}
		for _, event := range events {
			b, _ := json.Marshal(event)
			fmt.Fprintf(w, "id: %d\nevent: run\ndata: %s\n\n", event.Seq, b)
			after = event.Seq
		}
		fmt.Fprint(w, ": heartbeat\n\n")
		flusher.Flush()
		run, err := a.Store.Run(id)
		if err != nil {
			return
		}
		if len(events) < 200 && (run.Status == "completed" || run.Status == "failed" || run.Status == "cancelled" || run.Status == "interrupted") {
			return
		}
		select {
		case <-r.Context().Done():
			return
		case <-ticker.C:
		}
	}
}
