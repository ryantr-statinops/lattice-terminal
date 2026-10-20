// Package recovery implements offline, checksummed backups. It never erases data.
package recovery

import (
	"archive/zip"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"kestrel-terminal/gateway/internal/fileutil"
	_ "modernc.org/sqlite"
	"os"
	"path"
	"path/filepath"
	"strings"
)

const maxBytes int64 = 2 * 1024 * 1024 * 1024

type Manifest struct {
	Version int               `json:"version"`
	Files   map[string]string `json:"files"`
}

func allowed(name string) bool {
	if !fileutil.SafeRelative(name) {
		return false
	}
	if name == "kestrel.sqlite" {
		return true
	}
	first, _, ok := strings.Cut(name, "/")
	return ok && (first == "workspaces" || first == "code-snapshots" || first == "market" || first == "artifacts")
}
func hash(b []byte) string { sum := sha256.Sum256(b); return hex.EncodeToString(sum[:]) }

// Backup requires the caller to hold the application's single-instance listener.
// SQLite VACUUM INTO includes committed WAL data without copying a live database file.
func Backup(root, output string) error {
	root, err := filepath.Abs(root)
	if err != nil {
		return err
	}
	output, err = filepath.Abs(output)
	if err != nil {
		return err
	}
	rel, err := filepath.Rel(root, output)
	if err != nil || rel == "." || (!strings.HasPrefix(rel, ".."+string(filepath.Separator)) && rel != "..") {
		return errors.New("backup destination must be outside application data")
	}
	if _, err = os.Stat(filepath.Join(root, "kestrel.sqlite")); err != nil {
		return err
	}
	temp, err := os.MkdirTemp(filepath.Dir(output), ".kestrel-backup-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(temp)
	db, err := sql.Open("sqlite", filepath.Join(root, "kestrel.sqlite"))
	if err != nil {
		return err
	}
	copyDB := filepath.Join(temp, "kestrel.sqlite")
	_, err = db.Exec("VACUUM INTO ?", copyDB)
	db.Close()
	if err != nil {
		return err
	}
	target, err := os.OpenFile(output, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return err
	}
	success := false
	defer func() {
		target.Close()
		if !success {
			os.Remove(output)
		}
	}()
	writer := zip.NewWriter(target)
	defer writer.Close()
	manifest := Manifest{Version: 1, Files: map[string]string{}}
	var size int64
	add := func(name, p string) error {
		if !allowed(name) {
			return errors.New("managed file has unsupported Windows backup path")
		}
		info, err := os.Stat(p)
		if err != nil {
			return err
		}
		size += info.Size()
		if info.Size() > 256*1024*1024 || size > maxBytes || len(manifest.Files) >= 50000 {
			return errors.New("backup exceeds 256 MiB per file / 2 GiB total / 50000 files")
		}
		b, err := os.ReadFile(p)
		if err != nil {
			return err
		}
		w, err := writer.Create(name)
		if err != nil {
			return err
		}
		if _, err = w.Write(b); err != nil {
			return err
		}
		manifest.Files[name] = hash(b)
		return nil
	}
	if err = add("kestrel.sqlite", copyDB); err != nil {
		return err
	}
	for _, dir := range []string{"workspaces", "code-snapshots", "market", "artifacts"} {
		base := filepath.Join(root, dir)
		if _, err = os.Stat(base); os.IsNotExist(err) {
			continue
		}
		err = filepath.WalkDir(base, func(p string, d fs.DirEntry, e error) error {
			if e != nil {
				return e
			}
			resolved, e := filepath.EvalSymlinks(p)
			if e != nil {
				return e
			}
			relative, e := filepath.Rel(root, resolved)
			if e != nil || relative == ".." || strings.HasPrefix(relative, ".."+string(filepath.Separator)) || d.Type()&os.ModeSymlink != 0 {
				return errors.New("backup refuses links outside managed data")
			}
			if d.IsDir() {
				return nil
			}
			if !d.Type().IsRegular() {
				return errors.New("backup requires regular files")
			}
			name, _ := filepath.Rel(root, p)
			return add(filepath.ToSlash(name), p)
		})
		if err != nil {
			return err
		}
	}
	b, _ := json.Marshal(manifest)
	w, err := writer.Create("manifest.json")
	if err != nil {
		return err
	}
	if _, err = w.Write(b); err != nil {
		return err
	}
	if err = writer.Close(); err != nil {
		return err
	}
	if err = target.Sync(); err != nil {
		return err
	}
	if err = target.Close(); err != nil {
		return err
	}
	success = true
	return nil
}

// Restore only publishes a new directory after all entries validate. Credentials,
// session verifiers and source approvals are intentionally absent from backups.
func Restore(archive, destination string) error {
	destination, err := filepath.Abs(destination)
	if err != nil {
		return err
	}
	if _, err = os.Lstat(destination); !os.IsNotExist(err) {
		return errors.New("restore destination must not exist")
	}
	z, err := zip.OpenReader(archive)
	if err != nil {
		return err
	}
	defer z.Close()
	if len(z.File) > 50001 {
		return errors.New("too many backup entries")
	}
	entries := map[string]*zip.File{}
	var total uint64
	for _, f := range z.File {
		if f.UncompressedSize64 > 256*1024*1024 {
			return errors.New("backup entry exceeds 256 MiB")
		}
		if f.Name != "manifest.json" && !allowed(f.Name) {
			return fmt.Errorf("unsupported backup path: %s", f.Name)
		}
		if path.Clean(f.Name) != f.Name || f.FileInfo().IsDir() || f.Mode()&os.ModeSymlink != 0 || entries[f.Name] != nil {
			return errors.New("invalid or duplicate backup entry")
		}
		total += f.UncompressedSize64
		if total > uint64(maxBytes) {
			return errors.New("backup exceeds 2 GiB")
		}
		entries[f.Name] = f
	}
	seen := map[string]bool{}
	for name := range entries {
		lower := strings.ToLower(name)
		if seen[lower] {
			return errors.New("case-colliding backup paths")
		}
		seen[lower] = true
	}
	mf := entries["manifest.json"]
	if mf == nil || mf.UncompressedSize64 > 10*1024*1024 {
		return errors.New("missing or oversized manifest")
	}
	read := func(f *zip.File) ([]byte, error) {
		r, e := f.Open()
		if e != nil {
			return nil, e
		}
		defer r.Close()
		return io.ReadAll(io.LimitReader(r, int64(f.UncompressedSize64)+1))
	}
	b, err := read(mf)
	if err != nil {
		return err
	}
	var manifest Manifest
	if json.Unmarshal(b, &manifest) != nil || manifest.Version != 1 || len(manifest.Files) != len(entries)-1 || manifest.Files["kestrel.sqlite"] == "" {
		return errors.New("invalid backup manifest")
	}
	stage, err := os.MkdirTemp(filepath.Dir(destination), ".kestrel-restore-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(stage)
	for name, want := range manifest.Files {
		f := entries[name]
		if f == nil || !allowed(name) {
			return errors.New("manifest path missing or invalid")
		}
		b, err = read(f)
		if err != nil {
			return err
		}
		if hash(b) != want {
			return errors.New("backup checksum mismatch")
		}
		p := filepath.Join(stage, filepath.FromSlash(name))
		if err = os.MkdirAll(filepath.Dir(p), 0700); err != nil {
			return err
		}
		if err = os.WriteFile(p, b, 0600); err != nil {
			return err
		}
	}
	db, err := sql.Open("sqlite", filepath.Join(stage, "kestrel.sqlite"))
	if err != nil {
		return err
	}
	var integrity string
	err = db.QueryRow("PRAGMA integrity_check").Scan(&integrity)
	if err == nil && integrity == "ok" {
		var version int
		err = db.QueryRow("SELECT MAX(version) FROM migrations").Scan(&version)
		if err == nil && version != 1 {
			err = errors.New("unsupported database version")
		}
	}
	if err == nil && integrity == "ok" {
		_, err = db.Exec("UPDATE runs SET status='interrupted' WHERE status IN ('queued','running','stopping'); UPDATE allocations SET status='interrupted',controller='' WHERE mode IN ('manual','strategy');")
	}
	db.Close()
	if err != nil {
		return err
	}
	if integrity != "ok" {
		return errors.New("database integrity check failed")
	}
	return os.Rename(stage, destination)
}
