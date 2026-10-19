//go:build windows

package host

import (
	"fmt"
	"os/exec"
	"syscall"
	"unsafe"
)

// A Job Object closes the complete child process tree on gateway exit.
func attach(cmd *exec.Cmd) (func(), error) {
	kernel := syscall.NewLazyDLL("kernel32.dll")
	job, _, err := kernel.NewProc("CreateJobObjectW").Call(0, 0)
	if job == 0 {
		return nil, err
	}
	closeJob := func() { syscall.CloseHandle(syscall.Handle(job)) }
	type basic struct {
		ProcessTime, JobTime int64
		Flags                uint32
		Min, Max             uintptr
		Active               uint32
		Affinity             uintptr
		Priority, Scheduling uint32
	}
	type counters struct{ ReadOps, WriteOps, OtherOps, ReadBytes, WriteBytes, OtherBytes uint64 }
	type limits struct {
		Basic                                          basic
		IO                                             counters
		ProcessMemory, JobMemory, PeakProcess, PeakJob uintptr
	}
	info := limits{}
	info.Basic.Flags = 0x2000
	ok, _, err := kernel.NewProc("SetInformationJobObject").Call(job, 9, uintptr(unsafe.Pointer(&info)), unsafe.Sizeof(info))
	if ok == 0 {
		closeJob()
		return nil, err
	}
	process, err := syscall.OpenProcess(0x0100|0x0001, false, uint32(cmd.Process.Pid))
	if err != nil {
		closeJob()
		return nil, err
	}
	defer syscall.CloseHandle(process)
	ok, _, err = kernel.NewProc("AssignProcessToJobObject").Call(job, uintptr(process))
	if ok == 0 {
		closeJob()
		return nil, fmt.Errorf("attach child to Job Object: %w", err)
	}
	return closeJob, nil
}
