package host

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestLocalConfig(t *testing.T) {
	root := t.TempDir()
	if _, err := ReadLocal(root, "", true); err == nil {
		t.Fatal("missing env accepted")
	}
	t.Setenv("KESTREL_LOCAL_PASSWORD", "ignored-process-password")
	for _, password := range []string{"", "short", "Tiếng Việt $ # mật khẩu"} {
		text := "KESTREL_LOCAL_USERNAME=local\nKESTREL_LOCAL_PASSWORD='" + password + "'\nKESTREL_DATA_DIR=./data\n"
		os.WriteFile(filepath.Join(root, ".env"), []byte(text), 0600)
		c, err := ReadLocal(root, "", true)
		if len(password) < 6 {
			if err == nil {
				t.Fatal("invalid password accepted")
			}
			continue
		}
		if err != nil || c.Password != password || c.DataDir != filepath.Join(root, "data") {
			t.Fatal("config mismatch", err)
		}
		c, err = ReadLocal(root, "isolated", true)
		if err != nil || c.DataDir != filepath.Join(root, "isolated") {
			t.Fatal("override mismatch")
		}
	}
	os.WriteFile(filepath.Join(root, ".env"), []byte("KESTREL_LOCAL_PASSWORD=\"secret-invalid"), 0600)
	if _, err := ReadLocal(root, "", true); err == nil || strings.Contains(err.Error(), "secret-invalid") {
		t.Fatal("unsafe error")
	}
}
