package secret

import (
	"errors"
	"strings"
	"testing"
)

func TestRedactCredentialErrorRemovesCredentialValues(t *testing.T) {
	credentialID := "consumer-private"
	credentialSecret := "consumer-private-secret"
	err := redactCredentialError(errors.New("backend rejected "+credentialID+" with "+credentialSecret), credentialID, credentialSecret)
	if err == nil || strings.Contains(err.Error(), credentialID) || strings.Contains(err.Error(), credentialSecret) {
		t.Fatalf("credential values leaked through error: %v", err)
	}
	if !strings.Contains(err.Error(), "[redacted]") {
		t.Fatalf("redaction marker missing: %v", err)
	}
}

func TestRedactCredentialErrorPreservesNil(t *testing.T) {
	if redactCredentialError(nil, "secret") != nil {
		t.Fatal("nil error became non-nil")
	}
}
