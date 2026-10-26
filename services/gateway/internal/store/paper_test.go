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

func TestPaperBoughtSharesRemainUnavailableUntilSettlement(t *testing.T) {
	s, err := Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	fund, _ := s.CreateFund("Settlement", "paper", "1000", "settlement-fund")
	allocation, _ := s.Allocate(fund, "Manual", "manual", "1000", "settlement-allocation")
	trade := time.Date(2026, 10, 1, 2, 0, 0, 0, time.UTC)
	order := PaperOrder{ID: "settled-buy", AllocationID: allocation, InstrumentID: "HOSE:REGULAR:equity:SYN", Side: "buy", Price: "100", Quantity: "2", ReserveRate: "0", Created: trade.Format(time.RFC3339)}
	if err = s.PlacePaper(order, "settled-buy-order", ""); err != nil {
		t.Fatal(err)
	}
	fill := PaperFill{OrderID: order.ID, InstrumentID: order.InstrumentID, Side: "buy", Quantity: "2", Price: "90", Fee: "0", Tax: "0", EventID: "settlement-quote", EventTime: trade.Add(time.Second).Format(time.RFC3339), SettlementDate: "2026-10-02", Simulated: true}
	if err = s.FillPaper(fill, "settled-buy-fill"); err != nil {
		t.Fatal(err)
	}
	positions, err := s.Positions()
	if err != nil || len(positions) != 1 || positions[0].Quantity != "2" || positions[0].Settled != "0" {
		t.Fatalf("bought shares should remain unsettled: %#v, %v", positions, err)
	}
	sell := PaperOrder{ID: "too-early-sell", AllocationID: allocation, InstrumentID: order.InstrumentID, Side: "sell", Price: "100", Quantity: "1", ReserveRate: "0", Created: trade.Add(2 * time.Hour).Format(time.RFC3339)}
	if err = s.PlacePaper(sell, "too-early-sell-order", ""); err == nil {
		t.Fatal("unsettled shares were available for sale")
	}
	sell.ID = "settled-sell"
	sell.Created = trade.Add(24 * time.Hour).Format(time.RFC3339)
	if err = s.PlacePaper(sell, "settled-sell-order", ""); err != nil {
		t.Fatal(err)
	}
	positions, err = s.Positions()
	if err != nil || len(positions) != 1 || positions[0].Quantity != "2" || positions[0].Settled != "2" || positions[0].SellReserved != "1" {
		t.Fatalf("matured shares should become sellable: %#v, %v", positions, err)
	}
}
