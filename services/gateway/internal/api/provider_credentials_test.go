package api

import (
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"

	"kestrel-terminal/gateway/internal/host"
)

type credentialWriterStub struct {
	provider           string
	service            string
	credential         string
	configuredProvider string
	err                error
	deleted            bool
}

func (s *credentialWriterStub) Set(provider, service string, credential []byte) error {
	s.provider, s.service, s.credential = provider, service, string(credential)
	return s.err
}

func (s *credentialWriterStub) Delete(provider, service string) error {
	s.provider, s.service, s.deleted = provider, service, true
	return s.err
}

func (s *credentialWriterStub) HasProvider(provider string) (bool, error) {
	return provider == s.configuredProvider, s.err
}

func (s *credentialWriterStub) Get(provider, service string) ([]byte, error) {
	s.provider, s.service = provider, service
	if s.credential == "" {
		return nil, os.ErrNotExist
	}
	return []byte(s.credential), s.err
}

func TestProviderListingReflectsVaultConfigurationWithoutReturningSecrets(t *testing.T) {
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/internal/v1/providers" || r.Method != http.MethodGet || r.Header.Get("Authorization") != "Bearer engine-token" {
			t.Fatalf("unexpected provider status request: %s %s", r.Method, r.URL.Path)
		}
		_, _ = w.Write([]byte(`[{"id":"ssi","configured":false,"state":"blocked"},{"id":"dnse","configured":true,"state":"unknown"}]`))
	}))
	defer engine.Close()
	credentials := &credentialWriterStub{credential: "private-secret", configuredProvider: "ssi"}
	mux := http.NewServeMux()
	(&API{Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}}, Credentials: credentials}).Routes(mux)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/api/v1/providers", nil))
	var statuses []map[string]any
	if err := json.Unmarshal(response.Body.Bytes(), &statuses); err != nil || response.Code != http.StatusOK {
		t.Fatalf("provider listing response = %d %s (%v)", response.Code, response.Body.String(), err)
	}
	if statuses[0]["configured"] != true || statuses[1]["configured"] != false {
		t.Fatalf("provider configured state did not come from the vault: %#v", statuses)
	}
	if strings.Contains(response.Body.String(), "private-secret") {
		t.Fatal("provider listing exposed credential material")
	}
}

func TestSSIPingUsesVaultCredentialWithoutReturningItToClient(t *testing.T) {
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, _ := io.ReadAll(r.Body)
		if r.URL.Path != "/internal/v1/providers/ssi/ping" || r.Method != http.MethodPost {
			t.Errorf("unexpected SSI probe request: %s %s", r.Method, r.URL.Path)
		}
		if !strings.Contains(string(body), `"consumerSecret":"private-secret"`) || !strings.Contains(string(body), `"service":"market-data"`) {
			t.Errorf("vault credential was not forwarded to the internal engine: %s", body)
		}
		_, _ = w.Write([]byte(`{"id":"ssi","state":"connected","configured":true,"latency_ms":12}`))
	}))
	defer engine.Close()
	credentials := &credentialWriterStub{credential: `{"consumerID":"private-id","consumerSecret":"private-secret"}`}
	mux := http.NewServeMux()
	(&API{Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}}, Credentials: credentials}).Routes(mux)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/api/v1/providers/ssi/ping", strings.NewReader(`{}`)))
	if response.Code != http.StatusOK || credentials.provider != "ssi" || credentials.service != "market-data" {
		t.Fatalf("SSI probe response = %d %s, vault lookup = %s/%s", response.Code, response.Body.String(), credentials.provider, credentials.service)
	}
	if strings.Contains(response.Body.String(), "private-id") || strings.Contains(response.Body.String(), "private-secret") {
		t.Fatal("SSI connection check returned credential material to the client")
	}
}

func TestSSIPingRequiresMarketDataCredential(t *testing.T) {
	engineCalled := false
	engine := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		engineCalled = true
	}))
	defer engine.Close()
	mux := http.NewServeMux()
	(&API{Engine: &Runner{Engine: &host.Engine{URL: engine.URL, Token: "engine-token"}}, Credentials: &credentialWriterStub{}}).Routes(mux)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, httptest.NewRequest(http.MethodPost, "/api/v1/providers/ssi/ping", strings.NewReader(`{}`)))
	if response.Code != http.StatusBadRequest || engineCalled || !strings.Contains(response.Body.String(), "credentials are not configured") {
		t.Fatalf("missing SSI credentials response = %d %s, engineCalled=%v", response.Code, response.Body.String(), engineCalled)
	}
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

func TestProviderCredentialWriteRejectsInvalidReference(t *testing.T) {
	writer := &credentialWriterStub{}
	mux := http.NewServeMux()
	(&API{Credentials: writer}).Routes(mux)
	request := httptest.NewRequest(http.MethodPut, "/api/v1/providers/ssi/credentials", strings.NewReader(`{"service":"market data","credential":{"secret":"private-secret"}}`))
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, request)
	if response.Code != http.StatusBadRequest || writer.provider != "" {
		t.Fatalf("invalid credential reference accepted: %d %#v", response.Code, writer)
	}
}

func TestProviderCredentialDeleteDoesNotReturnSecret(t *testing.T) {
	writer := &credentialWriterStub{}
	mux := http.NewServeMux()
	(&API{Credentials: writer}).Routes(mux)
	request := httptest.NewRequest(http.MethodDelete, "/api/v1/providers/ssi/credentials?service=market-data", nil)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, request)
	if response.Code != http.StatusNoContent || response.Body.Len() != 0 || !writer.deleted || writer.provider != "ssi" || writer.service != "market-data" {
		t.Fatalf("delete response = %d %q, writer = %#v", response.Code, response.Body.String(), writer)
	}
}

func TestProviderCredentialDeleteDistinguishesMissingRecord(t *testing.T) {
	writer := &credentialWriterStub{err: os.ErrNotExist}
	mux := http.NewServeMux()
	(&API{Credentials: writer}).Routes(mux)
	request := httptest.NewRequest(http.MethodDelete, "/api/v1/providers/ssi/credentials?service=market-data", nil)
	response := httptest.NewRecorder()
	mux.ServeHTTP(response, request)
	if response.Code != http.StatusNotFound || strings.Contains(response.Body.String(), "private-secret") {
		t.Fatalf("missing credential response = %d %s", response.Code, response.Body.String())
	}
}
