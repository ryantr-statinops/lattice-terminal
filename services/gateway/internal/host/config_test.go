package host

import (
	"path/filepath"
	"testing"
)

func TestRuntimeConfigDefaultsAndOverrides(t *testing.T) {
	for _, key := range []string{"KESTREL_LISTEN_ADDR", "KESTREL_ENGINE_PYTHON"} {
		t.Setenv(key, "")
	}
	if got := ListenAddress(); got != "127.0.0.1:8080" {
		t.Fatalf("default listen address = %q", got)
	}
	if got := EnginePython("/app"); got != filepath.Join("/app", "services", "engine", ".venv", "bin", "python") && got != filepath.Join("/app", "services", "engine", ".venv", "Scripts", "python.exe") {
		t.Fatalf("unexpected default engine path %q", got)
	}

	t.Setenv("KESTREL_LISTEN_ADDR", "0.0.0.0:8080")
	t.Setenv("KESTREL_ENGINE_PYTHON", "/opt/venv/bin/python")
	if got := ListenAddress(); got != "0.0.0.0:8080" {
		t.Fatalf("listen override = %q", got)
	}
	if got := EnginePython("/app"); got != "/opt/venv/bin/python" {
		t.Fatalf("engine override = %q", got)
	}
}
