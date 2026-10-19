package api

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"kestrel-terminal/gateway/internal/store"
	"strings"
)

func eventKey(run, kind string, payload json.RawMessage) string {
	sum := sha256.Sum256(append([]byte(run+kind), payload...))
	return hex.EncodeToString(sum[:])
}
func (a *API) prepareStrategy(run *store.Run) error {
	if run.Kind != "strategy" {
		return nil
	}
	var params map[string]any
	if json.Unmarshal(run.Params, &params) != nil {
		return errors.New("parameters must be an object")
	}
	if params["paper_source"] != "fixture-replay" {
		return errors.New("SSI live paper remains blocked: entitlement/feed/rules not verified; select explicitly labelled fixture replay for development")
	}
	id, ok := params["allocation_id"].(string)
	if !ok || id == "" {
		return errors.New("select a Strategy allocation from Assets")
	}
	allocation, err := a.Store.Allocation(id)
	if err != nil {
		return err
	}
	if allocation.Mode != "strategy" || allocation.Status != "stopped" || allocation.Reserved != "0" || allocation.Unsettled != "0" {
		return errors.New("allocation is not stopped/reconciled")
	}
	orders, err := a.Store.PaperOrders(id)
	if err != nil {
		return err
	}
	for _, order := range orders {
		if order.Status == "open" {
			return errors.New("allocation has open orders")
		}
	}
	positions, err := a.Store.Positions()
	if err != nil {
		return err
	}
	initial := map[string]string{}
	for _, p := range positions {
		if p.AllocationID == id {
			if p.Quantity != p.Settled || p.SellReserved != "0" {
				return errors.New("settled position reconciliation required")
			}
			initial[p.InstrumentID] = p.Quantity
		}
	}
	snapshot, after, err := a.Store.PaperCursor(id)
	if err != nil {
		return err
	}
	if snapshot != "" && params["event_snapshot"] != snapshot {
		return errors.New("cannot change event tape on an existing paper book")
	}
	params["allocation_cash"] = allocation.Cash
	params["allocation_positions"] = initial
	params["after_sequence"] = after
	run.Params, err = json.Marshal(params)
	return err
}
func (a *API) bindStrategy(run store.Run) error {
	if run.Kind != "strategy" {
		return nil
	}
	var params map[string]any
	json.Unmarshal(run.Params, &params)
	return a.Store.BindController(params["allocation_id"].(string), run.ID)
}
func (a *API) PaperEvent(run store.Run, kind string, payload json.RawMessage) error {
	if !strings.HasPrefix(kind, "paper_") {
		return nil
	}
	if run.Kind != "strategy" {
		return errors.New("research/backtest cannot mutate paper funds")
	}
	var params map[string]any
	json.Unmarshal(run.Params, &params)
	id, _ := params["allocation_id"].(string)
	allocation, err := a.Store.Allocation(id)
	if err != nil || allocation.Controller != run.ID {
		return errors.New("strategy allocation lease missing")
	}
	key := eventKey(run.ID, kind, payload)
	switch kind {
	case "paper_order":
		var order store.PaperOrder
		if err = json.Unmarshal(payload, &order); err != nil {
			return err
		}
		if order.AllocationID != id {
			return errors.New("allocation mismatch")
		}
		return a.Store.PlacePaper(order, key, run.ID)
	case "paper_fill":
		var fill store.PaperFill
		if err = json.Unmarshal(payload, &fill); err != nil {
			return err
		}
		orders, err := a.Store.PaperOrders(id)
		if err != nil {
			return err
		}
		owned := false
		for _, order := range orders {
			if order.ID == fill.OrderID {
				owned = true
			}
		}
		if !owned {
			return errors.New("fill targets another allocation")
		}
		return a.Store.FillPaper(fill, key)
	case "paper_cancel":
		var input struct {
			OrderID string `json:"order_id"`
		}
		if err = json.Unmarshal(payload, &input); err != nil {
			return err
		}
		orders, err := a.Store.PaperOrders(id)
		if err != nil {
			return err
		}
		for _, order := range orders {
			if order.ID == input.OrderID {
				return a.Store.CancelPaper(input.OrderID, key)
			}
		}
		return errors.New("cancel targets another allocation")
	case "paper_cursor":
		var input struct {
			Allocation string `json:"allocation_id"`
			Snapshot   string `json:"snapshot_id"`
			Seq        int64  `json:"sequence"`
			Time       string `json:"event_time"`
			Instrument string `json:"instrument_id"`
			Bid        string `json:"bid"`
			Ask        string `json:"ask"`
		}
		if err = json.Unmarshal(payload, &input); err != nil {
			return err
		}
		if input.Allocation != id {
			return errors.New("cursor allocation mismatch")
		}
		return a.Store.AdvanceCursor(id, input.Snapshot, input.Seq, input.Time, input.Instrument, input.Bid, input.Ask)
	case "paper_session":
		return nil
	default:
		return errors.New("unknown paper event")
	}
}
func (a *API) FinishPaper(run store.Run) {
	if run.Kind != "strategy" {
		return
	}
	var params map[string]any
	json.Unmarshal(run.Params, &params)
	id, _ := params["allocation_id"].(string)
	allocation, err := a.Store.Allocation(id)
	if err != nil || allocation.Controller != run.ID {
		return
	}
	orders, err := a.Store.PaperOrders(id)
	if err != nil {
		return
	}
	for _, order := range orders {
		if order.Status == "open" {
			payload, _ := json.Marshal(order.ID)
			_ = a.Store.CancelPaper(order.ID, eventKey(run.ID, "cleanup", payload))
		}
	}
	status := "interrupted"
	if current, err := a.Store.Run(run.ID); err == nil && current.Status == "completed" {
		status = "stopped"
	}
	_ = a.Store.EndController(id, run.ID, status)
}
