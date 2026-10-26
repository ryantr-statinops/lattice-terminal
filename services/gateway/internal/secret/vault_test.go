package secret

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"testing"
)

func TestVaultPersistsCredentialsOnlyAsCiphertext(t *testing.T) {
	root := t.TempDir()
	key := bytes.Repeat([]byte{0x5a}, 32)
	vault, err := newVault(root, key)
	if err != nil {
		t.Fatal(err)
	}
	secret := []byte(`{"api_key":"private-value","api_secret":"another-private-value"}`)
	if err = vault.Set("ssi", "market-data", secret); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(root, "provider-vault", "credentials.json")
	stored, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	for _, value := range [][]byte{[]byte("private-value"), []byte("another-private-value")} {
		if bytes.Contains(stored, value) {
			t.Fatal("credential plaintext found in vault file")
		}
	}
	info, err := os.Stat(path)
	if err != nil {
		t.Fatal(err)
	}
	if runtime.GOOS != "windows" && info.Mode().Perm()&0077 != 0 {
		t.Fatalf("vault file permissions are too broad: %o", info.Mode().Perm())
	}

	reopened, err := newVault(root, key)
	if err != nil {
		t.Fatal(err)
	}
	got, err := reopened.Get("ssi", "market-data")
	if err != nil || !bytes.Equal(got, secret) {
		t.Fatalf("reopened credential differs: %q, %v", got, err)
	}
}

func TestVaultRejectsWrongKeyAndTamperedCiphertext(t *testing.T) {
	root := t.TempDir()
	vault, err := newVault(root, bytes.Repeat([]byte{1}, 32))
	if err != nil {
		t.Fatal(err)
	}
	if err = vault.Set("dnse", "market-data", []byte(`{"key":"value"}`)); err != nil {
		t.Fatal(err)
	}
	wrongKeyVault, err := newVault(root, bytes.Repeat([]byte{2}, 32))
	if err != nil {
		t.Fatal(err)
	}
	if _, err = wrongKeyVault.Get("dnse", "market-data"); err == nil {
		t.Fatal("wrong key decrypted credential")
	}

	path := filepath.Join(root, "provider-vault", "credentials.json")
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var doc vaultDocument
	if err = json.Unmarshal(data, &doc); err != nil {
		t.Fatal(err)
	}
	record := doc.Records[vaultRecordKey("dnse", "market-data")]
	ciphertext, err := base64.StdEncoding.DecodeString(record.Ciphertext)
	if err != nil {
		t.Fatal(err)
	}
	ciphertext[0] ^= 1
	record.Ciphertext = base64.StdEncoding.EncodeToString(ciphertext)
	doc.Records[vaultRecordKey("dnse", "market-data")] = record
	data, err = json.Marshal(doc)
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	if _, err = vault.Get("dnse", "market-data"); err == nil {
		t.Fatal("tampered ciphertext decrypted")
	}
}

func TestVaultValidatesCredentialReferenceAndJSON(t *testing.T) {
	vault, err := newVault(t.TempDir(), bytes.Repeat([]byte{7}, 32))
	if err != nil {
		t.Fatal(err)
	}
	for _, tc := range []struct {
		provider string
		service  string
		payload  []byte
	}{
		{"../ssi", "market-data", []byte(`{"key":"x"}`)},
		{"ssi", "market data", []byte(`{"key":"x"}`)},
		{"ssi", "market-data", []byte("not-json")},
		{"ssi", "market-data", nil},
	} {
		if err = vault.Set(tc.provider, tc.service, tc.payload); err == nil {
			t.Fatalf("accepted invalid credential %q/%q", tc.provider, tc.service)
		}
	}
}

func TestVaultDeleteRemovesCredential(t *testing.T) {
	vault, err := newVault(t.TempDir(), bytes.Repeat([]byte{9}, 32))
	if err != nil {
		t.Fatal(err)
	}
	if err = vault.Set("tcbs", "openapi", []byte(`{"api_key":"secret"}`)); err != nil {
		t.Fatal(err)
	}
	if err = vault.Delete("tcbs", "openapi"); err != nil {
		t.Fatal(err)
	}
	if _, err = vault.Get("tcbs", "openapi"); !os.IsNotExist(err) {
		t.Fatalf("deleted credential still present: %v", err)
	}
}
