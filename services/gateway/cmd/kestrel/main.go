package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"os/signal"
	"path"
	"path/filepath"
	"strings"
	"syscall"
	"time"

	"kestrel-terminal/gateway/internal/api"
	"kestrel-terminal/gateway/internal/auth"
	"kestrel-terminal/gateway/internal/fileutil"
	"kestrel-terminal/gateway/internal/host"
	"kestrel-terminal/gateway/internal/recovery"
	"kestrel-terminal/gateway/internal/secret"
	"kestrel-terminal/gateway/internal/store"
	"kestrel-terminal/gateway/internal/terminal"
	"kestrel-terminal/gateway/internal/workspace"

	"golang.org/x/term"
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
	root := flag.String("root", "", "Repository root (auto-detected)")
	data := flag.String("data", "", "Override .env local data directory")
	printData := flag.Bool("print-data-dir", false, "Print resolved data directory without credentials")
	checkConfig := flag.Bool("check-config", false, "Validate local account configuration without displaying it")
	dev := flag.Bool("dev", false, "Allow the Vite development origin")
	reset := flag.Bool("reset-password", false, "Show how to change the account in .env")
	credentials := flag.String("ssi-credentials", "", "set, status or delete OS keyring credentials")
	prepareSSISecret := flag.Bool("prepare-ssi-compose-secret", false, "write a temporary Compose secret file from the OS keyring")
	cleanSSISecret := flag.Bool("clean-ssi-compose-secret", false, "remove the temporary Compose secret file")
	bootstrapVault := flag.Bool("bootstrap-vault", false, "create the encrypted credential vault master key in the OS keyring")
	migrateSSICredentials := flag.Bool("migrate-ssi-credentials", false, "copy legacy SSI credentials into the encrypted provider vault")
	prepareVaultSecret := flag.Bool("prepare-vault-compose-secret", false, "write a temporary Compose secret file from the OS keyring")
	cleanVaultSecret := flag.Bool("clean-vault-compose-secret", false, "remove the temporary Compose vault secret file")
	backup := flag.String("backup", "", "Offline backup ZIP outside the data directory")
	restore := flag.String("restore", "", "Restore ZIP into a new -data directory")
	diagnostics := flag.Bool("diagnostics", false, "Print redacted runtime configuration; no payloads")
	flag.Parse()
	if *reset {
		fmt.Println("Edit KESTREL_LOCAL_USERNAME and KESTREL_LOCAL_PASSWORD in repository .env, save, then restart Kestrel. No profile file was changed.")
		return
	}
	if *diagnostics {
		fmt.Println(`{"product":"Kestrel Terminal","storage_schema":1,"source_mode":"fixture-only","secrets":"Windows Credential Manager (not inspected)","auto_resume":false}`)
		return
	}
	resolvedRoot, configErr := host.RepositoryRoot(*root)
	if configErr != nil {
		log.Fatal(configErr)
	}
	config, configErr := host.ReadLocal(resolvedRoot, *data, *checkConfig)
	if configErr != nil {
		log.Fatal(configErr)
	}
	*root, *data = resolvedRoot, config.DataDir
	if *printData {
		fmt.Println(*data)
		return
	}
	if *checkConfig {
		fmt.Println("Local account configuration is valid")
		return
	}
	if *backup != "" || *restore != "" || *reset || *credentials != "" || *prepareSSISecret || *cleanSSISecret || *bootstrapVault || *migrateSSICredentials || *prepareVaultSecret || *cleanVaultSecret {
		lock, err := net.Listen("tcp", host.ListenAddress())
		if err != nil {
			log.Print("Stop Kestrel Terminal before offline maintenance")
			os.Exit(1)
		}
		defer lock.Close()
		if *backup != "" || *restore != "" {
			if *backup != "" && *restore != "" {
				log.Print("Choose backup or restore")
				os.Exit(1)
			}
			var err error
			if *backup != "" {
				err = recovery.Backup(*data, *backup)
			} else {
				err = recovery.Restore(*restore, *data)
			}
			if err != nil {
				log.Print(err)
				os.Exit(1)
			}
			fmt.Println("Offline maintenance complete; no sessions resumed; backup files are not encrypted")
			return
		}
		if *prepareSSISecret && *cleanSSISecret {
			log.Print("Choose prepare or clean SSI Compose secret")
			os.Exit(1)
		}
		if *prepareVaultSecret && *cleanVaultSecret {
			log.Print("Choose prepare or clean vault Compose secret")
			os.Exit(1)
		}
		if *bootstrapVault {
			created, err := secret.BootstrapVaultMasterKey()
			if err != nil {
				log.Print(err)
				os.Exit(1)
			}
			if created {
				fmt.Println("Vault master key created in OS keyring")
			} else {
				fmt.Println("Vault master key already present in OS keyring")
			}
			return
		}
		if *migrateSSICredentials {
			migrated, err := secret.MigrateLegacySSICredentials(*data)
			if err != nil {
				log.Print(err)
				os.Exit(1)
			}
			if migrated {
				fmt.Println("Legacy SSI credentials copied into encrypted provider vault")
			} else {
				fmt.Println("Encrypted provider vault already contains SSI market-data credentials")
			}
			return
		}
		if *prepareVaultSecret {
			secretPath, err := secret.VaultComposeFilePath()
			if err == nil {
				err = secret.PrepareVaultComposeFile(secretPath)
			}
			if err != nil {
				log.Print(err)
				os.Exit(1)
			}
			fmt.Println(secretPath)
			return
		}
		if *cleanVaultSecret {
			secretPath, err := secret.VaultComposeFilePath()
			if err == nil {
				err = secret.CleanVaultComposeFile(secretPath)
			}
			if err != nil {
				log.Print(err)
				os.Exit(1)
			}
			return
		}
		if *prepareSSISecret {
			secretPath, err := secret.ComposeFilePath()
			if err == nil {
				err = secret.PrepareComposeFile(secretPath)
			}
			if err != nil {
				log.Print(err)
				os.Exit(1)
			}
			fmt.Println(secretPath)
			return
		}
		if *cleanSSISecret {
			secretPath, err := secret.ComposeFilePath()
			if err == nil {
				err = secret.CleanComposeFile(secretPath)
			}
			if err != nil {
				log.Print(err)
				os.Exit(1)
			}
			return
		}
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
	config, err := host.ReadLocal(root, data, true)
	if err != nil {
		return err
	}
	listenAddress := host.ListenAddress()
	listener, err := net.Listen("tcp", listenAddress)
	if err != nil {
		return err
	}
	defer listener.Close()
	root, _ = filepath.Abs(root)
	data, _ = filepath.Abs(data)
	if err := os.MkdirAll(data, 0700); err != nil {
		return err
	}
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()
	var engine *host.Engine
	if engineURL := os.Getenv("KESTREL_ENGINE_URL"); engineURL != "" {
		engine, err = host.ConnectEngine(ctx, engineURL, config.EngineToken)
	} else {
		engine, err = host.StartEngine(ctx, root, data)
	}
	if err != nil {
		return err
	}
	defer engine.Close()
	mux := handler().(*http.ServeMux)
	manager := auth.New(config.Username, config.Password)
	config.Password = ""
	config.EngineToken = ""
	mux.HandleFunc("GET /api/v1/local/config", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"data_dir": data, "account_source": ".env"})
	})
	manager.Routes(mux)
	db, err := store.Open(data)
	if err != nil {
		return err
	}
	defer db.Close()
	vault, _ := secret.OpenVault(data)
	bridge := &api.Runner{Engine: engine, Store: db, Context: ctx}
	routingPolicy, err := db.RoutingPolicy()
	if err != nil {
		return err
	}
	if err = bridge.ApplyRoutingPolicy(routingPolicy); err != nil {
		return fmt.Errorf("could not restore provider routing: %w", err)
	}
	defer func() { cancel(); bridge.Wait() }()
	application := &api.API{Store: db, Credentials: vault, Workspace: workspace.Workspace{Root: data, Repository: root}, Valid: manager.Valid, StartRun: bridge.Start, StopRun: bridge.Stop, Inspect: bridge.Inspect, Terminal: terminal.NewManager(root)}
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
	mux.Handle("/api/v1/engine/", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		path := strings.TrimPrefix(r.URL.Path, "/api/v1/engine")
		allowed := r.Method == "GET" && (path == "/market/instruments" || path == "/market/snapshots" || path == "/market/candles" || path == "/market/live-status" || path == "/quant/indicators" || path == "/quant/calculate" || path == "/backtest/data" || path == "/sources")
		allowed = allowed || (r.Method == "POST" && path == "/programs/inspect")
		if !allowed {
			http.NotFound(w, r)
			return
		}
		proxy.ServeHTTP(w, r)
	}))
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
		if _, err := io.Copy(io.Discard, http.MaxBytesReader(w, r.Body, 4096)); err != nil {
			http.Error(w, "invalid stop body", 400)
			return
		}
		w.Header().Set("Content-Length", "0")
		w.Header().Set("Connection", "close")
		w.WriteHeader(202)
		if flusher, ok := w.(http.Flusher); ok {
			flusher.Flush()
		}
		cancel()
	})
	state, _ := json.Marshal(map[string]any{"pid": os.Getpid(), "stop_token": stopToken})
	statePath := filepath.Join(data, "runtime.json")
	if err := os.WriteFile(statePath, state, 0600); err != nil {
		return err
	}
	defer os.Remove(statePath)
	dist := os.Getenv("KESTREL_WEB_DIST")
	if dist == "" {
		dist = filepath.Join(root, "apps", "web", "dist")
	}
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if strings.HasPrefix(r.URL.Path, "/api/") {
			http.NotFound(w, r)
			return
		}
		if r.Method != "GET" && r.Method != "HEAD" {
			http.Error(w, "method not allowed", 405)
			return
		}
		name := strings.TrimPrefix(path.Clean(r.URL.Path), "/")
		if name == "." || name == "" {
			name = "index.html"
		}
		if !fileutil.SafeRelative(name) {
			http.NotFound(w, r)
			return
		}
		candidate := filepath.Join(dist, name)
		if info, err := os.Stat(candidate); err != nil || info.IsDir() {
			if filepath.Ext(name) != "" {
				http.NotFound(w, r)
				return
			}
			candidate = filepath.Join(dist, "index.html")
		}
		http.ServeFile(w, r, candidate)
	})
	server := &http.Server{Addr: listenAddress, Handler: manager.Guard(mux, dev), ReadHeaderTimeout: 5 * time.Second, BaseContext: func(net.Listener) context.Context { return ctx }}
	shutdownDone := make(chan struct{})
	go func() {
		defer close(shutdownDone)
		<-ctx.Done()
		shutdown, done := context.WithTimeout(context.Background(), 5*time.Second)
		defer done()
		_ = server.Shutdown(shutdown)
	}()
	log.Print("Kestrel Terminal: http://127.0.0.1:8080 (fixture-only)")
	err = server.Serve(listener)
	cancel()
	<-shutdownDone
	_ = server.Close()
	if err != nil && err != http.ErrServerClosed {
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
