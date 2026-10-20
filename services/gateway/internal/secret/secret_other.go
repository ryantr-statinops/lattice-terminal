//go:build !windows

package secret

import (
	"encoding/json"
	"errors"

	"github.com/zalando/go-keyring"
)

const keyringService = "KestrelTerminal/SSI-FC-DATA"
const keyringAccount = "default"

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
		return err
	}
	return keyring.Set(keyringService, keyringAccount, string(data))
}
func Get() (Credential, error) {
	var result Credential
	data, err := keyring.Get(keyringService, keyringAccount)
	if err != nil {
		return result, err
	}
	err = json.Unmarshal([]byte(data), &result)
	return result, err
}
func Delete() error { return keyring.Delete(keyringService, keyringAccount) }
