package store

import (
	"testing"
)

func TestCSVAtomicImportAndMissingPriceNotZero(t *testing.T) {
	s, err := Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	fund, _ := s.CreateFund("Tracking", "tracking", "1000", "fund")
	header := "trade_id,event_time,instrument_id,side,quantity,price,fee,tax,settled\n"
	valid := header + "a,2026-10-01T02:00:00Z,HOSE:REGULAR:equity:SYN01,buy,2,100,0,0,true\n"
	preview := PreviewCSV(fund, valid)
	if len(preview.Errors) != 0 {
		t.Fatal(preview.Errors)
	}
	bad := append(preview.Rows, RecordedTrade{ID: "bad", Time: "2026-10-01T02:01:00Z", Instrument: "HOSE:REGULAR:equity:SYN01", Side: "sell", Quantity: "3", Price: "100", Fee: "0", Tax: "0", Settled: true})
	if s.RecordTrades(fund, bad) == nil {
		t.Fatal("oversell accepted")
	}
	funds, _ := s.Funds()
	if funds[0].Cash != "1000" {
		t.Fatal("partial CSV write")
	}
	if err = s.RecordTrades(fund, preview.Rows); err != nil {
		t.Fatal(err)
	}
	if err = s.RecordTrades(fund, preview.Rows); err != nil {
		t.Fatal(err)
	}
	funds, _ = s.Funds()
	if funds[0].Cash != "800" {
		t.Fatal("duplicate import")
	}
	summary, _ := s.Portfolio()
	values := summary["funds"].([]FundValue)
	if values[0].NAV != nil || len(values[0].Missing) != 1 {
		t.Fatal("unknown price became zero NAV")
	}
}

func TestRecordedChronologyAndCSVIdentifiers(t *testing.T) {
	s, err := Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	fund, _ := s.CreateFund("Tracking", "tracking", "1000", "fund")
	v := RecordedTrade{ID: "new", Time: "2026-10-02T02:00:00Z", Instrument: "HOSE:REGULAR:equity:SYN01", Side: "buy", Quantity: "1", Price: "100", Fee: "0", Tax: "0", Settled: true}
	if err = s.RecordTrades(fund, []RecordedTrade{v}); err != nil {
		t.Fatal(err)
	}
	old := v
	old.ID = "old"
	old.Time = "2026-10-01T02:00:00Z"
	if s.RecordTrades(fund, []RecordedTrade{old}) == nil {
		t.Fatal("backdated trade accepted")
	}
	if err = s.RecordTrades(fund, []RecordedTrade{v}); err != nil {
		t.Fatal("retry rejected", err)
	}
	for _, id := range []string{"=SUM(1)", "+cmd", "@formula", "\tformula", "-1"} {
		v.ID = id
		if validateRecorded(v) == nil {
			t.Fatal("unsafe CSV identifier", id)
		}
	}
}

func TestPortfolioDoesNotDoubleCountAllocatedCash(t *testing.T) {
	s, err := Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	fund, _ := s.CreateFund("Paper", "paper", "1000", "fund")
	if _, err = s.Allocate(fund, "Manual", "manual", "300", "allocation"); err != nil {
		t.Fatal(err)
	}
	if err = s.CashFlow(fund, "deposit", "200", "deposit"); err != nil {
		t.Fatal(err)
	}
	result, err := s.Portfolio()
	if err != nil {
		t.Fatal(err)
	}
	v := result["funds"].([]FundValue)[0]
	if v.NAV == nil || *v.NAV != "1200" || v.PnL == nil || *v.PnL != "0" {
		t.Fatalf("double counted capital: %+v", v)
	}
}
