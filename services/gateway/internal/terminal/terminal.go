package terminal

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"io"
	"os/exec"
	"runtime"
	"sync"
)

type Session struct {
	ID        string
	cmd       *exec.Cmd
	stdin     io.WriteCloser
	mu        sync.Mutex
	listeners map[chan []byte]struct{}
	closed    bool
}

type Manager struct {
	mu       sync.RWMutex
	sessions map[string]*Session
	repoRoot string
}

func NewManager(repoRoot string) *Manager {
	return &Manager{
		sessions: make(map[string]*Session),
		repoRoot: repoRoot,
	}
}

func (m *Manager) CreateSession(cwd string) (*Session, error) {
	if cwd == "" {
		cwd = m.repoRoot
	}

	var shell string
	var args []string
	if runtime.GOOS == "windows" {
		shell = "powershell.exe"
		args = []string{"-NoLogo", "-NoExit"}
	} else {
		shell = "/bin/bash"
		if _, err := exec.LookPath(shell); err != nil {
			shell = "/bin/sh"
		}
		args = []string{"-i"}
	}

	cmd := exec.Command(shell, args...)
	cmd.Dir = cwd

	stdin, err := cmd.StdinPipe()
	if err != nil {
		return nil, err
	}

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, err
	}
	cmd.Stderr = cmd.Stdout // merge stderr into stdout pipe

	idBytes := make([]byte, 8)
	rand.Read(idBytes)
	sessionID := hex.EncodeToString(idBytes)

	session := &Session{
		ID:        sessionID,
		cmd:       cmd,
		stdin:     stdin,
		listeners: make(map[chan []byte]struct{}),
	}

	if err := cmd.Start(); err != nil {
		return nil, err
	}

	// Reader goroutine
	go func() {
		buf := make([]byte, 4096)
		for {
			n, readErr := stdout.Read(buf)
			if n > 0 {
				data := make([]byte, n)
				copy(data, buf[:n])
				session.broadcast(data)
			}
			if readErr != nil {
				break
			}
		}
		session.Close()
		m.RemoveSession(sessionID)
	}()

	m.mu.Lock()
	m.sessions[sessionID] = session
	m.mu.Unlock()

	return session, nil
}

func (m *Manager) GetSession(id string) (*Session, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	s, ok := m.sessions[id]
	return s, ok
}

func (m *Manager) RemoveSession(id string) {
	m.mu.Lock()
	s, ok := m.sessions[id]
	if ok {
		delete(m.sessions, id)
	}
	m.mu.Unlock()
	if ok && s != nil {
		s.Close()
	}
}

func (s *Session) WriteInput(data []byte) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.closed || s.stdin == nil {
		return errors.New("session closed")
	}
	_, err := s.stdin.Write(data)
	return err
}

func (s *Session) Subscribe() chan []byte {
	s.mu.Lock()
	defer s.mu.Unlock()
	ch := make(chan []byte, 32)
	if !s.closed {
		s.listeners[ch] = struct{}{}
	} else {
		close(ch)
	}
	return ch
}

func (s *Session) Unsubscribe(ch chan []byte) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.listeners, ch)
	close(ch)
}

func (s *Session) broadcast(data []byte) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for ch := range s.listeners {
		select {
		case ch <- data:
		default:
			// listener buffer full, drop to prevent blocking
		}
	}
}

func (s *Session) Close() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.closed {
		return nil
	}
	s.closed = true
	if s.stdin != nil {
		s.stdin.Close()
	}
	if s.cmd != nil && s.cmd.Process != nil {
		_ = s.cmd.Process.Kill()
	}
	for ch := range s.listeners {
		close(ch)
	}
	s.listeners = make(map[chan []byte]struct{})
	return nil
}
