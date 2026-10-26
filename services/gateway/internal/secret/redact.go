package secret

import (
	"errors"
	"sort"
	"strings"
)

// redactCredentialError removes credential values before an error crosses into
// command output, API responses, or logs. Backend errors remain non-nil.
func redactCredentialError(err error, values ...string) error {
	if err == nil {
		return nil
	}
	secrets := make([]string, 0, len(values))
	for _, value := range values {
		if value == "" {
			continue
		}
		secrets = append(secrets, value)
	}
	sort.Slice(secrets, func(i, j int) bool { return len(secrets[i]) > len(secrets[j]) })
	message := err.Error()
	for _, value := range secrets {
		message = strings.ReplaceAll(message, value, "[redacted]")
	}
	return errors.New(message)
}
