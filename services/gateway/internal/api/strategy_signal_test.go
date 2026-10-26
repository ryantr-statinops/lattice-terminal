package api

import (
	"encoding/json"
	"strings"
	"testing"

	"kestrel-terminal/gateway/internal/store"
)

func TestSignalOnlyStrategyRunsWithoutAllocationOrPaperLedger(t *testing.T) {
	params := json.RawMessage(`{"strategy_mode":"signal_only","paper_source":"fixture-replay","event_snapshot":"` + strings.Repeat("a", 64) + `"}`)
	run := store.Run{Kind: "strategy", Params: params}
	app := &API{}
	if err := app.prepareStrategy(&run); err != nil {
		t.Fatal(err)
	}
	if err := app.bindStrategy(run); err != nil {
		t.Fatalf("signal-only run should not bind a paper allocation: %v", err)
	}
	var prepared map[string]any
	if err := json.Unmarshal(run.Params, &prepared); err != nil {
		t.Fatal(err)
	}
	if prepared["strategy_mode"] != "signal_only" {
		t.Fatalf("strategy mode was not preserved: %#v", prepared)
	}
	if _, ok := prepared["allocation_id"]; ok {
		t.Fatalf("signal-only run retained allocation data: %#v", prepared)
	}
	if err := app.PaperEvent(run, "paper_order", json.RawMessage(`{}`)); err == nil || !strings.Contains(err.Error(), "cannot emit paper events") {
		t.Fatalf("signal-only run accepted a paper event: %v", err)
	}
	app.FinishPaper(run)
}

func TestSignalOnlyStrategyRequiresDetailedSnapshot(t *testing.T) {
	run := store.Run{Kind: "strategy", Params: json.RawMessage(`{"strategy_mode":"signal_only","paper_source":"fixture-replay","event_snapshot":"candles-only"}`)}
	if err := (&API{}).prepareStrategy(&run); err == nil || !strings.Contains(err.Error(), "valid detailed replay snapshot") {
		t.Fatalf("invalid event snapshot was accepted: %v", err)
	}
}
