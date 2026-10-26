package api

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"os"
	"time"

	"kestrel-terminal/gateway/internal/secret"
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
		if a.Engine == nil || a.Engine.Engine == nil {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "engine unavailable"})
			return
		}
		var statuses []map[string]any
		if err := a.Engine.call(r.Context(), "GET", "/providers", nil, &statuses); err != nil {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "could not read provider status"})
			return
		}
		reader, canRead := a.Credentials.(CredentialPresence)
		for _, status := range statuses {
			provider, _ := status["id"].(string)
			configured := false
			if canRead {
				var err error
				configured, err = reader.HasProvider(provider)
				if err != nil {
					JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "could not read provider configuration state"})
					return
				}
			}
			status["configured"] = configured
		}
		JSON(w, http.StatusOK, statuses)
	})

	m.HandleFunc("GET /api/v1/providers/capabilities", func(w http.ResponseWriter, r *http.Request) {
		callEngine(w, r, "GET", "/internal/v1/providers/capabilities", nil)
	})

	m.HandleFunc("POST /api/v1/providers/{id}/ping", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		if !secret.ValidVaultID(id) {
			JSON(w, http.StatusBadRequest, map[string]string{"error": "invalid provider reference"})
			return
		}
		if id == "ssi" {
			reader, ok := a.Credentials.(CredentialReader)
			if !ok {
				JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "provider credential vault is unavailable"})
				return
			}
			credential, err := reader.Get(id, "market-data")
			if err != nil {
				if errors.Is(err, os.ErrNotExist) {
					JSON(w, http.StatusBadRequest, map[string]string{"error": "SSI market-data credentials are not configured"})
					return
				}
				JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "could not read SSI market-data credentials"})
				return
			}
			if !json.Valid(credential) {
				JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "SSI market-data credentials are invalid"})
				return
			}
			body, err := json.Marshal(struct {
				Service    string          `json:"service"`
				Credential json.RawMessage `json:"credential"`
			}{Service: "market-data", Credential: credential})
			if err != nil {
				JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not prepare SSI connection check"})
				return
			}
			callEngine(w, r, "POST", "/internal/v1/providers/ssi/ping", body)
			return
		}
		callEngine(w, r, "POST", "/internal/v1/providers/"+id+"/ping", nil)
	})

	m.HandleFunc("PUT /api/v1/providers/{id}/credentials", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "no-store")
		if a.Credentials == nil {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "credential vault is not initialized"})
			return
		}
		var input struct {
			Service    string          `json:"service"`
			Credential json.RawMessage `json:"credential"`
		}
		if !Read(w, r, &input) {
			return
		}
		var document map[string]json.RawMessage
		if !secret.ValidVaultID(r.PathValue("id")) || !secret.ValidVaultID(input.Service) || len(input.Credential) == 0 || len(input.Credential) > 1024*1024 || json.Unmarshal(input.Credential, &document) != nil || len(document) == 0 {
			JSON(w, http.StatusBadRequest, map[string]string{"error": "invalid provider credential"})
			return
		}
		if err := a.Credentials.Set(r.PathValue("id"), input.Service, input.Credential); err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not save provider credentials"})
			return
		}
		w.WriteHeader(http.StatusNoContent)
	})

	m.HandleFunc("DELETE /api/v1/providers/{id}/credentials", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "no-store")
		if a.Credentials == nil {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "credential vault is not initialized"})
			return
		}
		provider, service := r.PathValue("id"), r.URL.Query().Get("service")
		if !secret.ValidVaultID(provider) || !secret.ValidVaultID(service) {
			JSON(w, http.StatusBadRequest, map[string]string{"error": "invalid provider credential reference"})
			return
		}
		if err := a.Credentials.Delete(provider, service); err != nil {
			if errors.Is(err, os.ErrNotExist) {
				JSON(w, http.StatusNotFound, map[string]string{"error": "provider credential not found"})
				return
			}
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not delete provider credentials"})
			return
		}
		w.WriteHeader(http.StatusNoContent)
	})

	m.HandleFunc("GET /api/v1/providers/routing", func(w http.ResponseWriter, r *http.Request) {
		if a.Store == nil {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "routing store is unavailable"})
			return
		}
		policy, err := a.Store.RoutingPolicy()
		if err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not read routing policy"})
			return
		}
		JSON(w, http.StatusOK, policy)
	})

	m.HandleFunc("PUT /api/v1/providers/routing", func(w http.ResponseWriter, r *http.Request) {
		if a.Store == nil || a.Engine == nil {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "routing service is unavailable"})
			return
		}
		a.routingMu.Lock()
		defer a.routingMu.Unlock()
		var patch struct {
			HistoricalProvider *string           `json:"historical_provider"`
			RealtimeProvider   *string           `json:"realtime_provider"`
			FinancialsProvider *string           `json:"financials_provider"`
			FallbackEnabled    *bool             `json:"fallback_enabled"`
			Datasets           map[string]string `json:"datasets"`
		}
		if !Read(w, r, &patch) {
			return
		}
		policy, err := a.Store.RoutingPolicy()
		if err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not read routing policy"})
			return
		}
		previous := policy
		changed := false
		if patch.HistoricalProvider != nil {
			if *patch.HistoricalProvider == "" {
				JSON(w, http.StatusBadRequest, map[string]string{"error": "routing provider is required"})
				return
			}
			policy.HistoricalProvider, changed = *patch.HistoricalProvider, true
		}
		if patch.RealtimeProvider != nil {
			if *patch.RealtimeProvider == "" {
				JSON(w, http.StatusBadRequest, map[string]string{"error": "routing provider is required"})
				return
			}
			policy.RealtimeProvider, changed = *patch.RealtimeProvider, true
		}
		if patch.FinancialsProvider != nil {
			if *patch.FinancialsProvider == "" {
				JSON(w, http.StatusBadRequest, map[string]string{"error": "routing provider is required"})
				return
			}
			policy.FinancialsProvider, changed = *patch.FinancialsProvider, true
		}
		if patch.FallbackEnabled != nil {
			policy.FallbackEnabled, changed = *patch.FallbackEnabled, true
		}
		if patch.Datasets != nil {
			policy.Datasets, changed = patch.Datasets, true
		}
		if !changed {
			JSON(w, http.StatusBadRequest, map[string]string{"error": "routing patch is empty"})
			return
		}
		if err = a.Engine.ApplyRoutingPolicy(policy); err != nil {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "could not apply routing policy to engine"})
			return
		}
		if err = a.Store.SetRoutingPolicy(policy); err != nil {
			_ = a.Engine.ApplyRoutingPolicy(previous)
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not persist routing policy"})
			return
		}
		JSON(w, http.StatusOK, policy)
	})
}
