package secret

import (
	"encoding/json"
	"errors"
	"os"
)

type credentialVault interface {
	Get(provider, service string) ([]byte, error)
	Set(provider, service string, credential []byte) error
}

func migrateLegacySSI(vault credentialVault, readLegacy func() (Credential, error)) (bool, error) {
	if _, err := vault.Get("ssi", "market-data"); err == nil {
		return false, nil
	} else if !errors.Is(err, os.ErrNotExist) {
		return false, errors.New("could not inspect existing SSI vault credential")
	}
	legacy, err := readLegacy()
	if err != nil || legacy.ConsumerID == "" || legacy.ConsumerSecret == "" {
		return false, errors.New("legacy SSI credentials are not available")
	}
	payload, err := json.Marshal(legacy)
	if err != nil {
		return false, errors.New("could not encode legacy SSI credentials")
	}
	if err = vault.Set("ssi", "market-data", payload); err != nil {
		return false, errors.New("could not migrate legacy SSI credentials into the vault")
	}
	return true, nil
}

// MigrateLegacySSICredentials copies the old SSI keyring entry into the encrypted
// provider vault. The original remains in the OS keyring for recovery.
func MigrateLegacySSICredentials(root string) (bool, error) {
	vault, err := OpenVault(root)
	if err != nil {
		return false, errors.New("credential vault is not available; bootstrap its key first")
	}
	return migrateLegacySSI(vault, Get)
}
