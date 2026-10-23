package api

import (
	"encoding/base64"
	"fmt"
	"net/http"
)

func (a *API) terminalRoutes(m *http.ServeMux) {
	if a.Terminal == nil {
		return
	}

	m.HandleFunc("POST /api/v1/terminal/session", func(w http.ResponseWriter, r *http.Request) {
		var v struct{ Cwd string }
		Read(w, r, &v)
		session, err := a.Terminal.CreateSession(v.Cwd)
		if err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 201, map[string]string{"session_id": session.ID})
	})

	m.HandleFunc("POST /api/v1/terminal/input", func(w http.ResponseWriter, r *http.Request) {
		var v struct {
			SessionID string `json:"session_id"`
			Data      string `json:"data"`
		}
		if !Read(w, r, &v) {
			return
		}
		session, ok := a.Terminal.GetSession(v.SessionID)
		if !ok {
			http.Error(w, `{"error":"session not found"}`, 404)
			return
		}
		if err := session.WriteInput([]byte(v.Data)); err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, map[string]string{"status": "ok"})
	})

	m.HandleFunc("GET /api/v1/terminal/events", func(w http.ResponseWriter, r *http.Request) {
		sessionID := r.URL.Query().Get("session_id")
		session, ok := a.Terminal.GetSession(sessionID)
		if !ok {
			http.Error(w, `{"error":"session not found"}`, 404)
			return
		}

		flusher, ok := w.(http.Flusher)
		if !ok {
			http.Error(w, "streaming unsupported", 500)
			return
		}

		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache")
		w.Header().Set("Connection", "keep-alive")
		w.WriteHeader(200)
		flusher.Flush()

		ch := session.Subscribe()
		defer session.Unsubscribe(ch)

		notify := r.Context().Done()
		for {
			select {
			case <-notify:
				return
			case data, open := <-ch:
				if !open {
					fmt.Fprintf(w, "event: close\ndata: session closed\n\n")
					flusher.Flush()
					return
				}
				encoded := base64.StdEncoding.EncodeToString(data)
				fmt.Fprintf(w, "data: %s\n\n", encoded)
				flusher.Flush()
			}
		}
	})

	m.HandleFunc("POST /api/v1/terminal/kill", func(w http.ResponseWriter, r *http.Request) {
		var v struct {
			SessionID string `json:"session_id"`
		}
		if !Read(w, r, &v) {
			return
		}
		a.Terminal.RemoveSession(v.SessionID)
		JSON(w, 200, map[string]string{"status": "closed"})
	})
}
