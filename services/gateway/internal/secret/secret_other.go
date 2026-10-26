//go:build !windows

package secret

import (
	"encoding/json"
	"errors"

	"github.com/zalando/go-keyring"
)

const keyringService = "KestrelTerminal/SSI-FC-DATA"
const keyringAccount = "default"

func getVaultKeyringValue() (string, error) {
	value, err := keyring.Get(vaultKeyService, vaultKeyAccount)
	if errors.Is(err, keyring.ErrNotFound) {
		return "", errVaultMasterKeyMissing
	}
	return value, err
}

func setVaultKeyringValue(value string) error {
	return keyring.Set(vaultKeyService, vaultKeyAccount, value)
}

type Credential struct {
	ConsumerID     string
	ConsumerSecret string
}

func Set(value Credential) error {
	if value.ConsumerID == "" || value.ConsumerSecret == "" {
		return errors.New("both credential fields are required")
	}
	data, err := json.Marshal(value)
	if err != nil {
		return redactCredentialError(err, value.ConsumerID, value.ConsumerSecret)
	}
	return redactCredentialError(keyring.Set(keyringService, keyringAccount, string(data)), value.ConsumerID, value.ConsumerSecret, string(data))
}
func Get() (Credential, error) {
	var result Credential
	data, err := keyring.Get(keyringService, keyringAccount)
	if err != nil {
		return result, errors.New("could not read SSI credentials from OS keyring")
	}
	err = json.Unmarshal([]byte(data), &result)
	if err != nil {
		return Credential{}, errors.New("SSI credentials in OS keyring are invalid")
	}
	return result, nil
}
func Delete() error {
	if err := keyring.Delete(keyringService, keyringAccount); err != nil {
		return errors.New("could not delete SSI credentials from OS keyring")
	}
	return nil
}
