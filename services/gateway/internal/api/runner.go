package api

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"kestrel-terminal/gateway/internal/host"
	"kestrel-terminal/gateway/internal/store"
	"net/http"
	"sync"
	"time"
)

type Runner struct {
	Engine   *host.Engine
	Store    *store.Store
	Context  context.Context
	mu       sync.Mutex
	wg       sync.WaitGroup
	stopped  map[string]bool
	OnEvent  func(store.Run, string, json.RawMessage) error
	OnFinish func(store.Run)
}

func (r *Runner) call(ctx context.Context, method, path string, input, output any) error {
	var body io.Reader
	if input != nil {
		b, err := json.Marshal(input)
		if err != nil {
			return err
		}
		body = bytes.NewReader(b)
	}
	req, err := http.NewRequestWithContext(ctx, method, r.Engine.URL+"/internal/v1"+path, body)
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+r.Engine.Token)
	req.Header.Set("Content-Type", "application/json")
	client := http.Client{Timeout: 10 * time.Second}
	response, err := client.Do(req)
	if err != nil {
		return errors.New("engine unavailable")
	}
	defer response.Body.Close()
	if response.StatusCode >= 400 {
		var payload struct {
			Error  string `json:"error"`
			Detail any    `json:"detail"`
		}
		_ = json.NewDecoder(response.Body).Decode(&payload)
		if payload.Error != "" {
			return errors.New(payload.Error)
		}
		return fmt.Errorf("engine rejected request (%d)", response.StatusCode)
	}
	if output != nil {
		return json.NewDecoder(io.LimitReader(response.Body, 2*1024*1024)).Decode(output)
	}
	return nil
}

func (r *Runner) ApplyRoutingPolicy(policy store.RoutingPolicy) error {
	if r.Engine == nil {
		return errors.New("engine unavailable")
	}
	ctx := r.Context
	if ctx == nil {
		ctx = context.Background()
	}
	return r.call(ctx, "PUT", "/providers/routing", policy, nil)
}

func (r *Runner) Inspect(kind, source string, params json.RawMessage) error {
	var p map[string]any
	_ = json.Unmarshal(params, &p)
	return r.call(r.Context, "POST", "/programs/inspect", map[string]any{"kind": kind, "source": source, "selected": p["kind_detection"] == "selected"}, nil)
}
func (r *Runner) Start(run store.Run) {
	r.wg.Add(1)
	go func() {
		defer r.wg.Done()
		defer func() { r.mu.Lock(); delete(r.stopped, run.ID); r.mu.Unlock() }()
		if r.OnFinish != nil {
			defer r.OnFinish(run)
		}
		var after int64
		fail := func(err error) {
			p, _ := json.Marshal(map[string]string{"message": err.Error()})
			_ = r.Store.Append(run.ID, store.Event{Seq: after + 1, Type: "error", Payload: p}, "")
			p, _ = json.Marshal(map[string]string{"status": "interrupted"})
			_ = r.Store.Append(run.ID, store.Event{Seq: after + 2, Type: "state", Payload: p}, "interrupted")
		}
		var params map[string]any
		_ = json.Unmarshal(run.Params, &params)
		timeout := 120
		if run.Kind == "backtest" {
			timeout = 600
		}
		if v, ok := params["timeout_seconds"].(float64); ok && v >= 1 && v <= 3600 {
			timeout = int(v)
		}
		if err := r.call(r.Context, "POST", "/runner/start", map[string]any{"id": run.ID, "kind": run.Kind, "snapshot": run.Snapshot, "timeout_seconds": timeout}, nil); err != nil {
			fail(err)
			return
		}
		for {
			r.mu.Lock()
			stop := r.stopped[run.ID]
			r.mu.Unlock()
			if stop {
				_ = r.call(r.Context, "POST", "/runner/"+run.ID+"/stop", map[string]any{}, nil)
			}
			var result struct {
				Events []struct {
					Seq     int64           `json:"seq"`
					Type    string          `json:"type"`
					Payload json.RawMessage `json:"payload"`
				} `json:"events"`
				Done bool `json:"done"`
			}
			if err := r.call(r.Context, "GET", fmt.Sprintf("/runner/%s/events?after=%d", run.ID, after), nil, &result); err != nil {
				fail(err)
				return
			}
			for _, event := range result.Events {
				if event.Seq != after+1 {
					fail(errors.New("engine event sequence gap"))
					return
				}
				if r.OnEvent != nil {
					if err := r.OnEvent(run, event.Type, event.Payload); err != nil {
						_ = r.call(r.Context, "POST", "/runner/"+run.ID+"/stop", map[string]any{}, nil)
						fail(err)
						return
					}
				}
				status := ""
				if event.Type == "state" {
					var p struct {
						Status string `json:"status"`
					}
					if json.Unmarshal(event.Payload, &p) != nil {
						fail(errors.New("invalid worker state"))
						return
					}
					status = p.Status
				}
				if err := r.Store.Append(run.ID, store.Event{Seq: event.Seq, Type: event.Type, Payload: event.Payload}, status); err != nil {
					fail(err)
					return
				}
				after = event.Seq
			}
			if result.Done && len(result.Events) == 0 {
				return
			}
			select {
			case <-r.Context.Done():
				fail(errors.New("local service stopped; run interrupted"))
				return
			case <-time.After(100 * time.Millisecond):
			}
		}
	}()
}
func (r *Runner) Wait() { r.wg.Wait() }
func (r *Runner) Stop(id string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.stopped == nil {
		r.stopped = map[string]bool{}
	}
	r.stopped[id] = true
}
