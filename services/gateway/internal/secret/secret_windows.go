//go:build windows

package secret

import (
	"encoding/json"
	"errors"
	"syscall"
	"unsafe"
)

const target = "KestrelTerminal/SSI-FC-DATA"

type Credential struct {
	ConsumerID     string `json:"consumer_id"`
	ConsumerSecret string `json:"consumer_secret"`
}
type native struct {
	Flags, Type     uint32
	Target, Comment *uint16
	Written         syscall.Filetime
	Size            uint32
	Blob            *byte
	Persist, Count  uint32
	Attributes      uintptr
	Alias, User     *uint16
}

var api = syscall.NewLazyDLL("advapi32.dll")

func Set(v Credential) error {
	if v.ConsumerID == "" || v.ConsumerSecret == "" {
		return errors.New("both credential fields are required")
	}
	b, _ := json.Marshal(v)
	if len(b) > 2500 {
		return errors.New("credential too long")
	}
	name, _ := syscall.UTF16PtrFromString(target)
	user, _ := syscall.UTF16PtrFromString("Kestrel Terminal")
	c := native{Type: 1, Target: name, Size: uint32(len(b)), Blob: &b[0], Persist: 2, User: user}
	ok, _, err := api.NewProc("CredWriteW").Call(uintptr(unsafe.Pointer(&c)), 0)
	if ok == 0 {
		return err
	}
	return nil
}
func Get() (Credential, error) {
	var result Credential
	name, _ := syscall.UTF16PtrFromString(target)
	var p *native
	ok, _, err := api.NewProc("CredReadW").Call(uintptr(unsafe.Pointer(name)), 1, 0, uintptr(unsafe.Pointer(&p)))
	if ok == 0 {
		return result, err
	}
	defer api.NewProc("CredFree").Call(uintptr(unsafe.Pointer(p)))
	if p.Size > 2500 {
		return result, errors.New("invalid credential blob")
	}
	err = json.Unmarshal(unsafe.Slice(p.Blob, int(p.Size)), &result)
	return result, err
}
func Delete() error {
	name, _ := syscall.UTF16PtrFromString(target)
	ok, _, err := api.NewProc("CredDeleteW").Call(uintptr(unsafe.Pointer(name)), 1, 0)
	if ok == 0 {
		return err
	}
	return nil
}
