package workspace

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"io/fs"
	"kestrel-terminal/gateway/internal/fileutil"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
)

type Workspace struct{ Root, Repository string }

var (
	mutation     sync.Mutex
	mountedRoots = make(map[string]string)
	mountedMu    sync.RWMutex
)

type File struct {
	Path      string `json:"path"`
	Directory bool   `json:"directory"`
}

func (w Workspace) Mount(kind, targetDir string) (string, error) {
	if kind != "research" && kind != "backtest" && kind != "strategy" {
		return "", errors.New("unknown workspace")
	}
	clean := filepath.Clean(targetDir)
	if !filepath.IsAbs(clean) {
		return "", errors.New("mounted path must be absolute")
	}
	info, err := os.Stat(clean)
	if err != nil {
		return "", errors.New("mounted path does not exist")
	}
	if !info.IsDir() {
		return "", errors.New("mounted path must be a directory")
	}
	vol := filepath.VolumeName(clean)
	if clean == vol+string(filepath.Separator) || clean == "/" {
		return "", errors.New("mounting system root is not permitted")
	}
	mountedMu.Lock()
	mountedRoots[kind] = clean
	mountedMu.Unlock()
	return clean, nil
}

func (w Workspace) Unmount(kind string) error {
	if kind != "research" && kind != "backtest" && kind != "strategy" {
		return errors.New("unknown workspace")
	}
	mountedMu.Lock()
	delete(mountedRoots, kind)
	mountedMu.Unlock()
	return nil
}

func (w Workspace) GetMount(kind string) (string, bool) {
	mountedMu.RLock()
	defer mountedMu.RUnlock()
	p, ok := mountedRoots[kind]
	return p, ok
}

func (w Workspace) area(kind string) (string, error) {
	if kind != "research" && kind != "backtest" && kind != "strategy" {
		return "", errors.New("unknown workspace")
	}
	mountedMu.RLock()
	custom, ok := mountedRoots[kind]
	mountedMu.RUnlock()
	if ok && custom != "" {
		return custom, nil
	}
	root := filepath.Join(w.Root, "workspaces", kind)
	return root, os.MkdirAll(root, 0700)
}
func (w Workspace) Path(kind, name string) (string, error) {
	root, err := w.area(kind)
	if err != nil {
		return "", err
	}
	if !fileutil.SafeRelative(name) || strings.HasPrefix(name, ".trash") {
		return "", errors.New("invalid workspace path")
	}
	p := filepath.Join(root, filepath.FromSlash(name))
	current := p
	for {
		if info, err := os.Lstat(current); err == nil {
			if info.Mode()&os.ModeSymlink != 0 {
				return "", errors.New("workspace symlinks are not allowed")
			}
			resolved, err := filepath.EvalSymlinks(current)
			if err != nil {
				return "", err
			}
			rel, err := filepath.Rel(root, resolved)
			if err != nil || rel == ".." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
				return "", errors.New("path escapes workspace")
			}
		}
		if current == root {
			break
		}
		parent := filepath.Dir(current)
		if parent == current {
			return "", errors.New("invalid root")
		}
		current = parent
	}
	return p, nil
}
func (w Workspace) List(kind string) ([]File, error) {
	root, err := w.area(kind)
	if err != nil {
		return nil, err
	}
	files := []File{}
	err = filepath.WalkDir(root, func(p string, d fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if p == root {
			return nil
		}
		name, _ := filepath.Rel(root, p)
		name = filepath.ToSlash(name)
		if strings.HasPrefix(name, ".trash") {
			if d.IsDir() {
				return fs.SkipDir
			}
			return nil
		}
		if _, err := w.Path(kind, name); err != nil {
			return err
		}
		files = append(files, File{name, d.IsDir()})
		return nil
	})
	sort.Slice(files, func(i, j int) bool { return files[i].Path < files[j].Path })
	return files, err
}
func (w Workspace) Read(kind, name string) (string, error) {
	p, err := w.Path(kind, name)
	if err != nil {
		return "", err
	}
	info, err := os.Stat(p)
	if err != nil {
		return "", err
	}
	if info.Size() > 1024*1024 || info.IsDir() {
		return "", errors.New("not an editable file")
	}
	b, err := os.ReadFile(p)
	return string(b), err
}
func (w Workspace) Write(kind, name, content string, directory bool) error {
	mutation.Lock()
	defer mutation.Unlock()
	p, err := w.Path(kind, name)
	if err != nil {
		return err
	}
	if directory {
		return os.MkdirAll(p, 0700)
	}
	if len(content) > 1024*1024 {
		return errors.New("file too large")
	}
	ext := filepath.Ext(p)
	if ext != ".py" && ext != ".json" && ext != ".md" && ext != ".txt" {
		return errors.New("unsupported text file extension")
	}
	if err = os.MkdirAll(filepath.Dir(p), 0700); err != nil {
		return err
	}
	tmp := p + ".tmp"
	if err = os.WriteFile(tmp, []byte(content), 0600); err != nil {
		return err
	}
	return fileutil.Rename(tmp, p)
}
func (w Workspace) Rename(kind, from, to string) error {
	mutation.Lock()
	defer mutation.Unlock()
	p, err := w.Path(kind, from)
	if err != nil {
		return err
	}
	q, err := w.Path(kind, to)
	if err != nil {
		return err
	}
	if _, err = os.Stat(q); !os.IsNotExist(err) {
		return errors.New("destination exists")
	}
	return os.Rename(p, q)
}
func (w Workspace) Delete(kind, name string) error {
	mutation.Lock()
	defer mutation.Unlock()
	p, err := w.Path(kind, name)
	if err != nil {
		return err
	}
	info, err := os.Stat(p)
	if err != nil {
		return err
	}
	if info.IsDir() {
		return os.Remove(p)
	}
	root, _ := w.area(kind)
	trash := filepath.Join(root, ".trash")
	if err = os.MkdirAll(trash, 0700); err != nil {
		return err
	}
	f, err := os.CreateTemp(trash, "deleted-*")
	if err != nil {
		return err
	}
	q := f.Name()
	f.Close()
	os.Remove(q)
	return os.Rename(p, q)
}
func (w Workspace) Snapshot(kind, entry string, params json.RawMessage) (string, error) {
	mutation.Lock()
	defer mutation.Unlock()
	var object map[string]any
	if json.Unmarshal(params, &object) != nil || object == nil {
		return "", errors.New("snapshot parameters must be an object")
	}
	if _, err := w.Path(kind, entry); err != nil {
		return "", err
	}
	files, err := w.List(kind)
	if err != nil {
		return "", err
	}
	contents := map[string]string{}
	total := 0
	for _, file := range files {
		if file.Directory {
			continue
		}
		text, err := w.Read(kind, file.Path)
		if err != nil {
			return "", err
		}
		total += len(text)
		if total > 10*1024*1024 {
			return "", errors.New("workspace snapshot exceeds 10 MiB")
		}
		contents[file.Path] = text
	}
	if _, ok := contents[entry]; !ok {
		return "", errors.New("entrypoint missing")
	}
	lock, err := os.ReadFile(filepath.Join(w.Repository, "services", "engine", "uv.lock"))
	if err != nil {
		return "", err
	}
	engine, err := engineHash(filepath.Join(w.Repository, "services", "engine", "kestrel_engine"))
	if err != nil {
		return "", err
	}
	manifest := map[string]any{"kind": kind, "entry": entry, "params": params, "files": contents, "dependency_lock": string(lock), "engine_sha256": engine}
	b, _ := json.Marshal(manifest)
	hash := sha256.Sum256(b)
	id := hex.EncodeToString(hash[:])
	dir := filepath.Join(w.Root, "code-snapshots", id)
	if _, err = os.Stat(dir); err == nil {
		return id, nil
	}
	base := filepath.Dir(dir)
	os.MkdirAll(base, 0700)
	tmp, err := os.MkdirTemp(base, "pending-")
	if err != nil {
		return "", err
	}
	defer os.RemoveAll(tmp)
	for name, text := range contents {
		p := filepath.Join(tmp, "files", filepath.FromSlash(name))
		os.MkdirAll(filepath.Dir(p), 0700)
		if err = os.WriteFile(p, []byte(text), 0600); err != nil {
			return "", err
		}
	}
	if err = os.WriteFile(filepath.Join(tmp, "manifest.json"), b, 0600); err != nil {
		return "", err
	}
	return id, fileutil.Rename(tmp, dir)
}
func engineHash(root string) (string, error) {
	files := []string{}
	err := filepath.WalkDir(root, func(p string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !d.IsDir() && strings.HasSuffix(p, ".py") {
			files = append(files, p)
		}
		return nil
	})
	if err != nil {
		return "", err
	}
	sort.Strings(files)
	hash := sha256.New()
	for _, p := range files {
		rel, _ := filepath.Rel(root, p)
		io.WriteString(hash, filepath.ToSlash(rel)+"\x00")
		b, err := os.ReadFile(p)
		if err != nil {
			return "", err
		}
		hash.Write(b)
		hash.Write([]byte{0})
	}
	return hex.EncodeToString(hash.Sum(nil)), nil
}
