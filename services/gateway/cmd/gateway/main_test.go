package main

import (
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
)

func TestProxyRoundTrip(t *testing.T) {
	up := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.RequestURI() != "/api/v1/news?limit=2" || r.Header.Get("X-Request-ID") != "test-1" {
			t.Error("path/query/request id not preserved")
		}
		b, _ := io.ReadAll(r.Body)
		if string(b) != "hello" {
			t.Error("body not preserved")
		}
		w.Header().Set("X-Request-ID", "upstream-overwrite")
		w.WriteHeader(201)
		_, _ = w.Write([]byte("ok"))
	}))
	defer up.Close()
	u, _ := url.Parse(up.URL)
	r := httptest.NewRequest("POST", "/api/v1/news?limit=2", strings.NewReader("hello"))
	r.Header.Set("X-Request-ID", "test-1")
	w := httptest.NewRecorder()
	handler(u).ServeHTTP(w, r)
	if w.Code != 201 || w.Body.String() != "ok" || w.Header().Get("X-Request-ID") != "test-1" {
		t.Fatalf("unexpected response: %v", w.Result())
	}
}

func TestRoutesAndLimits(t *testing.T) {
	u, _ := url.Parse("http://127.0.0.1:1")
	h := handler(u)
	for _, tc := range []struct {
		path   string
		status int
	}{{"/healthz", 200}, {"/elsewhere", 404}, {"/api/news", 502}} {
		w := httptest.NewRecorder()
		h.ServeHTTP(w, httptest.NewRequest("GET", tc.path, nil))
		if w.Code != tc.status || !validRequestID(w.Header().Get("X-Request-ID")) {
			t.Errorf("%s: %d", tc.path, w.Code)
		}
	}
	r := httptest.NewRequest("POST", "/api/news", strings.NewReader(strings.Repeat("a", maxBody+1)))
	r.ContentLength = -1
	w := httptest.NewRecorder()
	h.ServeHTTP(w, r)
	if w.Code != 413 {
		t.Errorf("chunked oversize: %d", w.Code)
	}
}

func TestConfig(t *testing.T) {
	for _, raw := range []string{"ftp://example.com", "https://user:secret@example.com", "https://example.com/path", "https://example.com?key=value", "http://"} {
		t.Setenv("KESTREL_API_BASE_URL", raw)
		if _, err := loadConfig(); err == nil {
			t.Errorf("accepted invalid origin")
		}
	}
	t.Setenv("KESTREL_API_BASE_URL", "")
	t.Setenv("KESTREL_GATEWAY_ADDR", "")
	cfg, err := loadConfig()
	if err != nil || cfg.addr != "127.0.0.1:8080" {
		t.Fatal("defaults invalid")
	}
	for _, addr := range []string{"invalid", "127.0.0.1:0", "127.0.0.1:65536"} {
		t.Setenv("KESTREL_GATEWAY_ADDR", addr)
		if _, err := loadConfig(); err == nil {
			t.Error("accepted invalid listen address")
		}
	}
}
