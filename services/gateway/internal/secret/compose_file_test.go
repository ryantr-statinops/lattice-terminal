package secret

import (
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"testing"
)

func TestComposeSecretFilePathIsOutsideWorkingTree(t *testing.T) {
	root := t.TempDir()
	t.Chdir(root)
	if err := rejectWorkspacePath(filepath.Join(root, "secret.json")); err == nil {
		t.Fatal("expected workspace secret path to be rejected")
	}
	if err := rejectWorkspacePath(filepath.Join(t.TempDir(), "secret.json")); err != nil {
		t.Fatalf("external secret path rejected: %v", err)
	}
}

func TestCleanComposeSecretFileRejectsDirectories(t *testing.T) {
	root := t.TempDir()
	t.Chdir(root)
	dir := filepath.Join(t.TempDir(), "secret")
	if err := os.Mkdir(dir, 0700); err != nil {
		t.Fatal(err)
	}
	if err := CleanComposeFile(dir); err == nil {
		t.Fatal("expected directory path to be rejected")
	}
}

func TestComposeSecretFileIsExclusiveAndCleanable(t *testing.T) {
	root := t.TempDir()
	path := filepath.Join(root, "ssi-compose-secret.json")
	value := Credential{ConsumerID: "fixture-id", ConsumerSecret: "fixture-secret"}
	if err := writeComposeFile(path, value); err != nil {
		t.Fatal(err)
	}
	if runtime.GOOS != "windows" {
		info, err := os.Stat(path)
		if err != nil {
			t.Fatal(err)
		}
		if info.Mode().Perm() != 0600 {
			t.Fatalf("secret file mode = %o, want 600", info.Mode().Perm())
		}
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var actual Credential
	if err := json.Unmarshal(data, &actual); err != nil || actual != value {
		t.Fatalf("secret file contents did not round-trip: %#v, %v", actual, err)
	}
	if err := writeComposeFile(path, value); err == nil {
		t.Fatal("expected existing secret file to be preserved")
	}
	if err := CleanComposeFile(path); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(path); !os.IsNotExist(err) {
		t.Fatalf("secret file remains after cleanup: %v", err)
	}
}
