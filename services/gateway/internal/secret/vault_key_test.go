package secret

import (
	"errors"
	"testing"
)

func TestEnsureVaultMasterKeyCreatesOnceAndReusesKey(t *testing.T) {
	stored := ""
	writes := 0
	get := func() (string, error) {
		if stored == "" {
			return "", errVaultMasterKeyMissing
		}
		return stored, nil
	}
	set := func(value string) error {
		writes++
		stored = value
		return nil
	}

	first, created, err := ensureVaultMasterKey(get, set)
	if err != nil || !created || len(first) != 32 || writes != 1 {
		t.Fatalf("first bootstrap: len=%d created=%t writes=%d err=%v", len(first), created, writes, err)
	}
	second, created, err := ensureVaultMasterKey(get, set)
	if err != nil || created || writes != 1 || string(first) != string(second) {
		t.Fatalf("second bootstrap did not reuse key: created=%t writes=%d err=%v", created, writes, err)
	}
}

func TestEnsureVaultMasterKeyFailsClosedOnUnreadableKeyring(t *testing.T) {
	_, _, err := ensureVaultMasterKey(func() (string, error) {
		return "", errors.New("keyring locked")
	}, func(string) error {
		t.Fatal("must not replace an unreadable key")
		return nil
	})
	if err == nil {
		t.Fatal("expected locked keyring to fail closed")
	}
}

func TestEnsureVaultMasterKeyRejectsInvalidStoredKey(t *testing.T) {
	_, _, err := ensureVaultMasterKey(func() (string, error) { return "bad-key", nil }, func(string) error {
		t.Fatal("must not overwrite invalid key")
		return nil
	})
	if err == nil {
		t.Fatal("expected invalid stored key to fail")
	}
}
