package auth

import (
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestProfileResetAndLock(t *testing.T) {
	m := New(t.TempDir())
	if err := m.SetPassword("correct password 123", false); err != nil {
		t.Fatal(err)
	}
	if m.SetPassword("another password", false) == nil {
		t.Fatal("overwrote profile")
	}
	token, err := m.Login("correct password 123")
	if err != nil {
		t.Fatal(err)
	}
	r := httptest.NewRequest("GET", "http://127.0.0.1:8080/api/v1/private", nil)
	r.AddCookie(Cookie(token))
	if !m.Valid(r) {
		t.Fatal("session missing")
	}
	if err := m.SetPassword("new correct password", true); err != nil {
		t.Fatal(err)
	}
	if m.Valid(r) {
		t.Fatal("reset preserved old session")
	}
	token, _ = m.Login("new correct password")
	r = httptest.NewRequest("GET", "/", nil)
	r.AddCookie(Cookie(token))
	m.Lock()
	if m.Valid(r) {
		t.Fatal("lock failed")
	}
}

type wireBody struct {
	*strings.Reader
	closed bool
}

func (b *wireBody) Close() error { b.closed = true; return nil }
func TestGuardConsumesWireBodyBeforeAHandlerResponds(t *testing.T) {
	m := New(t.TempDir())
	body := &wireBody{Reader: strings.NewReader(`{}`)}
	request := httptest.NewRequest("POST", "http://127.0.0.1:8080/api/v1/auth/login", nil)
	request.Header.Set("Origin", "http://127.0.0.1:8080")
	request.Body = body
	handler := m.Guard(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if body.Len() != 0 || !body.closed {
			t.Error("wire body left unread before response")
		}
		b, err := io.ReadAll(r.Body)
		if err != nil || string(b) != "{}" {
			t.Error("handler lost request body")
		}
		w.WriteHeader(204)
	}), false)
	response := httptest.NewRecorder()
	handler.ServeHTTP(response, request)
	if response.Code != 204 {
		t.Fatal(response.Code)
	}
}
func TestActiveStreamCannotExtendAbsoluteSessionLifetime(t *testing.T) {
	m := New(t.TempDir())
	if err := m.SetPassword("test password only 123", false); err != nil {
		t.Fatal(err)
	}
	token, err := m.Login("test password only 123")
	if err != nil {
		t.Fatal(err)
	}
	v := m.sessions[token]
	v.Expires = time.Now().Add(-time.Second)
	v.Last = time.Now()
	m.sessions[token] = v
	r := httptest.NewRequest("GET", "/api/v1/runs/r/events", nil)
	r.AddCookie(Cookie(token))
	if m.Valid(r) {
		t.Fatal("active SSE extended expired session")
	}
}
func TestGuardOriginAndHost(t *testing.T) {
	m := New(t.TempDir())
	h := m.Guard(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(204) }), false)
	for _, u := range []string{"http://evil.example/api/v1/auth/status", "http://127.0.0.1:8080/api/v1/private"} {
		w := httptest.NewRecorder()
		h.ServeHTTP(w, httptest.NewRequest("GET", u, nil))
		if w.Code != 403 && w.Code != 401 {
			t.Fatal(w.Code)
		}
	}
	r := httptest.NewRequest("POST", "http://127.0.0.1:8080/api/v1/auth/setup", nil)
	r.Header.Set("Origin", "https://evil.example")
	w := httptest.NewRecorder()
	h.ServeHTTP(w, r)
	if w.Code != 403 {
		t.Fatal(w.Code)
	}
}
