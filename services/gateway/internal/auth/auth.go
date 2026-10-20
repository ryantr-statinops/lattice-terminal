package auth

import (
	"bytes"
	"crypto/rand"
	"crypto/subtle"
	"encoding/base64"
	"encoding/json"
	"errors"
	"golang.org/x/crypto/argon2"
	"io"
	"net/http"
	"sync"
	"time"
)

type record struct{ Salt, Hash, Generation string }
type session struct {
	Last       time.Time
	Expires    time.Time
	Generation string
}
type Manager struct {
	mu         sync.Mutex
	username   string
	verifier   record
	sessions   map[string]session
	failures   int
	retryAfter time.Time
}

// New creates only an in-memory verifier. The repository .env is authoritative.
func New(username, password string) *Manager {
	salt := random()
	return &Manager{username: username, verifier: record{Salt: salt, Hash: derive(password, salt), Generation: random()}, sessions: make(map[string]session)}
}
func random() string {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		panic(err)
	}
	return base64.RawURLEncoding.EncodeToString(b)
}
func derive(password, salt string) string {
	return base64.RawStdEncoding.EncodeToString(argon2.IDKey([]byte(password), []byte(salt), 3, 64*1024, 2, 32))
}
func (m *Manager) Login(username, password string) (string, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	now := time.Now()
	if now.Before(m.retryAfter) {
		return "", errors.New("try again later")
	}
	v := m.verifier
	hash := derive(password, v.Salt)
	if subtle.ConstantTimeCompare([]byte(hash), []byte(v.Hash)) != 1 || subtle.ConstantTimeCompare([]byte(username), []byte(m.username)) != 1 {
		m.failures++
		if m.failures >= 5 {
			m.retryAfter = now.Add(time.Minute)
			m.failures = 0
		}
		return "", errors.New("invalid password")
	}
	m.failures = 0
	token := random()
	m.sessions[token] = session{Last: now, Expires: now.Add(30 * time.Minute), Generation: v.Generation}
	return token, nil
}
func (m *Manager) Valid(r *http.Request) bool {
	cookie, err := r.Cookie("kestrel_session")
	if err != nil {
		return false
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	s, ok := m.sessions[cookie.Value]
	if !ok {
		return false
	}
	v := m.verifier
	if v.Generation != s.Generation || time.Now().After(s.Expires) || time.Since(s.Last) > 30*time.Minute {
		delete(m.sessions, cookie.Value)
		return false
	}
	s.Last = time.Now()
	m.sessions[cookie.Value] = s
	return true
}
func (m *Manager) Lock() { m.mu.Lock(); defer m.mu.Unlock(); clear(m.sessions) }
func Cookie(token string) *http.Cookie {
	return &http.Cookie{Name: "kestrel_session", Value: token, Path: "/", HttpOnly: true, SameSite: http.SameSiteStrictMode, MaxAge: 1800}
}

func (m *Manager) Guard(next http.Handler, dev bool) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Referrer-Policy", "no-referrer")
		w.Header().Set("Cache-Control", "no-store")
		if r.Host != "127.0.0.1:8080" && r.Host != "localhost:8080" {
			http.Error(w, "invalid host", 403)
			return
		}
		if r.Method != "GET" && r.Method != "HEAD" {
			origin := r.Header.Get("Origin")
			allowed := origin == "http://127.0.0.1:8080" || origin == "http://localhost:8080" || (dev && origin == "http://127.0.0.1:5173")
			if !allowed && r.URL.Path != "/api/v1/runtime/stop" {
				http.Error(w, "invalid origin", 403)
				return
			}
		}
		// Consume the bounded wire body before handlers can respond/stop. Leaving
		// unread POST bytes can reset Windows TCP connections during close.
		if r.Body != nil && r.Body != http.NoBody {
			body, err := io.ReadAll(http.MaxBytesReader(w, r.Body, 4*1024*1024))
			if err != nil {
				http.Error(w, "request body exceeds limit", 413)
				return
			}
			r.Body.Close()
			r.Body = io.NopCloser(bytes.NewReader(body))
			r.ContentLength = int64(len(body))
		}
		public := r.URL.Path == "/api/v1/health" || r.URL.Path == "/api/v1/ready" || r.URL.Path == "/api/v1/auth/status" || r.URL.Path == "/api/v1/auth/login" || r.URL.Path == "/api/v1/runtime/stop"
		if len(r.URL.Path) >= 8 && r.URL.Path[:8] == "/api/v1/" && !public && !m.Valid(r) {
			http.Error(w, "session locked", 401)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func (m *Manager) Routes(mux *http.ServeMux) {
	mux.HandleFunc("GET /api/v1/auth/status", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]bool{"configured": true, "authenticated": m.Valid(r)})
	})
	mux.HandleFunc("POST /api/v1/auth/login", func(w http.ResponseWriter, r *http.Request) {
		var input struct {
			Username string `json:"username"`
			Password string `json:"password"`
		}
		r.Body = http.MaxBytesReader(w, r.Body, 16384)
		if json.NewDecoder(r.Body).Decode(&input) != nil || len(input.Password) > 1024 || len(input.Username) > 1024 {
			http.Error(w, "invalid login request", 400)
			return
		}
		token, err := m.Login(input.Username, input.Password)
		if err != nil {
			http.Error(w, "login failed or temporarily limited", 401)
			return
		}
		http.SetCookie(w, Cookie(token))
		w.WriteHeader(204)
	})
	mux.HandleFunc("POST /api/v1/auth/lock", func(w http.ResponseWriter, r *http.Request) {
		m.Lock()
		c := Cookie("")
		c.MaxAge = -1
		http.SetCookie(w, c)
		w.WriteHeader(204)
	})
}
