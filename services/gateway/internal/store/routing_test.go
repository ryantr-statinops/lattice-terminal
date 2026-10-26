package store

import (
	"database/sql"
	"path/filepath"
	"testing"
)

func TestRoutingPolicyPersistsAcrossStoreRestart(t *testing.T) {
	root := t.TempDir()
	db, err := Open(root)
	if err != nil {
		t.Fatal(err)
	}
	initial, err := db.RoutingPolicy()
	if err != nil || initial.HistoricalProvider != "vndirect" || initial.RealtimeProvider != "fixture" || initial.FinancialsProvider != "tcbs" || !initial.FallbackEnabled || len(initial.Datasets) != 0 {
		t.Fatalf("default routing policy = %#v, %v", initial, err)
	}
	want := RoutingPolicy{HistoricalProvider: "ssi", RealtimeProvider: "dnse", FinancialsProvider: "fiingroup", FallbackEnabled: false, Datasets: map[string]string{"candles.1d:equity:HOSE": "ssi:market-data:candles.1d:equity:HOSE", "quotes.equity:equity:HOSE": "dnse:market-data:quotes:equity:HOSE"}}
	if err = db.SetRoutingPolicy(want); err != nil {
		t.Fatal(err)
	}
	if err = db.Close(); err != nil {
		t.Fatal(err)
	}
	db, err = Open(root)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	got, err := db.RoutingPolicy()
	if err != nil || got.HistoricalProvider != want.HistoricalProvider || got.RealtimeProvider != want.RealtimeProvider || got.FinancialsProvider != want.FinancialsProvider || got.FallbackEnabled != want.FallbackEnabled || got.Datasets["candles.1d:equity:HOSE"] != want.Datasets["candles.1d:equity:HOSE"] || got.Datasets["quotes.equity:equity:HOSE"] != want.Datasets["quotes.equity:equity:HOSE"] {
		t.Fatalf("restored routing policy = %#v, want %#v, err=%v", got, want, err)
	}
}

func TestOldRoutingSchemaMigratesWithoutLosingLegacySettings(t *testing.T) {
	root := t.TempDir()
	db, err := sql.Open("sqlite", filepath.Join(root, "kestrel.sqlite"))
	if err != nil {
		t.Fatal(err)
	}
	_, err = db.Exec(`CREATE TABLE provider_routing_policy(
		id INTEGER PRIMARY KEY CHECK(id=1), historical_provider TEXT NOT NULL,
		realtime_provider TEXT NOT NULL, financials_provider TEXT NOT NULL,
		fallback_enabled INTEGER NOT NULL, updated_at TEXT NOT NULL
	);
	INSERT INTO provider_routing_policy VALUES(1,'tcbs','fixture','tcbs',0,'old');`)
	if err != nil {
		db.Close()
		t.Fatal(err)
	}
	if err = db.Close(); err != nil {
		t.Fatal(err)
	}

	store, err := Open(root)
	if err != nil {
		t.Fatal(err)
	}
	defer store.Close()
	policy, err := store.RoutingPolicy()
	if err != nil || policy.HistoricalProvider != "tcbs" || policy.RealtimeProvider != "fixture" || policy.FallbackEnabled || len(policy.Datasets) != 0 {
		t.Fatalf("migrated routing policy = %#v, %v", policy, err)
	}
}
