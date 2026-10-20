package secret

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

const composeFileName = "ssi-compose-secret.json"

func ComposeFilePath() (string, error) {
	cache, err := os.UserCacheDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(cache, "KestrelTerminal", composeFileName), nil
}

func PrepareComposeFile(path string) error {
	path, err := filepath.Abs(path)
	if err != nil {
		return err
	}
	if err := rejectWorkspacePath(path); err != nil {
		return err
	}
	value, err := Get()
	if err != nil {
		return errors.New("SSI credentials are not available in the OS keyring")
	}
	return writeComposeFile(path, value)
}

func writeComposeFile(path string, value Credential) error {
	path, err := filepath.Abs(path)
	if err != nil {
		return err
	}
	if err := rejectWorkspacePath(path); err != nil {
		return err
	}
	if value.ConsumerID == "" || value.ConsumerSecret == "" {
		return errors.New("SSI credentials in the OS keyring are incomplete")
	}
	data, err := json.Marshal(value)
	if err != nil {
		return err
	}
	directory := filepath.Dir(path)
	if err := os.MkdirAll(directory, 0700); err != nil {
		return err
	}
	if err := os.Chmod(directory, 0700); err != nil {
		return err
	}
	file, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		if errors.Is(err, os.ErrExist) {
			return errors.New("SSI Compose secret file already exists; inspect or clean it before preparing another")
		}
		return err
	}
	cleanup := true
	defer func() {
		_ = file.Close()
		if cleanup {
			_ = os.Remove(path)
		}
	}()
	if _, err := file.Write(data); err != nil {
		return err
	}
	if err := file.Sync(); err != nil {
		return err
	}
	if err := file.Close(); err != nil {
		return err
	}
	cleanup = false
	return nil
}

func CleanComposeFile(path string) error {
	path, err := filepath.Abs(path)
	if err != nil {
		return err
	}
	if err := rejectWorkspacePath(path); err != nil {
		return err
	}
	info, err := os.Lstat(path)
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	if !info.Mode().IsRegular() {
		return errors.New("refusing to remove a non-regular SSI Compose secret path")
	}
	return os.Remove(path)
}

func rejectWorkspacePath(path string) error {
	working, err := os.Getwd()
	if err != nil {
		return err
	}
	working, err = filepath.Abs(working)
	if err != nil {
		return err
	}
	rel, err := filepath.Rel(working, path)
	if err != nil {
		return err
	}
	if rel == "." || (rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator))) {
		return fmt.Errorf("SSI Compose secret file must be outside the repository working directory")
	}
	return nil
}
