package api

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"kestrel-terminal/gateway/internal/store"
)

func TestInstrumentAliasAPIStoresAndResolvesMappings(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	mux := http.NewServeMux()
	(&API{Store: db}).Routes(mux)

	put := httptest.NewRecorder()
	mux.ServeHTTP(put, httptest.NewRequest(http.MethodPut, "/api/v1/market/instrument-aliases", strings.NewReader(`{"stable_instrument_id":"VN:HOSE:equity:ACME","provider_id":"ssi","provider_instrument_id":"42","native_symbol":"ACME","venue":"HOSE","effective_from":"2026-01-01T00:00:00Z"}`)))
	if put.Code != http.StatusNoContent {
		t.Fatalf("alias write returned %d: %s", put.Code, put.Body.String())
	}

	get := httptest.NewRecorder()
	mux.ServeHTTP(get, httptest.NewRequest(http.MethodGet, "/api/v1/market/instrument-aliases/resolve?provider_id=ssi&provider_instrument_id=42&at=2026-02-01T00%3A00%3A00Z", nil))
	if get.Code != http.StatusOK || !strings.Contains(get.Body.String(), `"stable_instrument_id":"VN:HOSE:equity:ACME"`) {
		t.Fatalf("alias resolve returned %d: %s", get.Code, get.Body.String())
	}

	invalid := httptest.NewRecorder()
	mux.ServeHTTP(invalid, httptest.NewRequest(http.MethodPut, "/api/v1/market/instrument-aliases", strings.NewReader(`{"stable_instrument_id":"x","provider_id":"ssi","provider_instrument_id":"42","native_symbol":"ACME","effective_from":"2026-01-01T00:00:00Z","unexpected":true}`)))
	if invalid.Code != http.StatusBadRequest {
		t.Fatalf("unknown alias field returned %d", invalid.Code)
	}
}
