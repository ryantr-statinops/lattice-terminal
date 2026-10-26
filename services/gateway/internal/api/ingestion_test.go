package api

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

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
