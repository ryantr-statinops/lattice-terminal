package main

import (
	"net/http/httptest"
	"testing"
)

func TestHealth(t *testing.T) {
	w := httptest.NewRecorder()
	handler().ServeHTTP(w, httptest.NewRequest("GET", "/api/v1/health", nil))
	if w.Code != 200 {
		t.Fatal(w.Code)
	}
}
