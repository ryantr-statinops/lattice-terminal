package host

import (
	"bufio"
	"errors"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

type LocalConfig struct{ Username, Password, DataDir string }

// RepositoryRoot supports scripts and binaries in .cache/bin from any cwd.
func RepositoryRoot(explicit string) (string, error) {
	if explicit != "" {
		return filepath.Abs(explicit)
	}
	cwd, _ := os.Getwd()
	executable, _ := os.Executable()
	for _, start := range []string{cwd, filepath.Dir(executable)} {
		for dir := start; dir != ""; dir = filepath.Dir(dir) {
			if _, err := os.Stat(filepath.Join(dir, "services", "gateway", "go.mod")); err == nil {
				return dir, nil
			}
			if filepath.Dir(dir) == dir {
				break
			}
		}
	}
	return "", errors.New("repository root not found; pass -root explicitly")
}

// ReadLocal reads the repository file, never process credential variables.
// No interpolation is performed: $ and # inside quotes are literal.
func ReadLocal(root, override string, credentials bool) (LocalConfig, error) {
	var c LocalConfig
	f, err := os.Open(filepath.Join(root, ".env"))
	if err != nil {
		return c, errors.New("cannot read repository .env; copy .env.example and configure the local account")
	}
	defer f.Close()
	values := map[string]string{}
	scan := bufio.NewScanner(f)
	scan.Buffer(make([]byte, 4096), 64*1024)
	for scan.Scan() {
		line := strings.TrimSpace(strings.TrimPrefix(scan.Text(), "\ufeff"))
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		key, value, ok := strings.Cut(strings.TrimPrefix(line, "export "), "=")
		if !ok {
			return c, errors.New("invalid .env assignment (values redacted)")
		}
		key, value = strings.TrimSpace(key), strings.TrimSpace(value)
		if strings.HasPrefix(value, "\"") {
			value, err = strconv.Unquote(value)
			if err != nil {
				return c, errors.New("invalid quoted .env value (redacted)")
			}
		} else if strings.HasPrefix(value, "'") {
			if len(value) < 2 || !strings.HasSuffix(value, "'") {
				return c, errors.New("invalid quoted .env value (redacted)")
			}
			value = value[1 : len(value)-1]
		} else if i := strings.Index(value, " #"); i >= 0 {
			value = strings.TrimSpace(value[:i])
		}
		if _, exists := values[key]; exists {
			return c, errors.New("duplicate .env assignment (values redacted)")
		}
		values[key] = value
	}
	if scan.Err() != nil {
		return c, errors.New("cannot parse .env (values redacted)")
	}
	c.Username, c.Password = values["KESTREL_LOCAL_USERNAME"], values["KESTREL_LOCAL_PASSWORD"]
	if credentials && (strings.TrimSpace(c.Username) == "" || len(c.Username) > 1024 || len(c.Password) < 6 || len(c.Password) > 1024) {
		return LocalConfig{}, errors.New("configure KESTREL_LOCAL_USERNAME and KESTREL_LOCAL_PASSWORD (6-1024 bytes) in repository .env, then restart")
	}
	c.DataDir = values["KESTREL_DATA_DIR"]
	if c.DataDir == "" {
		c.DataDir = "data"
	}
	if override != "" {
		c.DataDir = override
	}
	if !filepath.IsAbs(c.DataDir) {
		c.DataDir = filepath.Join(root, c.DataDir)
	}
	c.DataDir, err = filepath.Abs(c.DataDir)
	return c, err
}
