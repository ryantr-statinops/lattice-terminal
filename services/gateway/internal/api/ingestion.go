package api

import (
	"encoding/json"
	"errors"
	"net/http"
	"os"
	"strings"
	"time"

	"kestrel-terminal/gateway/internal/host"
	"kestrel-terminal/gateway/internal/store"
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

	m.HandleFunc("POST /api/v1/ingestion/catalogues/ssi/hose-equity", func(w http.ResponseWriter, r *http.Request) {
		if a.Store == nil || a.Engine == nil || a.Engine.Engine == nil {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "SSI ingestion service is unavailable"})
			return
		}
		var input struct{}
		if !Read(w, r, &input) {
			return
		}
		reader, ok := a.Credentials.(CredentialReader)
		if !ok {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "provider credential vault is unavailable"})
			return
		}
		rawCredential, err := reader.Get("ssi", "market-data")
		if err != nil {
			if errors.Is(err, os.ErrNotExist) {
				JSON(w, http.StatusBadRequest, map[string]string{"error": "SSI market-data credentials are not configured"})
				return
			}
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "could not read SSI market-data credentials"})
			return
		}
		var credential map[string]string
		if json.Unmarshal(rawCredential, &credential) != nil || len(credential) == 0 {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "SSI market-data credentials are invalid"})
			return
		}

		job := store.IngestionJob{
			ID: host.Token(), ProviderID: "ssi", CapabilityID: "ssi:market-data:instruments.details:equity:HOSE",
			Dataset: "instruments.details", AssetClass: "equity", Venue: "HOSE",
		}
		if err = a.Store.CreateIngestionJob(job); err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not create SSI ingestion job"})
			return
		}
		if err = a.Store.UpdateIngestionJob(job.ID, "running", 0, 0, ""); err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not start SSI ingestion job"})
			return
		}
		var published struct {
			SnapshotID string `json:"snapshot_id"`
			RowCount   int64  `json:"row_count"`
		}
		err = a.Engine.callWithTimeout(r.Context(), http.MethodPost, "/market/catalogues/ssi/hose-equity", map[string]any{"credential": credential}, &published, 150*time.Second)
		if err != nil {
			_ = a.Store.UpdateIngestionJob(job.ID, "failed", 0, 0, "provider_request_failed")
			JSON(w, http.StatusBadGateway, map[string]string{"error": "SSI HOSE equity catalogue ingestion failed", "job_id": job.ID, "error_code": "provider_request_failed"})
			return
		}
		if published.RowCount < 1 || published.SnapshotID == "" {
			_ = a.Store.UpdateIngestionJob(job.ID, "failed", 0, 0, "invalid_provider_response")
			JSON(w, http.StatusBadGateway, map[string]string{"error": "SSI catalogue returned an invalid snapshot", "job_id": job.ID, "error_code": "invalid_provider_response"})
			return
		}
		if err = a.Store.UpdateIngestionJob(job.ID, "running", published.RowCount, published.RowCount, ""); err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not save SSI ingestion progress", "job_id": job.ID})
			return
		}
		if err = a.Store.UpdateIngestionJob(job.ID, "completed", published.RowCount, published.RowCount, ""); err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not complete SSI ingestion job", "job_id": job.ID})
			return
		}
		completed, err := a.Store.IngestionJob(job.ID)
		if err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not read completed SSI ingestion job"})
			return
		}
		JSON(w, http.StatusCreated, map[string]any{"job": completed, "snapshot_id": published.SnapshotID})
	})

	m.HandleFunc("POST /api/v1/ingestion/catalogues/ssi/hose-indices", func(w http.ResponseWriter, r *http.Request) {
		if a.Store == nil || a.Engine == nil || a.Engine.Engine == nil {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "SSI ingestion service is unavailable"})
			return
		}
		var input struct{}
		if !Read(w, r, &input) {
			return
		}
		reader, ok := a.Credentials.(CredentialReader)
		if !ok {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "provider credential vault is unavailable"})
			return
		}
		rawCredential, err := reader.Get("ssi", "market-data")
		if err != nil {
			if errors.Is(err, os.ErrNotExist) {
				JSON(w, http.StatusBadRequest, map[string]string{"error": "SSI market-data credentials are not configured"})
				return
			}
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "could not read SSI market-data credentials"})
			return
		}
		var credential map[string]string
		if json.Unmarshal(rawCredential, &credential) != nil || len(credential) == 0 {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "SSI market-data credentials are invalid"})
			return
		}

		job := store.IngestionJob{
			ID: host.Token(), ProviderID: "ssi", CapabilityID: "ssi:market-data:instruments.index:index:HOSE",
			Dataset: "instruments.index", AssetClass: "index", Venue: "HOSE",
		}
		if err = a.Store.CreateIngestionJob(job); err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not create SSI ingestion job"})
			return
		}
		if err = a.Store.UpdateIngestionJob(job.ID, "running", 0, 0, ""); err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not start SSI ingestion job"})
			return
		}
		var published struct {
			SnapshotID string `json:"snapshot_id"`
			RowCount   int64  `json:"row_count"`
		}
		// SSI documents up to ten pages; the gateway allows the complete retried page set.
		err = a.Engine.callWithTimeout(r.Context(), http.MethodPost, "/market/catalogues/ssi/hose-indices", map[string]any{"credential": credential}, &published, 420*time.Second)
		if err != nil {
			_ = a.Store.UpdateIngestionJob(job.ID, "failed", 0, 0, "provider_request_failed")
			JSON(w, http.StatusBadGateway, map[string]string{"error": "SSI HOSE index catalogue ingestion failed", "job_id": job.ID, "error_code": "provider_request_failed"})
			return
		}
		if published.RowCount < 1 || published.SnapshotID == "" {
			_ = a.Store.UpdateIngestionJob(job.ID, "failed", 0, 0, "invalid_provider_response")
			JSON(w, http.StatusBadGateway, map[string]string{"error": "SSI index catalogue returned an invalid snapshot", "job_id": job.ID, "error_code": "invalid_provider_response"})
			return
		}
		if err = a.Store.UpdateIngestionJob(job.ID, "running", published.RowCount, published.RowCount, ""); err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not save SSI ingestion progress", "job_id": job.ID})
			return
		}
		if err = a.Store.UpdateIngestionJob(job.ID, "completed", published.RowCount, published.RowCount, ""); err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not complete SSI ingestion job", "job_id": job.ID})
			return
		}
		completed, err := a.Store.IngestionJob(job.ID)
		if err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not read completed SSI ingestion job"})
			return
		}
		JSON(w, http.StatusCreated, map[string]any{"job": completed, "snapshot_id": published.SnapshotID})
	})

	m.HandleFunc("POST /api/v1/ingestion/candles/ssi/hose-equity/daily", func(w http.ResponseWriter, r *http.Request) {
		if a.Store == nil || a.Engine == nil || a.Engine.Engine == nil {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "SSI ingestion service is unavailable"})
			return
		}
		var input struct {
			InstrumentID string `json:"instrument_id"`
			FromDate     string `json:"from_date"`
			ToDate       string `json:"to_date"`
		}
		if !Read(w, r, &input) {
			return
		}
		fromDate, fromErr := time.Parse("2006-01-02", input.FromDate)
		toDate, toErr := time.Parse("2006-01-02", input.ToDate)
		if strings.TrimSpace(input.InstrumentID) == "" || fromErr != nil || toErr != nil || fromDate.After(toDate) {
			JSON(w, http.StatusBadRequest, map[string]string{"error": "instrument_id and an ordered ISO date range are required"})
			return
		}
		reader, ok := a.Credentials.(CredentialReader)
		if !ok {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "provider credential vault is unavailable"})
			return
		}
		rawCredential, err := reader.Get("ssi", "market-data")
		if err != nil {
			if errors.Is(err, os.ErrNotExist) {
				JSON(w, http.StatusBadRequest, map[string]string{"error": "SSI market-data credentials are not configured"})
				return
			}
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "could not read SSI market-data credentials"})
			return
		}
		var credential map[string]string
		if json.Unmarshal(rawCredential, &credential) != nil || len(credential) == 0 {
			JSON(w, http.StatusServiceUnavailable, map[string]string{"error": "SSI market-data credentials are invalid"})
			return
		}

		job := store.IngestionJob{
			ID: host.Token(), ProviderID: "ssi", CapabilityID: "ssi:market-data:candles.1d:equity:HOSE",
			Dataset: "candles.1d", AssetClass: "equity", Venue: "HOSE",
		}
		if err = a.Store.CreateIngestionJob(job); err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not create SSI ingestion job"})
			return
		}
		if err = a.Store.UpdateIngestionJob(job.ID, "running", 0, 0, ""); err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not start SSI ingestion job"})
			return
		}
		var published struct {
			SnapshotID string `json:"snapshot_id"`
			RowCount   int64  `json:"row_count"`
		}
		requestBody := map[string]any{
			"credential": credential, "instrument_id": input.InstrumentID,
			"from_date": input.FromDate, "to_date": input.ToDate,
		}
		// SSI allows up to ten pages and the adapter retries transient reads;
		// allow the complete documented page set to finish before the gateway times out.
		err = a.Engine.callWithTimeout(r.Context(), http.MethodPost, "/market/candles/ssi/hose-equity/daily", requestBody, &published, 420*time.Second)
		if err != nil {
			_ = a.Store.UpdateIngestionJob(job.ID, "failed", 0, 0, "provider_request_failed")
			JSON(w, http.StatusBadGateway, map[string]string{"error": "SSI HOSE daily candle ingestion failed", "job_id": job.ID, "error_code": "provider_request_failed"})
			return
		}
		if published.RowCount < 1 || published.SnapshotID == "" {
			_ = a.Store.UpdateIngestionJob(job.ID, "failed", 0, 0, "invalid_provider_response")
			JSON(w, http.StatusBadGateway, map[string]string{"error": "SSI daily candles returned an invalid snapshot", "job_id": job.ID, "error_code": "invalid_provider_response"})
			return
		}
		if err = a.Store.UpdateIngestionJob(job.ID, "running", published.RowCount, published.RowCount, ""); err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not save SSI ingestion progress", "job_id": job.ID})
			return
		}
		if err = a.Store.UpdateIngestionJob(job.ID, "completed", published.RowCount, published.RowCount, ""); err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not complete SSI ingestion job", "job_id": job.ID})
			return
		}
		completed, err := a.Store.IngestionJob(job.ID)
		if err != nil {
			JSON(w, http.StatusInternalServerError, map[string]string{"error": "could not read completed SSI ingestion job"})
			return
		}
		JSON(w, http.StatusCreated, map[string]any{"job": completed, "snapshot_id": published.SnapshotID})
	})
}
