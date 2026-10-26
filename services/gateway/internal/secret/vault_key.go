package secret

import (
	"crypto/rand"
	"encoding/base64"
	"errors"
	"fmt"
)

const vaultKeyService = "KestrelTerminal/Vault"
const vaultKeyAccount = "master"

var errVaultMasterKeyMissing = errors.New("vault master key not found")

func ensureVaultMasterKey(get func() (string, error), set func(string) error) ([]byte, bool, error) {
	encoded, err := get()
	if err == nil {
		key, decodeErr := base64.StdEncoding.DecodeString(encoded)
		if decodeErr != nil || len(key) != 32 {
			return nil, false, errors.New("vault master key is invalid")
		}
		return key, false, nil
	}
	if !errors.Is(err, errVaultMasterKeyMissing) {
		return nil, false, errors.New("could not read vault master key from OS keyring")
	}

	key := make([]byte, 32)
	if _, err := rand.Read(key); err != nil {
		return nil, false, errors.New("could not generate vault master key")
	}
	if err := set(base64.StdEncoding.EncodeToString(key)); err != nil {
		return nil, false, errors.New("could not save vault master key to OS keyring")
	}
	return key, true, nil
}

// BootstrapVaultMasterKey creates the master key once and never prints or returns it.
func BootstrapVaultMasterKey() (bool, error) {
	_, created, err := ensureVaultMasterKey(getVaultKeyringValue, setVaultKeyringValue)
	if err != nil {
		return false, fmt.Errorf("vault bootstrap failed: %w", err)
	}
	return created, nil
}

// OpenVault loads the already-bootstrapped key from the OS keyring. It never
// creates or replaces a key while opening stored credentials.
func OpenVault(root string) (*Vault, error) {
	encoded, err := getVaultKeyringValue()
	if err != nil {
		return nil, errors.New("vault master key is not available in the OS keyring")
	}
	key, err := base64.StdEncoding.DecodeString(encoded)
	if err != nil || len(key) != 32 {
		return nil, errors.New("vault master key is invalid")
	}
	return newVault(root, key)
}
