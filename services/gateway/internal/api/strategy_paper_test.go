package api

import (
	"encoding/json"
	"testing"

	"kestrel-terminal/gateway/internal/store"
)

func TestStrategyPaperStepEventAdvancesItsBoundAllocation(t *testing.T) {
	db, err := store.Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	fund, err := db.CreateFund("Strategy event", "paper", "1000", "strategy-event-fund")
	if err != nil {
		t.Fatal(err)
	}
	allocation, err := db.Allocate(fund, "Strategy", "strategy", "1000", "strategy-event-allocation")
	if err != nil {
		t.Fatal(err)
	}
	if err = db.BindController(allocation, "strategy-event-run"); err != nil {
		t.Fatal(err)
	}
	params, _ := json.Marshal(map[string]string{"strategy_mode": "paper", "paper_source": "fixture-replay", "allocation_id": allocation, "event_snapshot": "snapshot"})
	run := store.Run{ID: "strategy-event-run", Kind: "strategy", Params: params}
	payload, _ := json.Marshal(map[string]any{
		"allocation_id": allocation, "snapshot_id": "snapshot", "after_sequence": 0,
		"sequence": 1, "event_time": "2026-10-01T02:00:00Z", "instrument_id": "SYN",
		"bid": "90", "ask": "91", "mutations": []store.StrategyPaperMutation{},
	})
	app := &API{Store: db}
	if err = app.PaperEvent(run, "paper_step", payload); err != nil {
		t.Fatal(err)
	}
	if err = app.PaperEvent(run, "paper_step", payload); err != nil {
		t.Fatalf("duplicate engine event should be idempotent: %v", err)
	}
	snapshot, sequence, err := db.PaperCursor(allocation)
	if err != nil || snapshot != "snapshot" || sequence != 1 {
		t.Fatalf("paper step cursor mismatch: %q %d %v", snapshot, sequence, err)
	}
}
