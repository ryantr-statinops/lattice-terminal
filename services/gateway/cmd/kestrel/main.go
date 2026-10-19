package main

import (
	"context"
	"encoding/json"
	"flag"
	"kestrel-terminal/gateway/internal/host"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"time"
)

func handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/v1/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"service": "kestrel-gateway", "status": "ok", "mode": "fixture-only"})
	})
	return mux
}
func main() {
	root := flag.String("root", ".", "Repository root")
	data := flag.String("data", host.DataRoot(), "Local data directory")
	dev := flag.Bool("dev", false, "Start Vite")
	flag.Parse()
	if err := run(*root, *data, *dev); err != nil {
		log.Print(err)
		os.Exit(1)
	}
}

func run(root, data string, dev bool) error {
	root, _ = filepath.Abs(root)
	data, _ = filepath.Abs(data)
	if err := os.MkdirAll(data, 0700); err != nil {
		return err
	}
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt)
	defer cancel()
	engine, err := host.StartEngine(ctx, root, data)
	if err != nil {
		return err
	}
	defer engine.Close()
	if dev {
		stop, err := host.StartVite(ctx, root)
		if err != nil {
			return err
		}
		defer stop()
	}
	mux := handler().(*http.ServeMux)
	target, _ := url.Parse(engine.URL)
	proxy := httputil.NewSingleHostReverseProxy(target)
	base := proxy.Director
	proxy.Director = func(r *http.Request) {
		base(r)
		r.URL.Path = "/internal/v1/" + strings.TrimPrefix(r.URL.Path, "/api/v1/engine/")
		r.Header.Del("Cookie")
		r.Header.Set("Authorization", "Bearer "+engine.Token)
	}
	mux.Handle("/api/v1/engine/", proxy)
	mux.HandleFunc("GET /api/v1/ready", func(w http.ResponseWriter, r *http.Request) {
		req, _ := http.NewRequestWithContext(r.Context(), "GET", engine.URL+"/internal/v1/health", nil)
		req.Header.Set("Authorization", "Bearer "+engine.Token)
		client := http.Client{Timeout: time.Second}
		resp, err := client.Do(req)
		if err != nil {
			http.Error(w, "engine unavailable", 503)
			return
		}
		defer resp.Body.Close()
		w.WriteHeader(resp.StatusCode)
	})
	stopToken := host.Token()
	mux.HandleFunc("POST /api/v1/runtime/stop", func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Authorization") != "Bearer "+stopToken {
			http.Error(w, "unauthorized", 401)
			return
		}
		w.WriteHeader(202)
		cancel()
	})
	state, _ := json.Marshal(map[string]any{"pid": os.Getpid(), "stop_token": stopToken})
	statePath := filepath.Join(data, "runtime.json")
	if err := os.WriteFile(statePath, state, 0600); err != nil {
		return err
	}
	defer os.Remove(statePath)
	dist := filepath.Join(root, "apps", "web", "dist")
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != "GET" && r.Method != "HEAD" {
			http.Error(w, "method not allowed", 405)
			return
		}
		name := strings.TrimPrefix(filepath.Clean(r.URL.Path), string(filepath.Separator))
		if name == "." {
			name = "index.html"
		}
		candidate := filepath.Join(dist, name)
		if _, err := os.Stat(candidate); err != nil {
			if filepath.Ext(name) != "" {
				http.NotFound(w, r)
				return
			}
			candidate = filepath.Join(dist, "index.html")
		}
		http.ServeFile(w, r, candidate)
	})
	server := &http.Server{Addr: "127.0.0.1:8080", Handler: mux, ReadHeaderTimeout: 5 * time.Second}
	go func() {
		<-ctx.Done()
		shutdown, done := context.WithTimeout(context.Background(), 5*time.Second)
		defer done()
		_ = server.Shutdown(shutdown)
	}()
	log.Print("Kestrel Terminal: http://127.0.0.1:8080 (fixture-only)")
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		return err
	}
	return nil
}
