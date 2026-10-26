package api

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"kestrel-terminal/gateway/internal/host"
	"kestrel-terminal/gateway/internal/store"
)

func TestProviderRoutingPersistsAndAppliesPatch(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var applied store.RoutingPolicy
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/internal/v1/providers/routing" || r.Method != http.MethodPut {
			http.NotFound(w, r)
			return
		}
		if r.Header.Get("Authorization") != "Bearer engine-test-token" {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		if err := json.NewDecoder(r.Body).Decode(&applied); err != nil {
			http.Error(w, "invalid policy", http.StatusBadRequest)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(applied)
	}))
	defer engine.Close()
	app := &API{
		Store: db,
		Engine: &Runner{
			Engine:  &host.Engine{URL: engine.URL, Token: "engine-test-token"},
			Context: context.Background(),
		},
	}
	mux := http.NewServeMux()
	app.Routes(mux)

	get := httptest.NewRecorder()
	mux.ServeHTTP(get, httptest.NewRequest(http.MethodGet, "/api/v1/providers/routing", nil))
	var initial store.RoutingPolicy
	if get.Code != http.StatusOK || json.Unmarshal(get.Body.Bytes(), &initial) != nil || initial.HistoricalProvider != "vndirect" {
		t.Fatalf("initial policy response = %d %s", get.Code, get.Body.String())
	}

	update := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodPut, "/api/v1/providers/routing", strings.NewReader(`{"historical_provider":"ssi","fallback_enabled":false,"datasets":{"candles.1d:equity:HOSE":"ssi"}}`))
	mux.ServeHTTP(update, request)
	if update.Code != http.StatusOK {
		t.Fatalf("update response = %d %s", update.Code, update.Body.String())
	}
	want := store.RoutingPolicy{HistoricalProvider: "ssi", RealtimeProvider: "fixture", FinancialsProvider: "tcbs", FallbackEnabled: false, Datasets: map[string]string{"candles.1d:equity:HOSE": "ssi"}}
	if applied.HistoricalProvider != want.HistoricalProvider || applied.RealtimeProvider != want.RealtimeProvider || applied.FinancialsProvider != want.FinancialsProvider || applied.FallbackEnabled != want.FallbackEnabled || applied.Datasets["candles.1d:equity:HOSE"] != "ssi" {
		t.Fatalf("engine got %#v, want %#v", applied, want)
	}
	stored, err := db.RoutingPolicy()
	if err != nil || stored.HistoricalProvider != want.HistoricalProvider || stored.RealtimeProvider != want.RealtimeProvider || stored.FinancialsProvider != want.FinancialsProvider || stored.FallbackEnabled != want.FallbackEnabled || stored.Datasets["candles.1d:equity:HOSE"] != "ssi" {
		t.Fatalf("SQLite policy = %#v, want %#v, err=%v", stored, want, err)
	}
}

func TestProviderRoutingDoesNotPersistWhenEngineRejectsUpdate(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusServiceUnavailable)
		_, _ = io.WriteString(w, `{"error":"routing unavailable"}`)
	}))
	defer engine.Close()
	app := &API{Store: db, Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-test-token"}, Context: context.Background()}}
	mux := http.NewServeMux()
	app.Routes(mux)
	response := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodPut, "/api/v1/providers/routing", strings.NewReader(`{"historical_provider":"ssi"}`))
	mux.ServeHTTP(response, request)
	if response.Code != http.StatusServiceUnavailable {
		t.Fatalf("failed engine update returned %d", response.Code)
	}
	stored, err := db.RoutingPolicy()
	if err != nil || stored.HistoricalProvider != "vndirect" {
		t.Fatalf("failed update changed SQLite policy: %#v, %v", stored, err)
	}
}
