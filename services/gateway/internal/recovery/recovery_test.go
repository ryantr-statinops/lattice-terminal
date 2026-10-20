package recovery

import (
	"archive/zip"
	"kestrel-terminal/gateway/internal/store"
	"os"
	"path/filepath"
	"testing"
)

func TestBackupRestoreExcludesSecretsAndNeverResumes(t *testing.T) {
	base := t.TempDir()
	root := filepath.Join(base, "original")
	s, e := store.Open(root)
	if e != nil {
		t.Fatal(e)
	}
	fund, _ := s.CreateFund("Fund", "paper", "1000", "fund")
	book, _ := s.Allocate(fund, "Strategy", "strategy", "300", "book")
	if e = s.BindController(book, "run"); e != nil {
		t.Fatal(e)
	}
	s.Close()
	os.WriteFile(filepath.Join(root, "profile.json"), []byte("private verifier"), 0600)
	os.WriteFile(filepath.Join(root, "source-policy.json"), []byte("private approval"), 0600)
	os.MkdirAll(filepath.Join(root, "workspaces", "research"), 0700)
	os.WriteFile(filepath.Join(root, "workspaces", "research", "sample.py"), []byte("KESTREL_KIND='research'"), 0600)
	os.WriteFile(filepath.Join(root, "workspaces", "research", "common.py"), []byte("VALUE=1"), 0600)
	os.MkdirAll(filepath.Join(root, "market", "snapshots", "fixture"), 0700)
	os.WriteFile(filepath.Join(root, "market", "snapshots", "fixture", "manifest.json"), []byte("synthetic fixture"), 0600)
	archive := filepath.Join(base, "backup.zip")
	if e = Backup(root, archive); e != nil {
		t.Fatal(e)
	}
	restored := filepath.Join(base, "restored")
	if e = Restore(archive, restored); e != nil {
		t.Fatal(e)
	}
	if _, e = os.Stat(filepath.Join(restored, "market", "snapshots", "fixture", "manifest.json")); e != nil {
		t.Fatal("market snapshot missing", e)
	}
	for _, name := range []string{"profile.json", "source-policy.json"} {
		if _, e = os.Stat(filepath.Join(restored, name)); !os.IsNotExist(e) {
			t.Fatal("secret/approval restored")
		}
	}
	s, e = store.Open(restored)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	a, e := s.Allocation(book)
	if e != nil || a.Status != "interrupted" || a.Cash != "300" {
		t.Fatal(a, e)
	}
	if Restore(archive, restored) == nil {
		t.Fatal("overwrote existing restore")
	}
}
func TestUnsafeArchivesDoNotPublish(t *testing.T) {
	for _, name := range []string{"../escape", "workspaces/../../escape", "workspaces/CON.py", "workspaces/a:stream", "workspaces/x.", "profile.json", ".env", "data/secret"} {
		t.Run(name, func(t *testing.T) {
			base := t.TempDir()
			p := filepath.Join(base, "bad.zip")
			f, _ := os.Create(p)
			z := zip.NewWriter(f)
			w, _ := z.Create(name)
			w.Write([]byte("bad"))
			z.Close()
			f.Close()
			dest := filepath.Join(base, "new")
			if Restore(p, dest) == nil {
				t.Fatal("unsafe archive accepted")
			}
			if _, e := os.Stat(dest); !os.IsNotExist(e) {
				t.Fatal("partial destination published")
			}
		})
	}
}
func TestChecksumFailureDoesNotPublish(t *testing.T) {
	base := t.TempDir()
	archive := filepath.Join(base, "corrupt.zip")
	f, _ := os.Create(archive)
	z := zip.NewWriter(f)
	w, _ := z.Create("kestrel.sqlite")
	w.Write([]byte("corrupt"))
	w, _ = z.Create("manifest.json")
	w.Write([]byte(`{"version":1,"files":{"kestrel.sqlite":"wrong"}}`))
	z.Close()
	f.Close()
	dest := filepath.Join(base, "restore")
	if Restore(archive, dest) == nil {
		t.Fatal("corruption accepted")
	}
	if _, e := os.Stat(dest); !os.IsNotExist(e) {
		t.Fatal("partial restore published")
	}
}
