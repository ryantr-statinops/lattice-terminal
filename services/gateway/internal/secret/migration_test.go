package secret

import (
	"encoding/json"
	"errors"
	"os"
	"testing"
)

type migrationVault struct {
	credential []byte
	getErr     error
	setErr     error
	sets       int
}

func (v *migrationVault) Get(string, string) ([]byte, error) {
	if v.getErr != nil {
		return nil, v.getErr
	}
	if v.credential == nil {
		return nil, os.ErrNotExist
	}
	return v.credential, nil
}

func (v *migrationVault) Set(_, _ string, credential []byte) error {
	v.sets++
	if v.setErr != nil {
		return v.setErr
	}
	v.credential = append([]byte(nil), credential...)
	return nil
}

func TestMigrateLegacySSICredentialsCopiesOnce(t *testing.T) {
	vault := &migrationVault{}
	legacyReads := 0
	readLegacy := func() (Credential, error) {
		legacyReads++
		return Credential{ConsumerID: "legacy-id", ConsumerSecret: "legacy-secret"}, nil
	}
	migrated, err := migrateLegacySSI(vault, readLegacy)
	if err != nil || !migrated || vault.sets != 1 || legacyReads != 1 {
		t.Fatalf("migration = %t, sets=%d reads=%d err=%v", migrated, vault.sets, legacyReads, err)
	}
	var copied Credential
	if err = json.Unmarshal(vault.credential, &copied); err != nil || copied != (Credential{ConsumerID: "legacy-id", ConsumerSecret: "legacy-secret"}) {
		t.Fatalf("migrated credential = %#v, %v", copied, err)
	}
	migrated, err = migrateLegacySSI(vault, func() (Credential, error) {
		t.Fatal("existing credential must not read or replace legacy value")
		return Credential{}, nil
	})
	if err != nil || migrated || vault.sets != 1 {
		t.Fatalf("repeat migration = %t, sets=%d err=%v", migrated, vault.sets, err)
	}
}

func TestMigrateLegacySSIFailsClosedForUnreadableOrInvalidRecords(t *testing.T) {
	for _, vault := range []*migrationVault{{getErr: errors.New("vault corrupted")}, {setErr: errors.New("disk unavailable")}} {
		if _, err := migrateLegacySSI(vault, func() (Credential, error) {
			return Credential{ConsumerID: "legacy-id", ConsumerSecret: "legacy-secret"}, nil
		}); err == nil {
			t.Fatal("migration unexpectedly succeeded")
		}
	}
	for _, legacy := range []Credential{{}, {ConsumerID: "id"}, {ConsumerSecret: "secret"}} {
		vault := &migrationVault{}
		if _, err := migrateLegacySSI(vault, func() (Credential, error) { return legacy, nil }); err == nil || vault.sets != 0 {
			t.Fatalf("invalid legacy credential migrated: %#v", legacy)
		}
	}
}
