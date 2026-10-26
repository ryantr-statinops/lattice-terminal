package store

import (
	"encoding/json"
	"testing"
	"time"
)

func TestStrategyPaperStepCommitsFillsAndCursorAtomically(t *testing.T) {
	s, err := Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	fund, err := s.CreateFund("Strategy step", "paper", "1000", "strategy-step-fund")
	if err != nil {
		t.Fatal(err)
	}
	allocation, err := s.Allocate(fund, "Strategy", "strategy", "1000", "strategy-step-allocation")
	if err != nil {
		t.Fatal(err)
	}
	if err = s.BindController(allocation, "run-step"); err != nil {
		t.Fatal(err)
	}
	at := time.Date(2026, 10, 1, 2, 0, 0, 0, time.UTC)
	order := PaperOrder{ID: "strategy-step-order", AllocationID: allocation, InstrumentID: "SYN", Side: "buy", Price: "100", Quantity: "2", ReserveRate: "0", Created: at.Add(-time.Second).Format(time.RFC3339)}
	if err = s.PlacePaper(order, "strategy-step-order-key", "run-step"); err != nil {
		t.Fatal(err)
	}
	fill := PaperFill{OrderID: order.ID, InstrumentID: order.InstrumentID, Side: "buy", Quantity: "1", Price: "90", Fee: "0", Tax: "0", EventID: "quote-step-1", EventTime: at.Format(time.RFC3339), SettlementDate: "2026-10-01", Simulated: true}
	rawFill, err := json.Marshal(fill)
	if err != nil {
		t.Fatal(err)
	}
	mutations := []StrategyPaperMutation{{Type: "paper_fill", Payload: rawFill}}
	badMutations := append(append([]StrategyPaperMutation{}, mutations...), StrategyPaperMutation{Type: "unsupported"})
	if err = s.ApplyStrategyStep(allocation, "run-step", "strategy-step-key", "snapshot", 0, 1, at.Format(time.RFC3339), "SYN", "89", "90", badMutations); err == nil {
		t.Fatal("invalid paper mutation committed")
	}
	a, err := s.Allocation(allocation)
	if err != nil || a.Cash != "800" || a.Reserved != "200" {
		t.Fatalf("failed step changed cash reservation: %#v, %v", a, err)
	}
	_, sequence, err := s.PaperCursor(allocation)
	if err != nil || sequence != 0 {
		t.Fatalf("failed step advanced cursor: %d, %v", sequence, err)
	}
	var stepCount int
	if err = s.DB.QueryRow("SELECT COUNT(*) FROM paper_steps WHERE allocation_id=?", allocation).Scan(&stepCount); err != nil || stepCount != 0 {
		t.Fatalf("failed step persisted its event: %d, %v", stepCount, err)
	}
	positions, err := s.Positions()
	if err != nil || len(positions) != 0 {
		t.Fatalf("failed step persisted a position: %#v, %v", positions, err)
	}
	if err = s.ApplyStrategyStep(allocation, "run-step", "strategy-step-key", "snapshot", 0, 1, at.Format(time.RFC3339), "SYN", "89", "90", mutations); err != nil {
		t.Fatal(err)
	}
	if err = s.ApplyStrategyStep(allocation, "run-step", "strategy-step-key", "snapshot", 0, 1, at.Format(time.RFC3339), "SYN", "89", "90", mutations); err != nil {
		t.Fatalf("duplicate recovery step should be idempotent: %v", err)
	}
	if err = s.ApplyStrategyStep(allocation, "run-step", "conflicting-step-key", "snapshot", 0, 1, at.Format(time.RFC3339), "SYN", "89", "90", mutations); err == nil {
		t.Fatal("different event reused an already committed market sequence")
	}
	a, err = s.Allocation(allocation)
	if err != nil || a.Cash != "810" || a.Reserved != "100" {
		t.Fatalf("step did not apply the fill exactly once: %#v, %v", a, err)
	}
	positions, err = s.Positions()
	if err != nil || len(positions) != 1 || positions[0].Quantity != "1" {
		t.Fatalf("step position is incorrect: %#v, %v", positions, err)
	}
	_, sequence, err = s.PaperCursor(allocation)
	if err != nil || sequence != 1 {
		t.Fatalf("step cursor was not committed: %d, %v", sequence, err)
	}
	if err = s.DB.QueryRow("SELECT COUNT(*) FROM paper_steps WHERE allocation_id=?", allocation).Scan(&stepCount); err != nil || stepCount != 1 {
		t.Fatalf("step event was not persisted with the cursor: %d, %v", stepCount, err)
	}
}
