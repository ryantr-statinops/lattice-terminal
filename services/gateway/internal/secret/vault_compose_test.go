package secret

import (
	"bytes"
	"encoding/base64"
	"os"
	"path/filepath"
	"runtime"
	"testing"
)

func TestVaultComposeSecretIsExclusiveAndOpensVault(t *testing.T) {
	root := t.TempDir()
	t.Chdir(root)
	path := filepath.Join(t.TempDir(), "vault-master-key")
	encoded := base64.StdEncoding.EncodeToString(bytes.Repeat([]byte{0x31}, 32))
	if err := writeVaultMasterKeyFile(path, encoded); err != nil {
		t.Fatal(err)
	}
	if runtime.GOOS != "windows" {
		info, err := os.Stat(path)
		if err != nil {
			t.Fatal(err)
		}
		if info.Mode().Perm() != 0600 {
			t.Fatalf("vault secret file mode = %o, want 600", info.Mode().Perm())
		}
	}
	if err := writeVaultMasterKeyFile(path, encoded); err == nil {
		t.Fatal("existing vault secret was overwritten")
	}
	t.Setenv(vaultMasterKeyFileEnv, path)
	vault, err := OpenVault(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	if err = vault.Set("ssi", "market-data", []byte(`{"key":"secret"}`)); err != nil {
		t.Fatal(err)
	}
	if err = CleanVaultComposeFile(path); err != nil {
		t.Fatal(err)
	}
	if _, err = os.Stat(path); !os.IsNotExist(err) {
		t.Fatalf("vault secret remains after cleanup: %v", err)
	}
}

func TestVaultComposeSecretRejectsInvalidKeyAndWorkspacePath(t *testing.T) {
	root := t.TempDir()
	t.Chdir(root)
	if err := writeVaultMasterKeyFile(filepath.Join(root, "key"), "invalid"); err == nil {
		t.Fatal("invalid key accepted")
	}
	encoded := base64.StdEncoding.EncodeToString(bytes.Repeat([]byte{0x42}, 32))
	if err := writeVaultMasterKeyFile(filepath.Join(root, "key"), encoded); err == nil {
		t.Fatal("workspace secret path accepted")
	}
	if _, err := readVaultMasterKeyFile(filepath.Join("relative", "key")); err == nil {
		t.Fatal("relative key file path accepted")
	}
}

func TestOpenVaultRejectsInvalidMountedKeyWithoutKeyringFallback(t *testing.T) {
	path := filepath.Join(t.TempDir(), "vault-master-key")
	if err := os.WriteFile(path, []byte("invalid"), 0600); err != nil {
		t.Fatal(err)
	}
	t.Setenv(vaultMasterKeyFileEnv, path)
	if _, err := OpenVault(t.TempDir()); err == nil {
		t.Fatal("invalid mounted key fell back to OS keyring")
	}
}
