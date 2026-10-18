package marketdata

import (
	"strings"
	"testing"
	"time"
)

const testStartMS int64 = 1735688700000

func testCandle(openMS int64, closePrice string) Candle {
	duration := Interval15m.Duration().Milliseconds()
	c := Candle{
		Venue: VenueBinance, MarketType: MarketSpot, NativeSymbol: "BTCUSDT", Interval: Interval15m,
		OpenTimeMS: openMS, CloseTimeMS: openMS + duration - 1, IsClosed: true,
		Open: "10", High: "12", Low: "9", Close: closePrice, BaseVolume: "1.25", QuoteVolume: "12.5", TradeCount: 2,
		SourceID: "fixture-only", SourceObjectID: "synthetic", SourceTimestampUnit: TimestampMilliseconds,
		SourceOpenTimestamp: openMS, SourceCloseTimestamp: openMS + duration - 1,
		AvailableAt: time.Date(2025, 1, 2, 0, 0, 0, 0, time.UTC),
	}
	c.RevisionID = revisionID(c)
	return c
}

func TestReconcileSortsDeduplicatesAndReportsGaps(t *testing.T) {
	first := testCandle(testStartMS, "11")
	duplicate := first
	duplicate.SourceObjectID = "second-synthetic-object"
	last := testCandle(testStartMS+2*Interval15m.Duration().Milliseconds(), "11")
	result, err := Reconcile([]Candle{last, first, duplicate}, "BTCUSDT", Interval15m, testStartMS, testStartMS+3*Interval15m.Duration().Milliseconds())
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Candles) != 2 || result.Candles[0].OpenTimeMS != testStartMS || result.Report.DuplicateRows != 1 {
		t.Fatalf("unexpected reconcile result: %+v", result)
	}
	if len(result.Report.Gaps) != 1 || result.Report.Gaps[0].MissingBars != 1 || result.Report.Gaps[0].FromOpenTimeMS != testStartMS+Interval15m.Duration().Milliseconds() {
		t.Fatalf("missing range was not reported exactly: %+v", result.Report.Gaps)
	}
	if !result.Report.QualityPassed {
		t.Fatal("a coverage gap alone should be reported without failing schema/conflict quality")
	}
}

func TestReconcilePreservesAndBlocksConflictingRevisions(t *testing.T) {
	first := testCandle(testStartMS, "11")
	second := testCandle(testStartMS, "11.5")
	second.SourceID = "rest-fixture"
	second.SourceObjectID = "rest-synthetic-object"
	second.RevisionID = revisionID(second)
	result, err := Reconcile([]Candle{first, second}, "BTCUSDT", Interval15m, testStartMS, testStartMS+Interval15m.Duration().Milliseconds())
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Conflicts) != 1 || len(result.Candles) != 0 || result.Report.RevisionRows != 1 || result.Report.QualityPassed {
		t.Fatalf("conflict should block publication: %+v", result)
	}
}

func TestReconcileRejectsOpenCandlesFromServingRows(t *testing.T) {
	candle := testCandle(testStartMS, "11")
	candle.IsClosed = false
	result, err := Reconcile([]Candle{candle}, "BTCUSDT", Interval15m, testStartMS, testStartMS+Interval15m.Duration().Milliseconds())
	if err != nil {
		t.Fatal(err)
	}
	if len(result.Candles) != 0 || result.Report.RejectedRows != 1 || len(result.Report.Gaps) != 1 {
		t.Fatalf("open bar must be excluded and shown as a coverage gap: %+v", result)
	}
}

func TestParserRejectsBadOHLCAndNegativeVolume(t *testing.T) {
	for _, row := range []string{
		"1735688700000,10,8,9,11,1,1735689599999,12,2,1,5,0\n",
		"1735688700000,10,12,9,11,-1,1735689599999,12,2,1,5,0\n",
	} {
		if _, err := ParseArchiveCSV(strings.NewReader(row), parserConfig(TimestampMilliseconds)); err == nil {
			t.Errorf("accepted invalid OHLCV row %q", row)
		}
	}
}

func TestReconcileRejectsMisalignedRangeAndWrongInterval(t *testing.T) {
	if _, err := Reconcile(nil, "BTCUSDT", Interval15m, testStartMS+1, testStartMS+Interval15m.Duration().Milliseconds()); err == nil {
		t.Fatal("accepted unaligned start range")
	}
	candle := testCandle(testStartMS, "11")
	if _, err := Reconcile([]Candle{candle}, "ETHUSDT", Interval15m, testStartMS, testStartMS+Interval15m.Duration().Milliseconds()); err == nil {
		t.Fatal("accepted candle for another symbol")
	}
}
