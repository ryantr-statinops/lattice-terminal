package api

import (
	"encoding/csv"
	"fmt"
	"kestrel-terminal/gateway/internal/store"
	"net/http"
)

func (a *API) portfolioRoutes(m *http.ServeMux) {
	m.HandleFunc("GET /api/v1/portfolio", func(w http.ResponseWriter, r *http.Request) {
		value, err := a.Store.Portfolio()
		if err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, value)
	})
	m.HandleFunc("POST /api/v1/portfolio/import/preview", func(w http.ResponseWriter, r *http.Request) {
		var v struct {
			Fund string `json:"fund_id"`
			CSV  string `json:"csv"`
		}
		if !Read(w, r, &v) {
			return
		}
		JSON(w, 200, store.PreviewCSV(v.Fund, v.CSV))
	})
	m.HandleFunc("POST /api/v1/portfolio/import/apply", func(w http.ResponseWriter, r *http.Request) {
		var v struct {
			Fund string `json:"fund_id"`
			CSV  string `json:"csv"`
			Hash string `json:"preview_hash"`
		}
		if !Read(w, r, &v) {
			return
		}
		preview := store.PreviewCSV(v.Fund, v.CSV)
		if preview.Hash != v.Hash || len(preview.Errors) > 0 {
			JSON(w, 400, map[string]any{"error": "preview changed or contains invalid rows", "details": preview.Errors})
			return
		}
		if err := a.Store.RecordTrades(v.Fund, preview.Rows); err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, map[string]int{"validated_rows": len(preview.Rows)})
	})
	m.HandleFunc("POST /api/v1/portfolio/trade", func(w http.ResponseWriter, r *http.Request) {
		var v struct {
			Fund  string              `json:"fund_id"`
			Trade store.RecordedTrade `json:"trade"`
		}
		if !Read(w, r, &v) {
			return
		}
		if err := a.Store.RecordTrades(v.Fund, []store.RecordedTrade{v.Trade}); err != nil {
			Fail(w, err)
			return
		}
		w.WriteHeader(201)
	})
	m.HandleFunc("GET /api/v1/portfolio/export", func(w http.ResponseWriter, r *http.Request) {
		trades, err := a.Store.RecordedTrades(r.URL.Query().Get("fund_id"))
		if err != nil {
			Fail(w, err)
			return
		}
		w.Header().Set("Content-Type", "text/csv; charset=utf-8")
		w.Header().Set("Content-Disposition", "attachment; filename=kestrel-recorded-trades.csv")
		writer := csv.NewWriter(w)
		_ = writer.Write(store.TradeColumns)
		for _, v := range trades {
			_ = writer.Write([]string{v.ID, v.Time, v.Instrument, v.Side, v.Quantity, v.Price, v.Fee, v.Tax, fmt.Sprint(v.Settled)})
		}
		writer.Flush()
	})
}
