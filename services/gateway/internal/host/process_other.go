//go:build !windows

package host

import "os/exec"

func attach(cmd *exec.Cmd) (func(), error) {
	return func() {
		if cmd.Process != nil {
			_ = cmd.Process.Kill()
		}
	}, nil
}
