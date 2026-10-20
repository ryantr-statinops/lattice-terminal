package fileutil

import (
	"errors"
	"os"
	"time"
)

// Rename retries transient Windows sharing/antivirus permission failures.
// It never removes the destination to emulate replacement.
func Rename(from, to string) error {
	var err error
	for attempt := 0; attempt < 8; attempt++ {
		err = os.Rename(from, to)
		if err == nil || !errors.Is(err, os.ErrPermission) {
			return err
		}
		time.Sleep(time.Duration(attempt+1) * 20 * time.Millisecond)
	}
	return err
}
