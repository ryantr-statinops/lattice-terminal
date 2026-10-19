package store

import (
	"testing"
	"time"
)

func TestManualStepIsAtomicAcrossFillsAndCursor(t *testing.T) {
	s, err := Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	fund, _ := s.CreateFund("A", "paper", "1000", "fund")
	a, _ := s.Allocate(fund, "M", "manual", "1000", "alloc")
	at := time.Date(2026, 10, 1, 2, 0, 0, 0, time.UTC)
	if err = s.AdvanceCursor(a, "tape", 1, at.Format(time.RFC3339), "SYN", "90", "100"); err != nil {
		t.Fatal(err)
	}
	s.PlacePaper(PaperOrder{ID: "order", AllocationID: a, InstrumentID: "SYN", Side: "buy", Price: "100", Quantity: "2", ReserveRate: "0", Created: at.Format(time.RFC3339)}, "order", "")
	fill := PaperFill{OrderID: "order", InstrumentID: "SYN", Side: "buy", Price: "95", Quantity: "1", Fee: "0", Tax: "0", EventID: "q2", EventTime: at.Add(time.Second).Format(time.RFC3339), SettlementDate: "2026-10-01", Simulated: true}
	bad := fill
	bad.Quantity = "5"
	if s.ManualStep(a, "tape", 1, 2, fill.EventTime, "SYN", "94", "95", []PaperFill{fill, bad}) == nil {
		t.Fatal("bad batch accepted")
	}
	allocation, _ := s.Allocation(a)
	_, seq, _ := s.PaperCursor(a)
	if allocation.Cash != "800" || seq != 1 {
		t.Fatal("partial commit")
	}
	if err = s.ManualStep(a, "tape", 1, 2, fill.EventTime, "SYN", "94", "95", []PaperFill{fill}); err != nil {
		t.Fatal(err)
	}
	allocation, _ = s.Allocation(a)
	if allocation.Cash != "805" {
		t.Fatal(allocation)
	}
}
