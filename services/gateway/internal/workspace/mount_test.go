package workspace

import (
	"os"
	"path/filepath"
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

	// 8. Unmount and verify revert
	if err := w.Unmount("research"); err != nil {
		t.Fatalf("failed to unmount: %v", err)
	}
	if _, ok := w.GetMount("research"); ok {
		t.Fatal("expected research unmounted")
	}
}
