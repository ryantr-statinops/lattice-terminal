package workspace

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestPathsAndSnapshots(t *testing.T) {
	root := t.TempDir()
	repo := t.TempDir()
	os.MkdirAll(filepath.Join(repo, "services", "engine", "kestrel_engine"), 0700)
	os.WriteFile(filepath.Join(repo, "services", "engine", "uv.lock"), []byte("lock-v1"), 0600)
	w := Workspace{root, repo}
	for _, p := range []string{"../x.py", "x/../../x.py", "C:/x.py", "x\\y.py", ".. /outside.py", "x./file.py", "CON.py", "NUL.txt"} {
		if _, err := w.Path("research", p); err == nil {
			t.Fatal(p)
		}
	}
	if err := w.Write("research", "x.py", "KESTREL_KIND='research'", false); err != nil {
		t.Fatal(err)
	}
	id, err := w.Snapshot("research", "x.py", json.RawMessage(`{}`))
	if err != nil {
		t.Fatal(err)
	}
	w.Write("research", "x.py", "changed", false)
	b, _ := os.ReadFile(filepath.Join(root, "code-snapshots", id, "files", "x.py"))
	if string(b) != "KESTREL_KIND='research'" {
		t.Fatal("snapshot changed")
	}
}
