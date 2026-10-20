package store

import "testing"

func TestInterruptedReconcileCancelsRemainderWithoutInventingFills(t *testing.T) {
	s, e := Open(t.TempDir())
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	fund, _ := s.CreateFund("Fund", "paper", "1000", "f")
	book, _ := s.Allocate(fund, "Manual", "manual", "300", "b")
	order := PaperOrder{ID: "o", AllocationID: book, InstrumentID: "SYN01", Side: "buy", Price: "100", Quantity: "2", ReserveRate: "0", Created: "2026-10-01T02:00:00Z"}
	if e = s.PlacePaper(order, "o", ""); e != nil {
		t.Fatal(e)
	}
	s.DB.Exec("UPDATE allocations SET status='interrupted' WHERE id=?", book)
	if e = s.ReconcileInterrupted(book, "reconcile"); e != nil {
		t.Fatal(e)
	}
	a, _ := s.Allocation(book)
	if a.Cash != "300" || a.Reserved != "0" || a.Status != "stopped" {
		t.Fatal(a)
	}
	positions, _ := s.Positions()
	if len(positions) != 0 {
		t.Fatal("invented fill")
	}
	if e = s.ReconcileInterrupted(book, "reconcile"); e != nil {
		t.Fatal("retry", e)
	}
	for _, v := range []string{"1e999999", "NaN", "-1", "1.000000001"} {
		if _, e = amount(v, false); e == nil {
			t.Fatal("invalid amount", v)
		}
	}
}
