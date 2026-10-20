package fileutil

import (
	"io/fs"
	"regexp"
	"strings"
)

var deviceName = regexp.MustCompile(`^(CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])$`)

// SafeRelative rejects NTFS aliases/devices as well as traversal and streams.
func SafeRelative(name string) bool {
	if !fs.ValidPath(name) || name == "." || strings.ContainsAny(name, ":\\") {
		return false
	}
	for _, r := range name {
		if r < 32 {
			return false
		}
	}
	for _, segment := range strings.Split(name, "/") {
		stem := strings.ToUpper(strings.Split(segment, ".")[0])
		if strings.TrimRight(segment, " .") != segment || deviceName.MatchString(stem) {
			return false
		}
	}
	return true
}
