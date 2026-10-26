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

func TestSSIHNXCatalogueSyncUsesVaultAndPersistsJob(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var received map[string]any
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/internal/v1/market/catalogues/ssi/hnx-equity" || r.Header.Get("Authorization") != "Bearer engine-token" {
			t.Fatalf("unexpected SSI HNX ingestion request: %s %s", r.Method, r.URL.Path)
		}
		if err := json.NewDecoder(r.Body).Decode(&received); err != nil {
			t.Fatal(err)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"snapshot_id": strings.Repeat("b", 64), "row_count": 17})
	}))
	defer engine.Close()
	credentials := &credentialWriterStub{credential: `{"consumerID":"local-id","consumerSecret":"hnx-catalogue-secret"}`}
	mux := http.NewServeMux()
	(&API{
		Store: db, Credentials: credentials,
		Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}},
	}).Routes(mux)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/api/v1/ingestion/catalogues/ssi/hnx-equity", strings.NewReader(`{}`)))
	if response.Code != http.StatusCreated || strings.Contains(response.Body.String(), "hnx-catalogue-secret") {
		t.Fatalf("SSI HNX ingestion response = %d %s", response.Code, response.Body.String())
	}
	if credentials.provider != "ssi" || credentials.service != "market-data" || received["credential"].(map[string]any)["consumerSecret"] != "hnx-catalogue-secret" {
		t.Fatalf("vault credentials were not sent to engine: vault=%s/%s engine=%#v", credentials.provider, credentials.service, received)
	}
	jobs, err := db.IngestionJobs()
	if err != nil || len(jobs) != 1 || jobs[0].Status != "completed" || jobs[0].CapabilityID != "ssi:market-data:instruments.details:equity:HNX" || jobs[0].Dataset != "instruments.details" || jobs[0].AssetClass != "equity" || jobs[0].Venue != "HNX" || jobs[0].ProcessedRecords != 17 {
		t.Fatalf("SSI HNX catalogue job = %#v, %v", jobs, err)
	}
}

func TestSSIUPCOMCatalogueSyncUsesVaultAndPersistsJob(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var received map[string]any
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/internal/v1/market/catalogues/ssi/upcom-equity" || r.Header.Get("Authorization") != "Bearer engine-token" {
			t.Fatalf("unexpected SSI UPCOM ingestion request: %s %s", r.Method, r.URL.Path)
		}
		if err := json.NewDecoder(r.Body).Decode(&received); err != nil {
			t.Fatal(err)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"snapshot_id": strings.Repeat("c", 64), "row_count": 23})
	}))
	defer engine.Close()
	credentials := &credentialWriterStub{credential: `{"consumerID":"local-id","consumerSecret":"upcom-catalogue-secret"}`}
	mux := http.NewServeMux()
	(&API{
		Store: db, Credentials: credentials,
		Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}},
	}).Routes(mux)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/api/v1/ingestion/catalogues/ssi/upcom-equity", strings.NewReader(`{}`)))
	if response.Code != http.StatusCreated || strings.Contains(response.Body.String(), "upcom-catalogue-secret") {
		t.Fatalf("SSI UPCOM ingestion response = %d %s", response.Code, response.Body.String())
	}
	if credentials.provider != "ssi" || credentials.service != "market-data" || received["credential"].(map[string]any)["consumerSecret"] != "upcom-catalogue-secret" {
		t.Fatalf("vault credentials were not sent to engine: vault=%s/%s engine=%#v", credentials.provider, credentials.service, received)
	}
	jobs, err := db.IngestionJobs()
	if err != nil || len(jobs) != 1 || jobs[0].Status != "completed" || jobs[0].CapabilityID != "ssi:market-data:instruments.details:equity:UPCOM" || jobs[0].Dataset != "instruments.details" || jobs[0].AssetClass != "equity" || jobs[0].Venue != "UPCOM" || jobs[0].ProcessedRecords != 23 {
		t.Fatalf("SSI UPCOM catalogue job = %#v, %v", jobs, err)
	}
}

func TestSSIHoseCoveredWarrantCatalogueSyncUsesVaultAndPersistsJob(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var received map[string]any
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/internal/v1/market/catalogues/ssi/hose-covered-warrants" || r.Header.Get("Authorization") != "Bearer engine-token" {
			t.Fatalf("unexpected SSI covered-warrant ingestion request: %s %s", r.Method, r.URL.Path)
		}
		if err := json.NewDecoder(r.Body).Decode(&received); err != nil {
			t.Fatal(err)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"snapshot_id": strings.Repeat("d", 64), "row_count": 31})
	}))
	defer engine.Close()
	credentials := &credentialWriterStub{credential: `{"consumerID":"local-id","consumerSecret":"covered-warrant-secret"}`}
	mux := http.NewServeMux()
	(&API{
		Store: db, Credentials: credentials,
		Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}},
	}).Routes(mux)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/api/v1/ingestion/catalogues/ssi/hose-covered-warrants", strings.NewReader(`{}`)))
	if response.Code != http.StatusCreated || strings.Contains(response.Body.String(), "covered-warrant-secret") {
		t.Fatalf("SSI covered-warrant ingestion response = %d %s", response.Code, response.Body.String())
	}
	if credentials.provider != "ssi" || credentials.service != "market-data" || received["credential"].(map[string]any)["consumerSecret"] != "covered-warrant-secret" {
		t.Fatalf("vault credentials were not sent to engine: vault=%s/%s engine=%#v", credentials.provider, credentials.service, received)
	}
	jobs, err := db.IngestionJobs()
	if err != nil || len(jobs) != 1 || jobs[0].Status != "completed" || jobs[0].CapabilityID != "ssi:market-data:instruments.details:covered_warrant:HOSE" || jobs[0].Dataset != "instruments.details" || jobs[0].AssetClass != "covered_warrant" || jobs[0].Venue != "HOSE" || jobs[0].ProcessedRecords != 31 {
		t.Fatalf("SSI covered-warrant catalogue job = %#v, %v", jobs, err)
	}
}

func TestSSIDerFuturesCatalogueSyncUsesVaultAndPersistsJob(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var received map[string]any
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/internal/v1/market/catalogues/ssi/der-futures" || r.Header.Get("Authorization") != "Bearer engine-token" {
			t.Fatalf("unexpected SSI derivatives ingestion request: %s %s", r.Method, r.URL.Path)
		}
		if err := json.NewDecoder(r.Body).Decode(&received); err != nil {
			t.Fatal(err)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"snapshot_id": strings.Repeat("e", 64), "row_count": 7})
	}))
	defer engine.Close()
	credentials := &credentialWriterStub{credential: `{"consumerID":"local-id","consumerSecret":"der-futures-secret"}`}
	mux := http.NewServeMux()
	(&API{
		Store: db, Credentials: credentials,
		Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}},
	}).Routes(mux)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/api/v1/ingestion/catalogues/ssi/der-futures", strings.NewReader(`{}`)))
	if response.Code != http.StatusCreated || strings.Contains(response.Body.String(), "der-futures-secret") {
		t.Fatalf("SSI DER futures ingestion response = %d %s", response.Code, response.Body.String())
	}
	if credentials.provider != "ssi" || credentials.service != "market-data" || received["credential"].(map[string]any)["consumerSecret"] != "der-futures-secret" {
		t.Fatalf("vault credentials were not sent to engine: vault=%s/%s engine=%#v", credentials.provider, credentials.service, received)
	}
	jobs, err := db.IngestionJobs()
	if err != nil || len(jobs) != 1 || jobs[0].Status != "completed" || jobs[0].CapabilityID != "ssi:market-data:instruments.details:derivative:DER" || jobs[0].Dataset != "instruments.details" || jobs[0].AssetClass != "derivative" || jobs[0].Venue != "DER" || jobs[0].ProcessedRecords != 7 {
		t.Fatalf("SSI DER futures catalogue job = %#v, %v", jobs, err)
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

func TestSSIHoseDailyCandleSyncUsesVaultAndPersistsOneDatasetJob(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var received map[string]any
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/internal/v1/market/candles/ssi/hose-equity/daily" {
			t.Fatalf("unexpected SSI daily candle request: %s %s", r.Method, r.URL.Path)
		}
		if err := json.NewDecoder(r.Body).Decode(&received); err != nil {
			t.Fatal(err)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"snapshot_id": strings.Repeat("b", 64), "row_count": 3})
	}))
	defer engine.Close()
	credentials := &credentialWriterStub{credential: `{"consumerID":"local-id","consumerSecret":"daily-secret"}`}
	mux := http.NewServeMux()
	(&API{
		Store: db, Credentials: credentials,
		Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}},
	}).Routes(mux)
	response := httptest.NewRecorder()
	body := `{"instrument_id":"SSI:ISIN:VN000000AAA1","from_date":"2025-01-02","to_date":"2025-03-31"}`
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/api/v1/ingestion/candles/ssi/hose-equity/daily", strings.NewReader(body)))
	if response.Code != http.StatusCreated || strings.Contains(response.Body.String(), "daily-secret") {
		t.Fatalf("SSI daily candle response = %d %s", response.Code, response.Body.String())
	}
	if received["instrument_id"] != "SSI:ISIN:VN000000AAA1" || received["from_date"] != "2025-01-02" || received["to_date"] != "2025-03-31" || received["credential"].(map[string]any)["consumerSecret"] != "daily-secret" {
		t.Fatalf("SSI daily candle engine input = %#v", received)
	}
	jobs, err := db.IngestionJobs()
	if err != nil || len(jobs) != 1 || jobs[0].Status != "completed" || jobs[0].CapabilityID != "ssi:market-data:candles.1d:equity:HOSE" || jobs[0].ProcessedRecords != 3 {
		t.Fatalf("SSI daily candle job = %#v, %v", jobs, err)
	}
}

func TestSSIHoseIndexCatalogueSyncUsesVaultAndPersistsIndexJob(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var received map[string]any
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/internal/v1/market/catalogues/ssi/hose-indices" {
			t.Fatalf("unexpected SSI index catalogue request: %s %s", r.Method, r.URL.Path)
		}
		if err := json.NewDecoder(r.Body).Decode(&received); err != nil {
			t.Fatal(err)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"snapshot_id": strings.Repeat("c", 64), "row_count": 3})
	}))
	defer engine.Close()
	credentials := &credentialWriterStub{credential: `{"consumerID":"local-id","consumerSecret":"index-secret"}`}
	mux := http.NewServeMux()
	(&API{
		Store: db, Credentials: credentials,
		Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}},
	}).Routes(mux)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/api/v1/ingestion/catalogues/ssi/hose-indices", strings.NewReader(`{}`)))
	if response.Code != http.StatusCreated || strings.Contains(response.Body.String(), "index-secret") {
		t.Fatalf("SSI index catalogue response = %d %s", response.Code, response.Body.String())
	}
	if credentials.provider != "ssi" || credentials.service != "market-data" || received["credential"].(map[string]any)["consumerSecret"] != "index-secret" {
		t.Fatalf("vault credentials were not sent to engine: vault=%s/%s engine=%#v", credentials.provider, credentials.service, received)
	}
	jobs, err := db.IngestionJobs()
	if err != nil || len(jobs) != 1 || jobs[0].Status != "completed" || jobs[0].CapabilityID != "ssi:market-data:instruments.index:index:HOSE" || jobs[0].Dataset != "instruments.index" || jobs[0].AssetClass != "index" || jobs[0].ProcessedRecords != 3 {
		t.Fatalf("SSI index catalogue job = %#v, %v", jobs, err)
	}
}

func TestSSIHnxIndexCatalogueSyncUsesVaultAndPersistsHnxIndexJob(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var received map[string]any
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/internal/v1/market/catalogues/ssi/hnx-indices" {
			t.Fatalf("unexpected SSI HNX index catalogue request: %s %s", r.Method, r.URL.Path)
		}
		if err := json.NewDecoder(r.Body).Decode(&received); err != nil {
			t.Fatal(err)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"snapshot_id": strings.Repeat("d", 64), "row_count": 4})
	}))
	defer engine.Close()
	credentials := &credentialWriterStub{credential: `{"consumerID":"local-id","consumerSecret":"hnx-index-secret"}`}
	mux := http.NewServeMux()
	(&API{
		Store: db, Credentials: credentials,
		Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}},
	}).Routes(mux)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/api/v1/ingestion/catalogues/ssi/hnx-indices", strings.NewReader(`{}`)))
	if response.Code != http.StatusCreated || strings.Contains(response.Body.String(), "hnx-index-secret") {
		t.Fatalf("SSI HNX index catalogue response = %d %s", response.Code, response.Body.String())
	}
	if credentials.provider != "ssi" || credentials.service != "market-data" || received["credential"].(map[string]any)["consumerSecret"] != "hnx-index-secret" {
		t.Fatalf("vault credentials were not sent to engine: vault=%s/%s engine=%#v", credentials.provider, credentials.service, received)
	}
	jobs, err := db.IngestionJobs()
	if err != nil || len(jobs) != 1 || jobs[0].Status != "completed" || jobs[0].CapabilityID != "ssi:market-data:instruments.index:index:HNX" || jobs[0].Dataset != "instruments.index" || jobs[0].AssetClass != "index" || jobs[0].Venue != "HNX" || jobs[0].ProcessedRecords != 4 {
		t.Fatalf("SSI HNX index catalogue job = %#v, %v", jobs, err)
	}
}

func TestSSIHoseIndexConstituentSyncUsesVaultAndPersistsConstituentJob(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var received map[string]any
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/internal/v1/market/index-components/ssi/hose" {
			t.Fatalf("unexpected SSI index constituent request: %s %s", r.Method, r.URL.Path)
		}
		if err := json.NewDecoder(r.Body).Decode(&received); err != nil {
			t.Fatal(err)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"snapshot_id": strings.Repeat("e", 64), "row_count": 1})
	}))
	defer engine.Close()
	credentials := &credentialWriterStub{credential: `{"consumerID":"local-id","consumerSecret":"constituent-secret"}`}
	mux := http.NewServeMux()
	(&API{
		Store: db, Credentials: credentials,
		Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}},
	}).Routes(mux)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/api/v1/ingestion/index-constituents/ssi/hose", strings.NewReader(`{"index_instrument_id":"SSI:INDEX:HOSE:VN30"}`)))
	if response.Code != http.StatusCreated || strings.Contains(response.Body.String(), "constituent-secret") {
		t.Fatalf("SSI index constituent response = %d %s", response.Code, response.Body.String())
	}
	if credentials.provider != "ssi" || credentials.service != "market-data" || received["credential"].(map[string]any)["consumerSecret"] != "constituent-secret" || received["index_instrument_id"] != "SSI:INDEX:HOSE:VN30" {
		t.Fatalf("vault credentials or index identity were not sent to engine: vault=%s/%s engine=%#v", credentials.provider, credentials.service, received)
	}
	jobs, err := db.IngestionJobs()
	if err != nil || len(jobs) != 1 || jobs[0].Status != "completed" || jobs[0].CapabilityID != "ssi:market-data:indices.constituents:index:HOSE" || jobs[0].Dataset != "indices.constituents" || jobs[0].AssetClass != "index" || jobs[0].Venue != "HOSE" || jobs[0].ProcessedRecords != 1 {
		t.Fatalf("SSI index constituent job = %#v, %v", jobs, err)
	}
}

func TestSSIHoseDailyIndexSyncUsesVaultAndPersistsDailyIndexJob(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var received map[string]any
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/internal/v1/market/index-series/ssi/hose/daily" {
			t.Fatalf("unexpected SSI DailyIndex request: %s %s", r.Method, r.URL.Path)
		}
		if err := json.NewDecoder(r.Body).Decode(&received); err != nil {
			t.Fatal(err)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"snapshot_id": strings.Repeat("f", 64), "row_count": 25})
	}))
	defer engine.Close()
	credentials := &credentialWriterStub{credential: `{"consumerID":"local-id","consumerSecret":"daily-index-secret"}`}
	mux := http.NewServeMux()
	(&API{
		Store: db, Credentials: credentials,
		Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}},
	}).Routes(mux)
	response := httptest.NewRecorder()
	body := `{"index_instrument_id":"SSI:INDEX:HOSE:VN30","from_date":"2025-01-01","to_date":"2025-02-01"}`
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/api/v1/ingestion/index-series/ssi/hose/daily", strings.NewReader(body)))
	if response.Code != http.StatusCreated || strings.Contains(response.Body.String(), "daily-index-secret") {
		t.Fatalf("SSI DailyIndex response = %d %s", response.Code, response.Body.String())
	}
	if credentials.provider != "ssi" || credentials.service != "market-data" || received["credential"].(map[string]any)["consumerSecret"] != "daily-index-secret" || received["index_instrument_id"] != "SSI:INDEX:HOSE:VN30" || received["from_date"] != "2025-01-01" || received["to_date"] != "2025-02-01" {
		t.Fatalf("vault credentials or DailyIndex request were not preserved: vault=%s/%s engine=%#v", credentials.provider, credentials.service, received)
	}
	jobs, err := db.IngestionJobs()
	if err != nil || len(jobs) != 1 || jobs[0].Status != "completed" || jobs[0].CapabilityID != "ssi:market-data:indices.daily:index:HOSE" || jobs[0].Dataset != "indices.daily" || jobs[0].AssetClass != "index" || jobs[0].Venue != "HOSE" || jobs[0].ProcessedRecords != 25 {
		t.Fatalf("SSI DailyIndex job = %#v, %v", jobs, err)
	}
}

func TestSSIHNXDailyIndexSyncUsesVaultAndPersistsDailyIndexJob(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var received map[string]any
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost || r.URL.Path != "/internal/v1/market/index-series/ssi/hnx/daily" {
			t.Fatalf("unexpected SSI DailyIndex request: %s %s", r.Method, r.URL.Path)
		}
		if err := json.NewDecoder(r.Body).Decode(&received); err != nil {
			t.Fatal(err)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"snapshot_id": strings.Repeat("e", 64), "row_count": 10})
	}))
	defer engine.Close()
	credentials := &credentialWriterStub{credential: `{"consumerID":"local-id","consumerSecret":"daily-index-secret"}`}
	mux := http.NewServeMux()
	(&API{
		Store: db, Credentials: credentials,
		Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}},
	}).Routes(mux)
	response := httptest.NewRecorder()
	body := `{"index_instrument_id":"SSI:INDEX:HNX:HNX30","from_date":"2025-01-01","to_date":"2025-02-01"}`
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/api/v1/ingestion/index-series/ssi/hnx/daily", strings.NewReader(body)))
	if response.Code != http.StatusCreated || strings.Contains(response.Body.String(), "daily-index-secret") {
		t.Fatalf("SSI DailyIndex response = %d %s", response.Code, response.Body.String())
	}
	if credentials.provider != "ssi" || credentials.service != "market-data" || received["credential"].(map[string]any)["consumerSecret"] != "daily-index-secret" || received["index_instrument_id"] != "SSI:INDEX:HNX:HNX30" || received["from_date"] != "2025-01-01" || received["to_date"] != "2025-02-01" {
		t.Fatalf("vault credentials or DailyIndex request were not preserved: vault=%s/%s engine=%#v", credentials.provider, credentials.service, received)
	}
	jobs, err := db.IngestionJobs()
	if err != nil || len(jobs) != 1 || jobs[0].Status != "completed" || jobs[0].CapabilityID != "ssi:market-data:indices.daily:index:HNX" || jobs[0].Dataset != "indices.daily" || jobs[0].AssetClass != "index" || jobs[0].Venue != "HNX" || jobs[0].ProcessedRecords != 10 {
		t.Fatalf("SSI DailyIndex job = %#v, %v", jobs, err)
	}
}
