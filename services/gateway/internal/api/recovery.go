package api

import "net/http"

func (a *API) recoveryRoutes(m *http.ServeMux) {
	m.HandleFunc("POST /api/v1/allocations/{id}/reconcile", func(w http.ResponseWriter, r *http.Request) {
		var input struct {
			Acknowledge bool   `json:"acknowledge_no_missing_fills_inferred"`
			Key         string `json:"request_key"`
		}
		if !Read(w, r, &input) {
			return
		}
		if !input.Acknowledge {
			JSON(w, 400, map[string]string{"error": "acknowledgement required: only cancel open remainder; no missing fills inferred"})
			return
		}
		a.paperMu.Lock()
		defer a.paperMu.Unlock()
		if err := a.Store.ReconcileInterrupted(r.PathValue("id"), input.Key); err != nil {
			Fail(w, err)
			return
		}
		w.WriteHeader(204)
	})
}
