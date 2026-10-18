package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"strings"
	"time"

	"researchterminal/ingestion/internal/marketdata"
)

func run(args []string, output io.Writer) error {
	flags := flag.NewFlagSet("marketdata", flag.ContinueOnError)
	flags.SetOutput(output)
	symbol := flags.String("symbol", "", "Binance Spot symbol: BTCUSDT or ETHUSDT")
	intervalText := flags.String("interval", "", "Candle interval: 15m, 1h, or 1d")
	startText := flags.String("start", "", "Inclusive UTC RFC3339 range start")
	endText := flags.String("end", "", "Exclusive UTC RFC3339 range end")
	archiveInput := flags.String("archive-input", "", "Local synthetic Binance-style archive CSV or ZIP")
	archiveChecksum := flags.String("archive-checksum", "", "Local SHA-256 sidecar for ZIP input; defaults to <archive-input>.CHECKSUM")
	archiveUnitText := flags.String("archive-timestamp-unit", "", "Explicit archive timestamp unit: millisecond or microsecond")
	restInput := flags.String("rest-input", "", "Optional local synthetic REST kline JSON fixture")
	outputDir := flags.String("output", "../../.cache/market-snapshots", "Local snapshot output directory")
	if err := flags.Parse(args); err != nil {
		if errors.Is(err, flag.ErrHelp) { return nil }
		return err
	}
	if flags.NArg() != 0 {
		return errors.New("unexpected positional arguments")
	}
	if *symbol == "" || *intervalText == "" || *startText == "" || *endText == "" || *archiveInput == "" || *archiveUnitText == "" {
		return errors.New("symbol, interval, start, end, archive-input, and archive-timestamp-unit are required")
	}
	interval := marketdata.Interval(*intervalText)
	if !interval.Valid() {
		return fmt.Errorf("unsupported interval %q", *intervalText)
	}
	unit := marketdata.TimestampUnit(*archiveUnitText)
	if unit != marketdata.TimestampMilliseconds && unit != marketdata.TimestampMicroseconds {
		return fmt.Errorf("unsupported archive timestamp unit %q", *archiveUnitText)
	}
	start, err := parseUTCMillis(*startText)
	if err != nil { return fmt.Errorf("invalid start: %w", err) }
	end, err := parseUTCMillis(*endText)
	if err != nil { return fmt.Errorf("invalid end: %w", err) }
	if end <= start { return errors.New("end must be later than start") }

	now := time.Now().UTC()
	baseConfig := marketdata.ParseConfig{
		Symbol: *symbol, Interval: interval, SourceID: marketdata.SourceFixture,
		RetrievedAt: now, Now: now,
	}
	archiveConfig := baseConfig
	archiveConfig.TimestampUnit = unit
	archiveCandles, archiveObject, err := marketdata.LoadArchiveFile(*archiveInput, *archiveChecksum, archiveConfig)
	if err != nil { return err }
	candles := append([]marketdata.Candle(nil), archiveCandles...)
	inputs := []marketdata.InputObject{archiveObject}
	if *restInput != "" {
		restConfig := baseConfig
		restConfig.TimestampUnit = marketdata.TimestampMilliseconds
		restCandles, restObject, err := marketdata.LoadRESTFile(*restInput, restConfig)
		if err != nil { return err }
		candles = append(candles, restCandles...)
		inputs = append(inputs, restObject)
	}
	result, err := marketdata.Reconcile(candles, *symbol, interval, start, end)
	if err != nil { return err }
	quality := marketdata.QualityArtifact{Report: result.Report, Conflicts: result.Conflicts}
	if err := json.NewEncoder(output).Encode(quality); err != nil { return err }
	if !result.Report.QualityPassed {
		return errors.New("snapshot blocked: unresolved candle revision conflict")
	}
	path, manifest, err := marketdata.PublishSnapshot(*outputDir, result.Candles, inputs, result, *symbol, interval, start, end, now)
	if err != nil { return err }
	_, err = fmt.Fprintf(output, "snapshot=%s rows=%d rights_eligible=%t\n", path, manifest.RowCount, manifest.RightsEligible)
	return err
}

func parseUTCMillis(value string) (int64, error) {
	parsed, err := time.Parse(time.RFC3339Nano, value)
	if err != nil { return 0, err }
	_, offset := parsed.Zone()
	if offset != 0 || parsed.Nanosecond()%int(time.Millisecond) != 0 || !strings.HasSuffix(value, "Z") {
		return 0, errors.New("timestamp must be UTC (Z) with millisecond precision")
	}
	return parsed.UTC().UnixMilli(), nil
}

func main() {
	if err := run(os.Args[1:], os.Stdout); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
