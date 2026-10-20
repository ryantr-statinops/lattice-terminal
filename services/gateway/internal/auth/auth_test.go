package auth

import (
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestUsernamePasswordAndLock(t *testing.T) {
	m := New("local", "correct password 123")
	token, err := m.Login("local", "correct password 123")
	if err != nil {
		t.Fatal(err)
	}
	r := httptest.NewRequest("GET", "http://127.0.0.1:8080/api/v1/private", nil)
	r.AddCookie(Cookie(token))
	if !m.Valid(r) {
		t.Fatal("session missing")
	}
	if _, err := m.Login("other", "correct password 123"); err == nil {
		t.Fatal("accepted wrong username")
	}
	if _, err := m.Login("local", "incorrect password"); err == nil {
		t.Fatal("accepted wrong password")
	}
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
	m := New("local", "test password 123")
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
	m := New("local", "test password only 123")
	token, err := m.Login("local", "test password only 123")
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
	m := New("local", "test password 123")
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

func TestLoginRouteUsesUsernameAndNeverReturnsCredentials(t *testing.T) {
	m := New("local", "Tiếng Việt $ secret 123")
	mux := http.NewServeMux()
	m.Routes(mux)
	h := m.Guard(mux, false)
	req := httptest.NewRequest("POST", "http://127.0.0.1:8080/api/v1/auth/login", strings.NewReader(`{"username":"local","password":"Tiếng Việt $ secret 123"}`))
	req.Header.Set("Origin", "http://127.0.0.1:8080")
	w := httptest.NewRecorder()
	h.ServeHTTP(w, req)
	if w.Code != http.StatusNoContent {
		t.Fatalf("login status %d: %s", w.Code, w.Body.String())
	}
	status := httptest.NewRecorder()
	h.ServeHTTP(status, httptest.NewRequest("GET", "http://127.0.0.1:8080/api/v1/auth/status", nil))
	if strings.Contains(status.Body.String(), "secret") || strings.Contains(status.Body.String(), "username") {
		t.Fatal("status disclosed credentials")
	}
}
