package host

import (
	"context"
	"io"
	"net/http"
	"strings"
	"testing"
	"time"
)

type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func TestWaitEngineAuthenticates(t *testing.T) {
	client := &http.Client{Transport: roundTripFunc(func(r *http.Request) (*http.Response, error) {
		if r.Header.Get("Authorization") != "Bearer local-test-token" {
			t.Fatal("engine request missing bearer token")
		}
		return &http.Response{StatusCode: http.StatusOK, Body: io.NopCloser(strings.NewReader(`{"status":"ok"}`)), Header: make(http.Header)}, nil
	})}
	engine := &Engine{URL: "http://127.0.0.1:8081", Token: "local-test-token"}
	if err := waitEngineWithClient(context.Background(), engine, time.Second, client); err != nil {
		t.Fatal(err)
	}
}

func TestConnectEngineRejectsMissingOrWrongToken(t *testing.T) {
	if _, err := ConnectEngine(context.Background(), "http://127.0.0.1:8081", ""); err == nil || !strings.Contains(err.Error(), "KESTREL_ENGINE_TOKEN") {
		t.Fatalf("missing token error = %v", err)
	}
	client := &http.Client{Transport: roundTripFunc(func(r *http.Request) (*http.Response, error) {
		return &http.Response{StatusCode: http.StatusUnauthorized, Body: io.NopCloser(strings.NewReader(`{"error":"unauthorized"}`)), Header: make(http.Header)}, nil
	})}
	err := waitEngineWithClient(context.Background(), &Engine{URL: "http://127.0.0.1:8081", Token: "wrong-local-test-token"}, time.Second, client)
	if err == nil || strings.Contains(err.Error(), "wrong-local-test-token") {
		t.Fatalf("wrong token error should be redacted, got %v", err)
	}
}

func TestConnectEngineRejectsNonLoopbackURL(t *testing.T) {
	if _, err := ConnectEngine(context.Background(), "http://example.com:8081", "local-test-token"); err == nil {
		t.Fatal("non-loopback engine URL was accepted")
	}
}
