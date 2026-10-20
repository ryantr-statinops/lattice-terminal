package api

import (
	"encoding/json"
	"net/http"
)

func (a *API) reportRoutes(m *http.ServeMux) {
	m.HandleFunc("GET /api/v1/runs/{id}/report", func(w http.ResponseWriter, r *http.Request) {
		run, err := a.Store.Run(r.PathValue("id"))
		if err != nil || run.Kind != "backtest" || run.Status != "completed" {
			JSON(w, 409, map[string]string{"error": "completed Backtest run required"})
			return
		}
		var raw string
		if err = a.Store.DB.QueryRow("SELECT payload FROM run_events WHERE run_id=? AND type='backtest_report' ORDER BY seq DESC LIMIT 1", run.ID).Scan(&raw); err != nil {
			JSON(w, 404, map[string]string{"error": "backtest report unavailable"})
			return
		}
		JSON(w, 200, map[string]any{"run": run, "report": json.RawMessage(raw)})
	})
}
