package store

import (
	"testing"
	"time"
)

func TestPaperReservationFillIdempotencyAndWeightedCost(t *testing.T) {
	s, err := Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	fund, _ := s.CreateFund("A", "paper", "1000", "fund")
	allocation, _ := s.Allocate(fund, "Manual", "manual", "1000", "alloc")
	at := time.Date(2026, 10, 1, 2, 0, 0, 0, time.UTC)
	order := PaperOrder{ID: "order", AllocationID: allocation, InstrumentID: "SYN", Side: "buy", Price: "100", Quantity: "5", ReserveRate: "0", Created: at.Format(time.RFC3339)}
	if err = s.PlacePaper(order, "order", ""); err != nil {
		t.Fatal(err)
	}
	a, _ := s.Allocation(allocation)
	if a.Cash != "500" || a.Reserved != "500" {
		t.Fatal(a)
	}
	fill := PaperFill{OrderID: "order", InstrumentID: "SYN", Side: "buy", Quantity: "2", Price: "90", Fee: "0", Tax: "0", EventID: "quote", EventTime: at.Add(time.Second).Format(time.RFC3339), SettlementDate: "2026-10-01", Simulated: true}
	if err = s.FillPaper(fill, "fill"); err != nil {
		t.Fatal(err)
	}
	if err = s.FillPaper(fill, "fill"); err != nil {
		t.Fatal(err)
	}
	a, _ = s.Allocation(allocation)
	if a.Cash != "520" || a.Reserved != "300" {
		t.Fatal(a)
	}
	positions, _ := s.Positions()
	if positions[0].Quantity != "2" || positions[0].AverageCost != "90" {
		t.Fatal(positions)
	}
	if err = s.CancelPaper("order", "cancel"); err != nil {
		t.Fatal(err)
	}
	a, _ = s.Allocation(allocation)
	if a.Cash != "820" || a.Reserved != "0" {
		t.Fatal(a)
	}
	if s.FillPaper(fill, "late-fill") == nil {
		t.Fatal("late fill accepted")
	}
}
