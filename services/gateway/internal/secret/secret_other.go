//go:build !windows

package secret

import "errors"

type Credential struct {
	ConsumerID     string
	ConsumerSecret string
}

func Set(Credential) error { return errors.New("Windows Credential Manager is required") }
func Get() (Credential, error) {
	return Credential{}, errors.New("Windows Credential Manager is required")
}
func Delete() error { return errors.New("Windows Credential Manager is required") }
