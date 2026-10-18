package main

import (
	"bytes"
	"path/filepath"
	"strings"
	"testing"
)

func TestRunCreatesSyntheticLocalSnapshot(t *testing.T) {
	outputDir := filepath.Join(t.TempDir(), "market-snapshots")
	var output bytes.Buffer
	err := run([]string{
		"--symbol", "BTCUSDT", "--interval", "15m",
		"--start", "2024-12-31T23:45:00Z", "--end", "2025-01-01T00:00:00Z",
		"--archive-input", "../../internal/marketdata/testdata/synthetic-archive-2024.csv",
		"--archive-timestamp-unit", "millisecond", "--output", outputDir,
	}, &output)
	if err != nil { t.Fatal(err) }
	if !strings.Contains(output.String(), `"quality_passed":true`) || !strings.Contains(output.String(), "rights_eligible=false") {
		t.Fatalf("unexpected CLI output: %s", output.String())
	}
}

func TestRunRequiresExplicitRangeAndTimestampUnit(t *testing.T) {
	for _, args := range [][]string{
		{"--symbol", "BTCUSDT"},
		{"--symbol", "BTCUSDT", "--interval", "15m", "--start", "2025-01-01T00:00:00Z", "--end", "2025-01-01T00:15:00Z", "--archive-input", "x.csv"},
	} {
		if err := run(args, &bytes.Buffer{}); err == nil { t.Errorf("accepted incomplete arguments: %v", args) }
	}
}

func TestRunHelpDoesNotFail(t *testing.T) {
	var output bytes.Buffer
	if err := run([]string{"--help"}, &output); err != nil { t.Fatal(err) }
	if !strings.Contains(output.String(), "archive-input") { t.Fatal("help output omitted local input options") }
}

func TestParseUTCMillisRejectsLocalAndSubMillisecondTimes(t *testing.T) {
	for _, value := range []string{"2025-01-01T00:00:00+07:00", "2025-01-01T00:00:00.000001Z"} {
		if _, err := parseUTCMillis(value); err == nil { t.Errorf("accepted non-canonical UTC time %q", value) }
	}
}
