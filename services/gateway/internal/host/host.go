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
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

func Token() string {
	var b [32]byte
	if _, err := rand.Read(b[:]); err != nil {
		panic(err)
	}
	return hex.EncodeToString(b[:])
}
func DataRoot() string {
	if v := os.Getenv("LOCALAPPDATA"); v != "" {
		return filepath.Join(v, "KestrelTerminal")
	}
	d, _ := os.UserConfigDir()
	return filepath.Join(d, "KestrelTerminal")
}

type Engine struct {
	URL, Token string
	cmd        *exec.Cmd
	done       chan error
	closeJob   func()
}

func (e *Engine) Close() {
	if e.closeJob != nil {
		e.closeJob()
	}
	if e.cmd != nil && e.cmd.Process != nil {
		_ = e.cmd.Process.Kill()
	}
	select {
	case <-e.done:
	case <-time.After(5 * time.Second):
	}
}

func StartEngine(ctx context.Context, root, data string) (*Engine, error) {
	python := filepath.Join(root, "services", "engine", ".venv", "bin", "python")
	if runtime.GOOS == "windows" {
		python = filepath.Join(root, "services", "engine", ".venv", "Scripts", "python.exe")
	}
	if _, err := os.Stat(python); err != nil {
		return nil, errors.New("Python environment missing; run scripts/setup.ps1")
	}
	token := Token()
	payload, _ := json.Marshal(map[string]string{"token": token, "data_root": data})
	cmd := exec.CommandContext(ctx, python, "-m", "kestrel_engine")
	cmd.Dir = filepath.Join(root, "services", "engine")
	cmd.Stdin = strings.NewReader(string(payload) + "\n")
	cmd.Stderr = os.Stderr
	output, err := cmd.StdoutPipe()
	if err != nil {
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
	client := http.Client{Timeout: time.Second}
	for range 300 {
		req, _ := http.NewRequestWithContext(ctx, "GET", e.URL+"/internal/v1/health", nil)
		req.Header.Set("Authorization", "Bearer "+token)
		response, err := client.Do(req)
		if err == nil {
			response.Body.Close()
			if response.StatusCode == 200 {
				return e, nil
			}
		}
		select {
		case <-ctx.Done():
			e.Close()
			return nil, ctx.Err()
		case <-time.After(100 * time.Millisecond):
		}
	}
	e.Close()
	return nil, errors.New("engine health check failed")
}

func StartVite(ctx context.Context, root string) (func(), error) {
	cmd := exec.CommandContext(ctx, "node", filepath.Join(root, "node_modules", "vite", "bin", "vite.js"), "--host", "127.0.0.1", "--port", "5173", "--strictPort")
	cmd.Dir = filepath.Join(root, "apps", "web")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Start(); err != nil {
		return nil, err
	}
	closeJob, err := attach(cmd)
	if err != nil {
		cmd.Process.Kill()
		cmd.Wait()
		return nil, err
	}
	go cmd.Wait()
	return func() { closeJob(); _ = cmd.Process.Kill() }, nil
}
