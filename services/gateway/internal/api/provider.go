package api

import (
	"bytes"
	"io"
	"net/http"
	"time"
)

func (a *API) providerRoutes(m *http.ServeMux) {
	callEngine := func(w http.ResponseWriter, r *http.Request, method, path string, body []byte) {
		if a.Engine == nil || a.Engine.Engine == nil {
			http.Error(w, `{"error":"engine unavailable"}`, 503)
			return
		}
		var reader io.Reader
		if len(body) > 0 {
			reader = bytes.NewReader(body)
		}
		req, err := http.NewRequestWithContext(r.Context(), method, a.Engine.Engine.URL+path, reader)
		if err != nil {
			Fail(w, err)
			return
		}
		req.Header.Set("Authorization", "Bearer "+a.Engine.Engine.Token)
		if len(body) > 0 {
			req.Header.Set("Content-Type", "application/json")
		}
		client := &http.Client{Timeout: 6 * time.Second}
		resp, err := client.Do(req)
		if err != nil {
			Fail(w, err)
			return
		}
		defer resp.Body.Close()
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(resp.StatusCode)
		io.Copy(w, resp.Body)
	}

	m.HandleFunc("GET /api/v1/providers", func(w http.ResponseWriter, r *http.Request) {
		callEngine(w, r, "GET", "/internal/v1/providers", nil)
	})

	m.HandleFunc("POST /api/v1/providers/{id}/ping", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		callEngine(w, r, "POST", "/internal/v1/providers/"+id+"/ping", nil)
	})

	m.HandleFunc("GET /api/v1/providers/routing", func(w http.ResponseWriter, r *http.Request) {
		callEngine(w, r, "GET", "/internal/v1/providers/routing", nil)
	})

	m.HandleFunc("PUT /api/v1/providers/routing", func(w http.ResponseWriter, r *http.Request) {
		body, err := io.ReadAll(r.Body)
		if err != nil {
			Fail(w, err)
			return
		}
		callEngine(w, r, "PUT", "/internal/v1/providers/routing", body)
	})
}
