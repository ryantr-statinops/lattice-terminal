package store

import (
	"github.com/shopspring/decimal"
	"sync"
	"testing"
)

func TestAtomicConcurrentAllocationsAndIdempotency(t *testing.T) {
	s, err := Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	fund, err := s.CreateFund("Quỹ A", "paper", "100", "create")
	if err != nil {
		t.Fatal(err)
	}
	var wg sync.WaitGroup
	success := make(chan string, 2)
	for _, key := range []string{"a", "b"} {
		wg.Add(1)
		go func(k string) {
			defer wg.Done()
			id, err := s.Allocate(fund, k, "manual", "70", k)
			if err == nil {
				success <- id
			}
		}(key)
	}
	wg.Wait()
	close(success)
	if len(success) != 1 {
		t.Fatal("double allocation")
	}
	funds, _ := s.Funds()
	if funds[0].Cash != "30" {
		t.Fatal(funds)
	}
	if err = s.CashFlow(fund, "deposit", "0.1", "deposit"); err != nil {
		t.Fatal(err)
	}
	if err = s.CashFlow(fund, "deposit", "0.1", "deposit"); err != nil {
		t.Fatal(err)
	}
	funds, _ = s.Funds()
	if !decimal.RequireFromString(funds[0].Cash).Equal(decimal.RequireFromString("30.1")) {
		t.Fatal("duplicate or float drift")
	}
	if s.CashFlow(fund, "deposit", "0.2", "deposit") == nil {
		t.Fatal("key reused for different amount")
	}
}
