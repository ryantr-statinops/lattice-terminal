package auth

import (
	"net/http"
	"net/http/httptest"
	"testing"
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
