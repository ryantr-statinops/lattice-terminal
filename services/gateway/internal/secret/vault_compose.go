package secret

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
)

const vaultMasterKeyFileEnv = "KESTREL_VAULT_MASTER_KEY_FILE"
const vaultComposeFileName = "vault-master-key"

func VaultComposeFilePath() (string, error) {
	cache, err := os.UserCacheDir()
	if err != nil {
		return "", errors.New("could not resolve local cache directory")
	}
	return filepath.Join(cache, "KestrelTerminal", vaultComposeFileName), nil
}

// PrepareVaultComposeFile exports the encoded key only to a restricted host file
// that Compose can mount read-only. The key is never printed by this function.
func PrepareVaultComposeFile(path string) error {
	path, err := filepath.Abs(path)
	if err != nil {
		return errors.New("could not resolve vault secret path")
	}
	if err = rejectWorkspacePath(path); err != nil {
		return err
	}
	encoded, err := getVaultKeyringValue()
	if err != nil {
		return errors.New("vault master key is not available in the OS keyring")
	}
	if _, err = decodeVaultMasterKey(encoded); err != nil {
		return errors.New("vault master key in the OS keyring is invalid")
	}
	return writeVaultMasterKeyFile(path, encoded)
}

func writeVaultMasterKeyFile(path, encoded string) error {
	if _, err := decodeVaultMasterKey(encoded); err != nil {
		return errors.New("invalid vault master key")
	}
	path, err := filepath.Abs(path)
	if err != nil {
		return errors.New("could not resolve vault secret path")
	}
	if err = rejectWorkspacePath(path); err != nil {
		return err
	}
	directory := filepath.Dir(path)
	if err = os.MkdirAll(directory, 0700); err != nil {
		return errors.New("could not create vault secret directory")
	}
	if err = os.Chmod(directory, 0700); err != nil {
		return errors.New("could not restrict vault secret directory")
	}
	file, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		if errors.Is(err, os.ErrExist) {
			return errors.New("vault Compose secret already exists; inspect or clean it before preparing another")
		}
		return errors.New("could not create vault Compose secret")
	}
	cleanup := true
	defer func() {
		_ = file.Close()
		if cleanup {
			_ = os.Remove(path)
		}
	}()
	if _, err = file.Write([]byte(strings.TrimSpace(encoded))); err != nil {
		return errors.New("could not write vault Compose secret")
	}
	if err = file.Sync(); err != nil {
		return errors.New("could not persist vault Compose secret")
	}
	if err = file.Close(); err != nil {
		return errors.New("could not close vault Compose secret")
	}
	cleanup = false
	return nil
}

func CleanVaultComposeFile(path string) error {
	path, err := filepath.Abs(path)
	if err != nil {
		return errors.New("could not resolve vault secret path")
	}
	if err = rejectWorkspacePath(path); err != nil {
		return err
	}
	info, err := os.Lstat(path)
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return errors.New("could not inspect vault Compose secret")
	}
	if !info.Mode().IsRegular() {
		return errors.New("refusing to remove a non-regular vault Compose secret path")
	}
	if err = os.Remove(path); err != nil {
		return errors.New("could not remove vault Compose secret")
	}
	return nil
}
