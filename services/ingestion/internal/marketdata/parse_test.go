package marketdata

import (
	"os"
	"strings"
	"testing"
	"time"
)

func parserConfig(unit TimestampUnit) ParseConfig {
	return ParseConfig{
		Symbol: "BTCUSDT", Interval: Interval15m, TimestampUnit: unit,
		SourceID: "fixture-only", SourceObjectID: "synthetic-object",
		RetrievedAt: time.Date(2025, 1, 2, 0, 0, 0, 0, time.UTC),
		Now: time.Date(2025, 1, 2, 0, 0, 0, 0, time.UTC),
	}
}

func openTestdata(t *testing.T, name string) *os.File {
	t.Helper()
	f, err := os.Open("testdata/" + name)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = f.Close() })
	return f
}

func TestParseArchiveTimestampUnitTransition(t *testing.T) {
	preTransition, err := ParseArchiveCSV(openTestdata(t, "synthetic-archive-2024.csv"), parserConfig(TimestampMilliseconds))
	if err != nil {
		t.Fatal(err)
	}
	if got, want := preTransition[0].OpenTimeMS, int64(1735688700000); got != want {
		t.Fatalf("millisecond open time = %d, want %d", got, want)
	}
	if !preTransition[0].IsClosed || preTransition[0].SourceTimestampUnit != TimestampMilliseconds {
		t.Fatal("pre-transition synthetic candle metadata is incorrect")
	}

	postTransition, err := ParseArchiveCSV(openTestdata(t, "synthetic-archive-2025.csv"), parserConfig(TimestampMicroseconds))
	if err != nil {
		t.Fatal(err)
	}
	if got, want := postTransition[0].OpenTimeMS, int64(1735689600000); got != want {
		t.Fatalf("microsecond open time = %d, want %d", got, want)
	}
	if got, want := postTransition[0].CloseTimeMS, int64(1735690499999); got != want {
		t.Fatalf("microsecond close time = %d, want %d", got, want)
	}
	if postTransition[0].SourceOpenTimestamp != 1735689600000000 {
		t.Fatal("raw source timestamp was not preserved")
	}
}

func TestParseRESTKlines(t *testing.T) {
	candles, err := ParseRESTKlines(openTestdata(t, "synthetic-rest.json"), parserConfig(TimestampMilliseconds))
	if err != nil {
		t.Fatal(err)
	}
	if len(candles) != 1 || candles[0].Open != "10.00" || candles[0].TradeCount != 42 {
		t.Fatalf("unexpected REST candle: %+v", candles)
	}
}

func TestLoadRESTFixtureVerifiesSyntheticSidecar(t *testing.T) {
	candles, input, err := LoadRESTFile("testdata/synthetic-rest.json", parserConfig(TimestampMilliseconds))
	if err != nil { t.Fatal(err) }
	if len(candles) != 1 || !input.syntheticVerified || input.SourceID != SourceFixture {
		t.Fatalf("REST loader did not preserve synthetic provenance: %+v %+v", candles, input)
	}
}

func TestMicrosecondTimestampPrecisionIsExplicit(t *testing.T) {
	candles, err := ParseArchiveCSV(openTestdata(t, "synthetic-archive-2025.csv"), parserConfig(TimestampMicroseconds))
	if err != nil { t.Fatal(err) }
	candle := candles[0]
	candle.SourceOpenTimestamp++
	if err := validateCandle(candle); err == nil { t.Fatal("accepted a microsecond open timestamp that loses precision when normalized") }
}

func TestParsersRejectMalformedRowsAndUnsupportedIdentity(t *testing.T) {
	for _, input := range []string{
		"1735689600000,10,12,9,11,25.5,1735690499999,280.5,42,15,165.7\n",
		"bad,10,12,9,11,25.5,1735690499999,280.5,42,15,165.7,0\n",
	} {
		if _, err := ParseArchiveCSV(strings.NewReader(input), parserConfig(TimestampMilliseconds)); err == nil {
			t.Errorf("accepted malformed row %q", input)
		}
	}
	if _, err := ParseArchiveCSV(strings.NewReader("1735689600000,10,12,9,11,25.5,1735690499999,280.5,42,15,165.7,0\n"), ParseConfig{
		Symbol: "BTCUSDT-PERP", Interval: Interval15m, TimestampUnit: TimestampMilliseconds,
		SourceID: "fixture-only", SourceObjectID: "synthetic-object", RetrievedAt: time.Now().UTC(), Now: time.Now().UTC(),
	}); err == nil {
		t.Fatal("accepted unsupported derivative symbol")
	}
}

func TestParserMarksOpenCandleProvisional(t *testing.T) {
	cfg := parserConfig(TimestampMilliseconds)
	cfg.Now = time.Date(2024, 12, 31, 23, 45, 0, 0, time.UTC)
	candles, err := ParseArchiveCSV(openTestdata(t, "synthetic-archive-2024.csv"), cfg)
	if err != nil {
		t.Fatal(err)
	}
	if candles[0].IsClosed {
		t.Fatal("candle whose close time is in the future was marked closed")
	}
}
