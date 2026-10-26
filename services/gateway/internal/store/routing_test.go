package store

import "testing"

func TestRoutingPolicyPersistsAcrossStoreRestart(t *testing.T) {
	root := t.TempDir()
	db, err := Open(root)
	if err != nil {
		t.Fatal(err)
	}
	initial, err := db.RoutingPolicy()
	if err != nil || initial != (RoutingPolicy{HistoricalProvider: "vndirect", RealtimeProvider: "fixture", FinancialsProvider: "tcbs", FallbackEnabled: true}) {
		t.Fatalf("default routing policy = %#v, %v", initial, err)
	}
	want := RoutingPolicy{HistoricalProvider: "ssi", RealtimeProvider: "dnse", FinancialsProvider: "fiingroup", FallbackEnabled: false}
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
	if err != nil || got != want {
		t.Fatalf("restored routing policy = %#v, want %#v, err=%v", got, want, err)
	}
}
