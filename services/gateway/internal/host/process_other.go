//go:build !windows

package host

import (
	"os/exec"
	"syscall"
)

func prepare(cmd *exec.Cmd) error {
	cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
	return nil
}

func attach(cmd *exec.Cmd) (func(), error) {
	return func() {
		if cmd.Process != nil {
			_ = syscall.Kill(-cmd.Process.Pid, syscall.SIGKILL)
		}
	}, nil
}
