package host

import (
	"bufio"
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"time"
)

func Token() string {
	var b [32]byte
	if _, err := rand.Read(b[:]); err != nil {
		panic(err)
	}
	return hex.EncodeToString(b[:])
}

// ListenAddress is loopback by default. Container deployments can opt in to a
// container-interface bind while keeping the host port published on loopback.
func ListenAddress() string {
	if v := os.Getenv("KESTREL_LISTEN_ADDR"); v != "" {
		return v
	}
	return "127.0.0.1:8080"
}

func EnginePython(root string) string {
	if v := os.Getenv("KESTREL_ENGINE_PYTHON"); v != "" {
		return v
	}
	python := filepath.Join(root, "services", "engine", ".venv", "bin", "python")
	if runtime.GOOS == "windows" {
		python = filepath.Join(root, "services", "engine", ".venv", "Scripts", "python.exe")
	}
	return python
}

type Engine struct {
	URL, Token string
	cmd        *exec.Cmd
	done       chan error
	closeJob   func()
}

func (e *Engine) Close() {
	if e.cmd == nil {
		return
	}
	done := false
	if e.cmd != nil && e.cmd.Process != nil && runtime.GOOS != "windows" {
		_ = e.cmd.Process.Signal(syscall.SIGTERM)
		select {
		case <-e.done:
			done = true
		case <-time.After(8 * time.Second):
		}
	}
	if e.closeJob != nil {
		e.closeJob()
	}
	if !done {
		select {
		case <-e.done:
		case <-time.After(5 * time.Second):
		}
	}
}

func StartEngine(ctx context.Context, root, data string) (*Engine, error) {
	python := EnginePython(root)
	if _, err := os.Stat(python); err != nil {
		return nil, errors.New("Python environment missing; install it with `uv sync --project services/engine --frozen` from the repository root")
	}
	token := Token()
	payload, _ := json.Marshal(map[string]string{"token": token, "data_root": data})
	cmd := exec.Command(python, "-m", "kestrel_engine")
	cmd.Dir = filepath.Join(root, "services", "engine")
	cmd.Stdin = strings.NewReader(string(payload) + "\n")
	cmd.Stderr = os.Stderr
	output, err := cmd.StdoutPipe()
	if err != nil {
		return nil, err
	}
	if err = prepare(cmd); err != nil {
		return nil, err
	}
	if err = cmd.Start(); err != nil {
		return nil, err
	}
	cleanup, err := attach(cmd)
	if err != nil {
		_ = cmd.Process.Kill()
		_ = cmd.Wait()
		return nil, err
	}
	e := &Engine{Token: token, cmd: cmd, done: make(chan error, 1), closeJob: cleanup}
	ready := make(chan struct {
		port int
		err  error
	}, 1)
	go func() {
		r := bufio.NewReader(output)
		line, err := r.ReadString('\n')
		var msg struct {
			Port int `json:"port"`
		}
		if err == nil {
			err = json.Unmarshal([]byte(line), &msg)
		}
		ready <- struct {
			port int
			err  error
		}{msg.Port, err}
		_, _ = io.Copy(io.Discard, r)
	}()
	go func() { e.done <- cmd.Wait() }()
	select {
	case v := <-ready:
		if v.err != nil || v.port < 1 {
			e.Close()
			return nil, errors.New("engine boot failed")
		}
		e.URL = fmt.Sprintf("http://127.0.0.1:%d", v.port)
	case <-time.After(20 * time.Second):
		e.Close()
		return nil, errors.New("engine readiness timeout")
	case <-ctx.Done():
		e.Close()
		return nil, ctx.Err()
	}
	if err := waitEngine(ctx, e, 30*time.Second); err != nil {
		e.Close()
		return nil, err
	}
	return e, nil
}

// ConnectEngine attaches to a separately started loopback engine. The bearer
// token is read from the local .env by the caller and never logged.
func ConnectEngine(ctx context.Context, rawURL, token string) (*Engine, error) {
	if token == "" {
		return nil, errors.New("configure KESTREL_ENGINE_TOKEN in repository .env for terminal debug mode")
	}
	target, err := url.Parse(rawURL)
	if err != nil || target.Scheme != "http" || target.Hostname() == "" || target.Port() == "" || target.User != nil || target.RawQuery != "" || target.Fragment != "" || (target.Path != "" && target.Path != "/") {
		return nil, errors.New("KESTREL_ENGINE_URL must be an http URL to a loopback engine")
	}
	host := target.Hostname()
	if !strings.EqualFold(host, "localhost") && net.ParseIP(host).IsLoopback() == false {
		return nil, errors.New("KESTREL_ENGINE_URL must use localhost or a loopback IP")
	}
	e := &Engine{URL: strings.TrimRight(rawURL, "/"), Token: token}
	if err := waitEngine(ctx, e, 10*time.Second); err != nil {
		return nil, fmt.Errorf("cannot connect to terminal debug engine: %w", err)
	}
	return e, nil
}

func waitEngine(ctx context.Context, e *Engine, timeout time.Duration) error {
	return waitEngineWithClient(ctx, e, timeout, &http.Client{Timeout: time.Second})
}

func waitEngineWithClient(ctx context.Context, e *Engine, timeout time.Duration, client *http.Client) error {
	deadline := time.NewTimer(timeout)
	defer deadline.Stop()
	var lastErr error
	for {
		req, err := http.NewRequestWithContext(ctx, "GET", e.URL+"/internal/v1/health", nil)
		if err == nil {
			req.Header.Set("Authorization", "Bearer "+e.Token)
			response, requestErr := client.Do(req)
			if requestErr == nil {
				response.Body.Close()
				if response.StatusCode == http.StatusOK {
					return nil
				}
				if response.StatusCode == http.StatusUnauthorized {
					return errors.New("engine token rejected; check KESTREL_ENGINE_TOKEN in repository .env")
				}
				lastErr = fmt.Errorf("engine health returned HTTP %d", response.StatusCode)
			} else {
				lastErr = requestErr
			}
		} else {
			lastErr = err
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-deadline.C:
			if lastErr == nil {
				lastErr = errors.New("engine readiness timeout")
			}
			return lastErr
		case <-time.After(100 * time.Millisecond):
		}
	}
}
