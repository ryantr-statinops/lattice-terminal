package workspace

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestMountDirectoryAndSecurity(t *testing.T) {
	root := t.TempDir()
	repo := t.TempDir()
	customDir := t.TempDir()

	w := Workspace{Root: root, Repository: repo}

	// 1. Initially unmounted
	if _, ok := w.GetMount("research"); ok {
		t.Fatal("expected research not mounted")
	}

	// 2. Reject relative path
	if _, err := w.Mount("research", "relative/path"); err == nil {
		t.Fatal("expected error for relative path")
	}

	// 3. Reject non-existent path
	if _, err := w.Mount("research", filepath.Join(customDir, "does-not-exist")); err == nil {
		t.Fatal("expected error for non-existent path")
	}
	// 3b. Reject system root
	vol := filepath.VolumeName(customDir)
	if _, err := w.Mount("research", vol+string(filepath.Separator)); err == nil {
		t.Fatal("expected error when mounting drive root")
	}

	// 4. Mount valid directory
	mounted, err := w.Mount("research", customDir)
	if err != nil {
		t.Fatalf("failed to mount: %v", err)
	}
	if mounted != customDir {
		t.Fatalf("expected %s, got %s", customDir, mounted)
	}

	// 5. Verify GetMount
	path, ok := w.GetMount("research")
	if !ok || path != customDir {
		t.Fatalf("expected mounted at %s, got %s (ok=%v)", customDir, path, ok)
	}

	// 6. Write and list in mounted directory
	if err := os.WriteFile(filepath.Join(customDir, "custom_strategy.py"), []byte("print('hello')"), 0600); err != nil {
		t.Fatal(err)
	}
	files, err := w.List("research")
	if err != nil {
		t.Fatalf("failed to list mounted workspace: %v", err)
	}
	found := false
	for _, f := range files {
		if f.Path == "custom_strategy.py" {
			found = true
			break
		}
	}
	if !found {
		t.Fatal("custom_strategy.py not found in mounted workspace file list")
	}

	// 7. Verify path traversal in mounted workspace is blocked
	if _, err := w.Path("research", "../escaped.py"); err == nil {
		t.Fatal("expected path traversal to be blocked")
	}

	// 7b. Verify snapshot includes mounted_root
	os.MkdirAll(filepath.Join(repo, "services", "engine", "kestrel_engine"), 0700)
	os.WriteFile(filepath.Join(repo, "services", "engine", "uv.lock"), []byte("lock-v1"), 0600)
	snapID, err := w.Snapshot("research", "custom_strategy.py", []byte(`{}`))
	if err != nil {
		t.Fatalf("failed to take snapshot: %v", err)
	}
	manifestData, err := os.ReadFile(filepath.Join(root, "code-snapshots", snapID, "manifest.json"))
	if err != nil {
		t.Fatalf("failed to read snapshot manifest: %v", err)
	}
	if !strings.Contains(string(manifestData), "mounted_root") {
		t.Fatalf("expected manifest to contain mounted_root, got: %s", string(manifestData))
	}

	// 8. Unmount and verify revert
	if err := w.Unmount("research"); err != nil {
		t.Fatalf("failed to unmount: %v", err)
	}
	if _, ok := w.GetMount("research"); ok {
		t.Fatal("expected research unmounted")
	}
}

