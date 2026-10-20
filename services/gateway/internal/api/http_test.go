package api

import (
	"net/http/httptest"
	"strings"
	"testing"
)

func TestRejectUnknownAndTrailingJSON(t *testing.T) {
	for _, body := range []string{`{"value":"a"} {"value":"b"}`, `{"unknown":1}`, `null {}`} {
		r := httptest.NewRequest("POST", "/", strings.NewReader(body))
		w := httptest.NewRecorder()
		var v struct {
			Value string `json:"value"`
		}
		if Read(w, r, &v) || w.Code != 400 {
			t.Fatal("invalid JSON accepted", body)
		}
	}
}
