package api

import (
	"net/http"
)

func (a *API) ingestionRoutes(m *http.ServeMux) {
	m.HandleFunc("GET /api/v1/ingestion/jobs", func(w http.ResponseWriter, r *http.Request) {
		if a.Store == nil {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "ingestion job store is unavailable"})
			return
		}
		jobs, err := a.Store.IngestionJobs()
		if err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not read ingestion jobs"})
			return
		}
		JSON(w, http.StatusOK, jobs)
	})
}
