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

func TestPaperCashSettlesOnDueDateAndCannotBeSpentEarly(t *testing.T) {
	s, err := Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	fund, _ := s.CreateFund("Cash settlement", "paper", "1000", "cash-settlement-fund")
	allocation, _ := s.Allocate(fund, "Manual", "manual", "1000", "cash-settlement-allocation")
	trade := time.Date(2026, 10, 1, 2, 0, 0, 0, time.UTC)
	buy := PaperOrder{ID: "cash-seed-buy", AllocationID: allocation, InstrumentID: "HOSE:REGULAR:equity:SYN", Side: "buy", Price: "100", Quantity: "5", ReserveRate: "0", Created: trade.Format(time.RFC3339)}
	if err = s.PlacePaper(buy, "cash-seed-order", ""); err != nil {
		t.Fatal(err)
	}
	buyFill := PaperFill{OrderID: buy.ID, InstrumentID: buy.InstrumentID, Side: "buy", Quantity: "5", Price: "90", Fee: "0", Tax: "0", EventID: "cash-seed-event", EventTime: trade.Add(time.Second).Format(time.RFC3339), SettlementDate: "2026-10-01", Simulated: true}
	if err = s.FillPaper(buyFill, "cash-seed-fill"); err != nil {
		t.Fatal(err)
	}
	sell := PaperOrder{ID: "cash-delayed-sell", AllocationID: allocation, InstrumentID: buy.InstrumentID, Side: "sell", Price: "100", Quantity: "2", ReserveRate: "0", Created: trade.Add(time.Minute).Format(time.RFC3339)}
	if err = s.PlacePaper(sell, "cash-delayed-sell-order", ""); err != nil {
		t.Fatal(err)
	}
	sellFill := PaperFill{OrderID: sell.ID, InstrumentID: buy.InstrumentID, Side: "sell", Quantity: "2", Price: "110", Fee: "0", Tax: "0", EventID: "cash-delayed-sell-event", EventTime: trade.Add(2 * time.Minute).Format(time.RFC3339), SettlementDate: "2026-10-02", Simulated: true}
	if err = s.FillPaper(sellFill, "cash-delayed-sell-fill"); err != nil {
		t.Fatal(err)
	}
	a, err := s.Allocation(allocation)
	if err != nil || a.Cash != "550" || a.Unsettled != "220" {
		t.Fatalf("sale proceeds should remain unsettled: %#v, %v", a, err)
	}
	early := PaperOrder{ID: "cash-too-early", AllocationID: allocation, InstrumentID: buy.InstrumentID, Side: "buy", Price: "100", Quantity: "7", ReserveRate: "0", Created: trade.Add(3 * time.Minute).Format(time.RFC3339)}
	if err = s.PlacePaper(early, "cash-too-early-order", ""); err == nil {
		t.Fatal("unsettled sale proceeds were available for a new order")
	}
	if err = s.AdvanceCursor(allocation, "settlement-tape", 1, trade.Add(24*time.Hour).Format(time.RFC3339), buy.InstrumentID, "109", "110"); err != nil {
		t.Fatal(err)
	}
	a, err = s.Allocation(allocation)
	if err != nil || a.Cash != "770" || a.Unsettled != "0" {
		t.Fatalf("paper event clock should settle due proceeds: %#v, %v", a, err)
	}
	due := PaperOrder{ID: "cash-after-due", AllocationID: allocation, InstrumentID: buy.InstrumentID, Side: "buy", Price: "100", Quantity: "7", ReserveRate: "0", Created: trade.Add(24 * time.Hour).Format(time.RFC3339)}
	if err = s.PlacePaper(due, "cash-after-due-order", ""); err != nil {
		t.Fatal(err)
	}
	a, err = s.Allocation(allocation)
	if err != nil || a.Cash != "70" || a.Unsettled != "0" {
		t.Fatalf("due sale proceeds should become spendable cash: %#v, %v", a, err)
	}
}

func TestPaperPurchasePayableReducesCashAvailableUntilSettlement(t *testing.T) {
	s, err := Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	fund, _ := s.CreateFund("Purchase payable", "paper", "1000", "purchase-payable-fund")
	allocation, _ := s.Allocate(fund, "Manual", "manual", "1000", "purchase-payable-allocation")
	trade := time.Date(2026, 10, 1, 2, 0, 0, 0, time.UTC)
	order := PaperOrder{ID: "deferred-buy", AllocationID: allocation, InstrumentID: "HOSE:REGULAR:equity:SYN", Side: "buy", Price: "100", Quantity: "5", ReserveRate: "0", Created: trade.Format(time.RFC3339)}
	if err = s.PlacePaper(order, "deferred-buy-order", ""); err != nil {
		t.Fatal(err)
	}
	fill := PaperFill{OrderID: order.ID, InstrumentID: order.InstrumentID, Side: "buy", Quantity: "2", Price: "90", Fee: "0", Tax: "0", EventID: "deferred-buy-event", EventTime: trade.Add(time.Second).Format(time.RFC3339), SettlementDate: "2026-10-02", Simulated: true}
	if err = s.FillPaper(fill, "deferred-buy-fill"); err != nil {
		t.Fatal(err)
	}
	a, err := s.Allocation(allocation)
	if err != nil || a.Cash != "700" || a.Reserved != "300" || a.Unsettled != "-180" {
		t.Fatalf("purchase payable should remain unsettled: %#v, %v", a, err)
	}
	tooLarge := PaperOrder{ID: "too-large-before-due", AllocationID: allocation, InstrumentID: order.InstrumentID, Side: "buy", Price: "530", Quantity: "1", ReserveRate: "0", Created: trade.Add(2 * time.Second).Format(time.RFC3339)}
	if err = s.PlacePaper(tooLarge, "too-large-before-due-order", ""); err == nil {
		t.Fatal("pending purchase payable was spent twice")
	}
	if err = s.Release(allocation, "530", "release-before-due"); err == nil {
		t.Fatal("pending purchase payable was released from the allocation")
	}
	afterDue := PaperOrder{ID: "after-purchase-settles", AllocationID: allocation, InstrumentID: order.InstrumentID, Side: "buy", Price: "520", Quantity: "1", ReserveRate: "0", Created: trade.Add(24 * time.Hour).Format(time.RFC3339)}
	if err = s.PlacePaper(afterDue, "after-purchase-settles-order", ""); err != nil {
		t.Fatal(err)
	}
	a, err = s.Allocation(allocation)
	if err != nil || a.Cash != "0" || a.Unsettled != "0" {
		t.Fatalf("purchase payable should settle before new cash is reserved: %#v, %v", a, err)
	}
}
