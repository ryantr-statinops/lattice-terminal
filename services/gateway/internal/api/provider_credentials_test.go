package api

import (
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

type credentialWriterStub struct {
	provider   string
	service    string
	credential string
	err        error
}

func (s *credentialWriterStub) Set(provider, service string, credential []byte) error {
	s.provider, s.service, s.credential = provider, service, string(credential)
	return s.err
}

func TestProviderCredentialWriteIsWriteOnly(t *testing.T) {
	writer := &credentialWriterStub{}
	mux := http.NewServeMux()
	(&API{Credentials: writer}).Routes(mux)
	request := httptest.NewRequest(http.MethodPut, "/api/v1/providers/ssi/credentials", strings.NewReader(`{"service":"market-data","credential":{"consumer_id":"private-id","consumer_secret":"private-secret"}}`))
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, request)
	if response.Code != http.StatusNoContent || response.Body.Len() != 0 {
		t.Fatalf("write response = %d %q", response.Code, response.Body.String())
	}
	if response.Header().Get("Cache-Control") != "no-store" {
		t.Fatal("credential response can be cached")
	}
	if writer.provider != "ssi" || writer.service != "market-data" || !strings.Contains(writer.credential, "private-secret") {
		t.Fatalf("credential was not sent to vault: %#v", writer)
	}
}

func TestProviderCredentialWriteDoesNotEchoVaultError(t *testing.T) {
	writer := &credentialWriterStub{err: errors.New("failed to store private-secret")}
	mux := http.NewServeMux()
	(&API{Credentials: writer}).Routes(mux)
	request := httptest.NewRequest(http.MethodPut, "/api/v1/providers/ssi/credentials", strings.NewReader(`{"service":"market-data","credential":{"secret":"private-secret"}}`))
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, request)
	if response.Code != http.StatusInternalServerError || strings.Contains(response.Body.String(), "private-secret") {
		t.Fatalf("vault error leaked: %d %s", response.Code, response.Body.String())
	}
}

func TestProviderCredentialWriteRequiresVaultAndObject(t *testing.T) {
	mux := http.NewServeMux()
	(&API{}).Routes(mux)
	request := httptest.NewRequest(http.MethodPut, "/api/v1/providers/ssi/credentials", strings.NewReader(`{"service":"market-data","credential":{"secret":"private-secret"}}`))
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, request)
	if response.Code != http.StatusServiceUnavailable || strings.Contains(response.Body.String(), "private-secret") {
		t.Fatalf("uninitialized vault response = %d %s", response.Code, response.Body.String())
	}

	writer := &credentialWriterStub{}
	mux = http.NewServeMux()
	(&API{Credentials: writer}).Routes(mux)
	request = httptest.NewRequest(http.MethodPut, "/api/v1/providers/ssi/credentials", strings.NewReader(`{"service":"market-data","credential":"private-secret"}`))
	response = httptest.NewRecorder()
	mux.ServeHTTP(response, request)
	if response.Code != http.StatusBadRequest || writer.provider != "" {
		t.Fatalf("non-object credential accepted: %d %#v", response.Code, writer)
	}
}
