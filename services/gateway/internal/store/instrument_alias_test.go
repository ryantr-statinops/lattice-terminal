package store

import (
	"database/sql"
	"errors"
	"testing"
	"time"
)

func aliasAt(symbol string, from, to string) ProviderInstrumentAlias {
	start, _ := time.Parse(time.RFC3339Nano, from)
	alias := ProviderInstrumentAlias{
		StableInstrumentID:   "VN:HOSE:equity:ACME",
		ProviderID:           "ssi",
		ProviderInstrumentID: "instrument-42",
		NativeSymbol:         symbol,
		EffectiveFrom:        start,
	}
	if to != "" {
		end, _ := time.Parse(time.RFC3339Nano, to)
		alias.EffectiveTo = &end
	}
	return alias
}

func TestProviderInstrumentAliasesPersistAndResolveEffectiveSymbolHistory(t *testing.T) {
	root := t.TempDir()
	s, err := Open(root)
	if err != nil {
		t.Fatal(err)
	}
	old := aliasAt("OLD", "2026-01-01T00:00:00Z", "2026-06-01T00:00:00Z")
	newAlias := aliasAt("NEW", "2026-06-01T00:00:00Z", "")
	if err = s.PutProviderInstrumentAlias(old); err != nil {
		t.Fatal(err)
	}
	if err = s.PutProviderInstrumentAlias(newAlias); err != nil {
		t.Fatal(err)
	}
	// Repeating the exact row is idempotent.
	if err = s.PutProviderInstrumentAlias(newAlias); err != nil {
		t.Fatal(err)
	}
	gotOld, err := s.ResolveProviderInstrument("ssi", "instrument-42", time.Date(2026, 5, 31, 23, 59, 59, 0, time.UTC))
	if err != nil || gotOld.NativeSymbol != "OLD" {
		t.Fatalf("pre-change alias = %#v, %v", gotOld, err)
	}
	gotNew, err := s.ResolveProviderInstrument("ssi", "instrument-42", time.Date(2026, 6, 1, 0, 0, 0, 0, time.UTC))
	if err != nil || gotNew.NativeSymbol != "NEW" {
		t.Fatalf("boundary alias = %#v, %v", gotNew, err)
	}
	if err = s.Close(); err != nil {
		t.Fatal(err)
	}

	s, err = Open(root)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	items, err := s.ProviderInstrumentAliases("ssi", "instrument-42")
	if err != nil || len(items) != 2 || items[0].NativeSymbol != "OLD" || items[1].NativeSymbol != "NEW" {
		t.Fatalf("persisted aliases = %#v, %v", items, err)
	}
}

func TestProviderInstrumentAliasRejectsOverlapsAndConflictingRows(t *testing.T) {
	s, err := Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	if err = s.PutProviderInstrumentAlias(aliasAt("OLD", "2026-01-01T00:00:00Z", "2026-06-01T00:00:00Z")); err != nil {
		t.Fatal(err)
	}
	if err = s.PutProviderInstrumentAlias(aliasAt("OVERLAP", "2026-05-31T00:00:00Z", "2026-07-01T00:00:00Z")); err == nil {
		t.Fatal("overlapping alias range was accepted")
	}
	if err = s.PutProviderInstrumentAlias(aliasAt("CONFLICT", "2026-01-01T00:00:00Z", "2026-06-01T00:00:00Z")); err == nil {
		t.Fatal("conflicting alias for the same effective start was accepted")
	}
	_, err = s.ResolveProviderInstrument("ssi", "instrument-42", time.Date(2026, 6, 1, 0, 0, 0, 0, time.UTC))
	if !errors.Is(err, sql.ErrNoRows) {
		t.Fatalf("expected no mapping at the exclusive end boundary, got %v", err)
	}
}

func TestProviderInstrumentAliasRejectsInvalidEffectiveRange(t *testing.T) {
	s, err := Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	if err = s.PutProviderInstrumentAlias(aliasAt("BAD", "2026-06-01T00:00:00Z", "2026-01-01T00:00:00Z")); err == nil {
		t.Fatal("effective_to before effective_from was accepted")
	}
}

func TestProviderInstrumentAliasResolutionUsesSubsecondEffectiveBounds(t *testing.T) {
	s, err := Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	alias := aliasAt("SUB", "2026-01-01T00:00:00.5Z", "2026-01-01T00:00:00.75Z")
	alias.ProviderInstrumentID = "fractional"
	if err = s.PutProviderInstrumentAlias(alias); err != nil {
		t.Fatal(err)
	}
	for _, tc := range []struct {
		at      time.Time
		wantHit bool
	}{
		{time.Date(2026, 1, 1, 0, 0, 0, 499_000_000, time.UTC), false},
		{time.Date(2026, 1, 1, 0, 0, 0, 500_000_000, time.UTC), true},
		{time.Date(2026, 1, 1, 0, 0, 0, 750_000_000, time.UTC), false},
	} {
		_, resolveErr := s.ResolveProviderInstrument("ssi", "fractional", tc.at)
		if tc.wantHit && resolveErr != nil {
			t.Fatalf("expected alias at %s, got %v", tc.at, resolveErr)
		}
		if !tc.wantHit && !errors.Is(resolveErr, sql.ErrNoRows) {
			t.Fatalf("expected no alias at %s, got %v", tc.at, resolveErr)
		}
	}
}
