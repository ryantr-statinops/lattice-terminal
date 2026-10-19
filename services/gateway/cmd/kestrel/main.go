package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"golang.org/x/term"
	"kestrel-terminal/gateway/internal/api"
	"kestrel-terminal/gateway/internal/auth"
	"kestrel-terminal/gateway/internal/host"
	"kestrel-terminal/gateway/internal/secret"
	"kestrel-terminal/gateway/internal/store"
	"kestrel-terminal/gateway/internal/workspace"
	"log"
	"net"
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
	reset := flag.Bool("reset-password", false, "Reset local password without deleting data")
	credentials := flag.String("ssi-credentials", "", "set, status or delete Windows credentials")
	flag.Parse()
	if *reset || *credentials != "" {
		if err := cli(*data, *reset, *credentials); err != nil {
			log.Print(err)
			os.Exit(1)
		}
		return
	}
	if err := run(*root, *data, *dev); err != nil {
		log.Print(err)
		os.Exit(1)
	}
}

func run(root, data string, dev bool) error {
	listener, err := net.Listen("tcp", "127.0.0.1:8080")
	if err != nil {
		return err
	}
	defer listener.Close()
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
	manager := auth.New(data)
	manager.Routes(mux)
	db, err := store.Open(data)
	if err != nil {
		return err
	}
	defer db.Close()
	bridge := &api.Runner{Engine: engine, Store: db, Context: ctx}
	application := &api.API{Store: db, Workspace: workspace.Workspace{Root: data, Repository: root}, Valid: manager.Valid, StartRun: bridge.Start, StopRun: bridge.Stop, Inspect: bridge.Inspect}
	application.Engine = bridge
	bridge.OnEvent = application.PaperEvent
	bridge.OnFinish = application.FinishPaper
	application.Routes(mux)
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
	server := &http.Server{Addr: "127.0.0.1:8080", Handler: manager.Guard(mux, dev), ReadHeaderTimeout: 5 * time.Second}
	go func() {
		<-ctx.Done()
		shutdown, done := context.WithTimeout(context.Background(), 5*time.Second)
		defer done()
		_ = server.Shutdown(shutdown)
	}()
	log.Print("Kestrel Terminal: http://127.0.0.1:8080 (fixture-only)")
	if err := server.Serve(listener); err != nil && err != http.ErrServerClosed {
		return err
	}
	return nil
}

func cli(data string, reset bool, action string) error {
	if err := os.MkdirAll(data, 0700); err != nil {
		return err
	}
	read := func(prompt string) (string, error) {
		fmt.Fprint(os.Stderr, prompt)
		b, err := term.ReadPassword(int(os.Stdin.Fd()))
		fmt.Fprintln(os.Stderr)
		return string(b), err
	}
	if reset {
		a, err := read("New local password: ")
		if err != nil {
			return err
		}
		b, err := read("Confirm password: ")
		if err != nil {
			return err
		}
		if a != b {
			return fmt.Errorf("passwords differ")
		}
		return auth.New(data).SetPassword(a, true)
	}
	switch action {
	case "set":
		id, err := read("ConsumerID: ")
		if err != nil {
			return err
		}
		value, err := read("ConsumerSecret: ")
		if err != nil {
			return err
		}
		return secret.Set(secret.Credential{ConsumerID: id, ConsumerSecret: value})
	case "delete":
		return secret.Delete()
	case "status":
		_, err := secret.Get()
		if err != nil {
			return fmt.Errorf("SSI credentials not available")
		}
		fmt.Println("SSI credentials present; capability approval unchanged")
		return nil
	default:
		return fmt.Errorf("unknown credential command")
	}
}
