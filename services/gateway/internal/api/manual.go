package api

import (
	"database/sql"
	"errors"
	"kestrel-terminal/gateway/internal/store"
	"net/http"
)

func (a *API) paperRoutes(m *http.ServeMux) {
	m.HandleFunc("GET /api/v1/allocations/{id}/paper", func(w http.ResponseWriter, r *http.Request) {
		id := r.PathValue("id")
		allocation, err := a.Store.Allocation(id)
		if err != nil {
			Fail(w, err)
			return
		}
		orders, err := a.Store.PaperOrders(id)
		if err != nil {
			Fail(w, err)
			return
		}
		snapshot, sequence, err := a.Store.PaperCursor(id)
		if err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, map[string]any{"allocation": allocation, "orders": orders, "snapshot": snapshot, "sequence": sequence, "mode": "fixture-replay; SSI live blocked"})
	})
	m.HandleFunc("POST /api/v1/allocations/{id}/paper/order", func(w http.ResponseWriter, r *http.Request) {
		a.paperMu.Lock()
		defer a.paperMu.Unlock()
		var input struct {
			Snapshot string `json:"snapshot"`
			Source   string `json:"source"`
			Side     string `json:"side"`
			Price    string `json:"limit_price"`
			Quantity string `json:"quantity"`
			Key      string `json:"request_key"`
		}
		if !Read(w, r, &input) {
			return
		}
		id := r.PathValue("id")
		allocation, err := a.Store.Allocation(id)
		if err != nil || allocation.Mode != "manual" || input.Source != "fixture-replay" {
			Fail(w, errors.New("choose a manual allocation and explicit fixture-replay; SSI live blocked"))
			return
		}
		if previous, lookup := a.Store.PaperOrderRequest(input.Key); lookup == nil {
			if previous.AllocationID != id || previous.Side != input.Side || previous.Price != input.Price || previous.Quantity != input.Quantity {
				Fail(w, errors.New("idempotency key reused for different order"))
				return
			}
			JSON(w, 201, previous)
			return
		} else if lookup != sql.ErrNoRows {
			Fail(w, lookup)
			return
		}
		snapshot, sequence, err := a.Store.PaperCursor(id)
		if err != nil || snapshot != input.Snapshot {
			Fail(w, errors.New("advance selected fixture clock first"))
			return
		}
		var order store.PaperOrder
		err = a.Engine.call(r.Context(), "POST", "/paper/prepare", map[string]any{"snapshot": snapshot, "sequence": sequence, "id": eventKey(id, "manual-order", []byte(input.Key)), "side": input.Side, "limit_price": input.Price, "quantity": input.Quantity}, &order)
		if err != nil {
			Fail(w, err)
			return
		}
		order.AllocationID = id
		if err = a.Store.PlacePaper(order, input.Key, ""); err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 201, order)
	})
	m.HandleFunc("POST /api/v1/allocations/{id}/paper/advance", func(w http.ResponseWriter, r *http.Request) {
		a.paperMu.Lock()
		defer a.paperMu.Unlock()
		var input struct {
			Snapshot string `json:"snapshot"`
			After    int64  `json:"after"`
			Source   string `json:"source"`
		}
		if !Read(w, r, &input) {
			return
		}
		if input.Source != "fixture-replay" {
			Fail(w, errors.New("SSI live transport blocked"))
			return
		}
		id := r.PathValue("id")
		allocation, err := a.Store.Allocation(id)
		if err != nil || allocation.Mode != "manual" {
			Fail(w, errors.New("manual allocation required"))
			return
		}
		snapshot, seq, err := a.Store.PaperCursor(id)
		if err != nil || seq != input.After || (snapshot != "" && snapshot != input.Snapshot) {
			Fail(w, errors.New("cursor/source mismatch; refresh state"))
			return
		}
		orders, err := a.Store.PaperOrders(id)
		if err != nil {
			Fail(w, err)
			return
		}
		var result struct {
			Event struct {
				Sequence   int64  `json:"sequence"`
				Time       string `json:"event_time"`
				Instrument string `json:"instrument_id"`
				Bid        string `json:"bid"`
				Ask        string `json:"ask"`
			} `json:"event"`
			Fills []store.PaperFill `json:"fills"`
		}
		err = a.Engine.call(r.Context(), "POST", "/paper/evaluate", map[string]any{"snapshot": input.Snapshot, "after": seq, "orders": orders}, &result)
		if err != nil {
			Fail(w, err)
			return
		}
		event := result.Event
		if err = a.Store.ManualStep(id, input.Snapshot, seq, event.Sequence, event.Time, event.Instrument, event.Bid, event.Ask, result.Fills); err != nil {
			Fail(w, err)
			return
		}
		JSON(w, 200, result)
	})
	m.HandleFunc("POST /api/v1/allocations/{id}/paper/cancel", func(w http.ResponseWriter, r *http.Request) {
		a.paperMu.Lock()
		defer a.paperMu.Unlock()
		var input struct {
			Order string `json:"order_id"`
			Key   string `json:"request_key"`
		}
		if !Read(w, r, &input) {
			return
		}
		allocation, err := a.Store.Allocation(r.PathValue("id"))
		if err != nil || allocation.Mode != "manual" {
			Fail(w, errors.New("manual allocation required"))
			return
		}
		orders, err := a.Store.PaperOrders(allocation.ID)
		if err != nil {
			Fail(w, err)
			return
		}
		for _, order := range orders {
			if order.ID == input.Order {
				if err = a.Store.CancelPaper(order.ID, input.Key); err != nil {
					Fail(w, err)
					return
				}
				w.WriteHeader(204)
				return
			}
		}
		http.NotFound(w, r)
	})
}
