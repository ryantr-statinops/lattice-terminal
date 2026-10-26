package api

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"kestrel-terminal/gateway/internal/host"
	"kestrel-terminal/gateway/internal/store"
)

func TestIngestionJobsEndpointReturnsProgressAndCheckpoint(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	job := store.IngestionJob{ID: "ssi-daily", ProviderID: "ssi", CapabilityID: "ssi:market-data:candles.1d:equity:HOSE", Dataset: "candles.1d", AssetClass: "equity", Venue: "HOSE"}
	if err = db.CreateIngestionJob(job); err != nil {
		t.Fatal(err)
	}
	if err = db.UpdateIngestionJob(job.ID, "running", 25, 100, ""); err != nil {
		t.Fatal(err)
	}
	if err = db.SaveIngestionCheckpoint(job.ID, store.IngestionCheckpoint{Version: 1, Kind: "page", Value: "3"}, 25, 100); err != nil {
		t.Fatal(err)
	}
	mux := http.NewServeMux()
	(&API{Store: db}).Routes(mux)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/api/v1/ingestion/jobs", nil))
	var jobs []store.IngestionJob
	if response.Code != http.StatusOK || json.Unmarshal(response.Body.Bytes(), &jobs) != nil || len(jobs) != 1 {
		t.Fatalf("ingestion jobs response = %d %s", response.Code, response.Body.String())
	}
	if jobs[0].Status != "running" || jobs[0].ProcessedRecords != 25 || jobs[0].Checkpoint == nil || jobs[0].Checkpoint.Version != 1 || jobs[0].Checkpoint.Value != "3" {
		t.Fatalf("ingestion job response = %#v", jobs[0])
	}
}

func TestIngestionJobsEndpointRequiresStore(t *testing.T) {
	mux := http.NewServeMux()
	(&API{}).Routes(mux)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/api/v1/ingestion/jobs", nil))
	if response.Code != http.StatusServiceUnavailable {
		t.Fatalf("missing store response = %d %s", response.Code, response.Body.String())
	}
}

func TestSSIHoseCatalogueSyncUsesVaultAndPersistsJob(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var received map[string]any
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/internal/v1/market/catalogues/ssi/hose-equity" || r.Header.Get("Authorization") != "Bearer engine-token" {
			t.Fatalf("unexpected SSI ingestion request: %s %s", r.Method, r.URL.Path)
		}
		if err := json.NewDecoder(r.Body).Decode(&received); err != nil {
			t.Fatal(err)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"snapshot_id": strings.Repeat("a", 64), "row_count": 2})
	}))
	defer engine.Close()
	credentials := &credentialWriterStub{credential: `{"consumerID":"local-id","consumerSecret":"catalogue-secret"}`}
	mux := http.NewServeMux()
	(&API{
		Store: db, Credentials: credentials,
		Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}},
	}).Routes(mux)
	response := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodPost, "/api/v1/ingestion/catalogues/ssi/hose-equity", strings.NewReader(`{}`))
	mux.ServeHTTP(response, request)
	if response.Code != http.StatusCreated || strings.Contains(response.Body.String(), "catalogue-secret") {
		t.Fatalf("SSI ingestion response = %d %s", response.Code, response.Body.String())
	}
	if credentials.provider != "ssi" || credentials.service != "market-data" || received["credential"].(map[string]any)["consumerSecret"] != "catalogue-secret" {
		t.Fatalf("vault credentials were not sent to engine: vault=%s/%s engine=%#v", credentials.provider, credentials.service, received)
	}
	jobs, err := db.IngestionJobs()
	if err != nil || len(jobs) != 1 || jobs[0].Status != "completed" || jobs[0].ProcessedRecords != 2 || jobs[0].Venue != "HOSE" {
		t.Fatalf("SSI catalogue job = %#v, %v", jobs, err)
	}
}

func TestSSIHoseCatalogueSyncRedactsProviderErrors(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusBadRequest)
		_, _ = w.Write([]byte(`{"error":"credential catalogue-secret rejected"}`))
	}))
	defer engine.Close()
	mux := http.NewServeMux()
	(&API{
		Store: db, Credentials: &credentialWriterStub{credential: `{"consumerID":"local-id","consumerSecret":"catalogue-secret"}`},
		Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}},
	}).Routes(mux)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/api/v1/ingestion/catalogues/ssi/hose-equity", strings.NewReader(`{}`)))
	if response.Code != http.StatusBadGateway || strings.Contains(response.Body.String(), "catalogue-secret") {
		t.Fatalf("provider failure response leaked details: %d %s", response.Code, response.Body.String())
	}
	var result struct {
		JobID string `json:"job_id"`
	}
	if err = json.Unmarshal(response.Body.Bytes(), &result); err != nil || result.JobID == "" {
		t.Fatalf("failed SSI ingestion response = %s (%v)", response.Body.String(), err)
	}
	job, err := db.IngestionJob(result.JobID)
	if err != nil || job.Status != "failed" || job.ErrorCode != "provider_request_failed" {
		t.Fatalf("failed SSI ingestion job = %#v, %v", job, err)
	}
}

func TestSSIHoseCatalogueSyncRejectsMissingVaultCredentialBeforeStartingJob(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	engineCalled := false
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		engineCalled = true
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer engine.Close()
	mux := http.NewServeMux()
	(&API{
		Store: db, Credentials: &credentialWriterStub{},
		Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}},
	}).Routes(mux)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/api/v1/ingestion/catalogues/ssi/hose-equity", strings.NewReader(`{}`)))
	jobs, listErr := db.IngestionJobs()
	if response.Code != http.StatusBadRequest || engineCalled || listErr != nil || len(jobs) != 0 {
		t.Fatalf("missing credential handling = %d %s, engineCalled=%v jobs=%#v error=%v", response.Code, response.Body.String(), engineCalled, jobs, listErr)
	}
}
