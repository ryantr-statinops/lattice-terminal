package api

import (
	"net/http"
	"strings"
	"time"

	"kestrel-terminal/gateway/internal/store"
)

func (a *API) instrumentAliasRoutes(m *http.ServeMux) {
	m.HandleFunc("GET /api/v1/market/instrument-aliases", func(w http.ResponseWriter, r *http.Request) {
		if a.Store == nil {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "instrument registry is unavailable"})
			return
		}
		aliases, err := a.Store.ProviderInstrumentAliases(r.URL.Query().Get("provider_id"), r.URL.Query().Get("provider_instrument_id"))
		if err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not read instrument aliases"})
			return
		}
		JSON(w, http.StatusOK, aliases)
	})

	m.HandleFunc("PUT /api/v1/market/instrument-aliases", func(w http.ResponseWriter, r *http.Request) {
		if a.Store == nil {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "instrument registry is unavailable"})
			return
		}
		var alias store.ProviderInstrumentAlias
		if !Read(w, r, &alias) {
			return
		}
		if strings.TrimSpace(alias.ProviderID) == "" || strings.TrimSpace(alias.ProviderInstrumentID) == "" {
			JSON(w, http.StatusBadRequest, map[string]string{"error": "provider identity is required"})
			return
		}
		if err := a.Store.PutProviderInstrumentAlias(alias); err != nil {
			JSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
			return
		}
		w.WriteHeader(http.StatusNoContent)
	})

	m.HandleFunc("GET /api/v1/market/instrument-aliases/resolve", func(w http.ResponseWriter, r *http.Request) {
		if a.Store == nil {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "instrument registry is unavailable"})
			return
		}
		at, err := time.Parse(time.RFC3339Nano, r.URL.Query().Get("at"))
		if err != nil || strings.TrimSpace(r.URL.Query().Get("provider_id")) == "" || strings.TrimSpace(r.URL.Query().Get("provider_instrument_id")) == "" {
			JSON(w, http.StatusBadRequest, map[string]string{"error": "provider identity and RFC3339 at timestamp are required"})
			return
		}
		alias, err := a.Store.ResolveProviderInstrument(r.URL.Query().Get("provider_id"), r.URL.Query().Get("provider_instrument_id"), at)
		if err != nil {
			http.NotFound(w, r)
			return
		}
		JSON(w, http.StatusOK, alias)
	})
}
