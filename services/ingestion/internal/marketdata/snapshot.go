package marketdata

import (
	"crypto/sha256"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

type snapshotIdentity struct {
	SchemaVersion string        `json:"schema_version"`
	AdapterVersion string      `json:"adapter_version"`
	Symbol        string        `json:"symbol"`
	Interval      Interval      `json:"interval"`
	StartMS       int64         `json:"start_ms"`
	EndMS         int64         `json:"end_ms"`
	Inputs        []inputIdentity `json:"inputs"`
}

type inputIdentity struct {
	SourceID string `json:"source_id"`
	ObjectID string `json:"object_id"`
	SHA256 string `json:"sha256"`
	TimestampUnit TimestampUnit `json:"timestamp_unit"`
}

func PublishSnapshot(outputRoot string, rows []Candle, inputs []InputObject, result ReconcileResult, symbol string, interval Interval, startMS, endMS int64, createdAt time.Time) (string, Manifest, error) {
	if strings.TrimSpace(outputRoot) == "" || createdAt.IsZero() {
		return "", Manifest{}, errors.New("output directory and creation time are required")
	}
	if symbol != "BTCUSDT" && symbol != "ETHUSDT" || !interval.Valid() || endMS <= startMS {
		return "", Manifest{}, errors.New("invalid snapshot identity")
	}
	if len(rows) == 0 || !result.Report.QualityPassed || len(result.Conflicts) != 0 {
		return "", Manifest{}, errors.New("snapshot requires closed candles and a conflict-free quality result")
	}
	if len(inputs) == 0 {
		return "", Manifest{}, errors.New("snapshot requires input provenance")
	}
	for _, input := range inputs {
		if input.SourceID != SourceFixture || !input.syntheticVerified || len(input.SHA256) != 64 || input.ObjectID != input.SHA256 {
			return "", Manifest{}, errors.New("rights gate blocks persistence of non-synthetic or unhashed input")
		}
	}
	sortedRows := append([]Candle(nil), rows...)
	sort.Slice(sortedRows, func(i, j int) bool { return sortedRows[i].OpenTimeMS < sortedRows[j].OpenTimeMS })
	for _, row := range sortedRows {
		if row.SourceID != SourceFixture || row.NativeSymbol != symbol || row.Interval != interval || !row.IsClosed || row.OpenTimeMS < startMS || row.OpenTimeMS >= endMS {
			return "", Manifest{}, errors.New("snapshot contains a non-fixture, open, or out-of-range candle")
		}
	}
	sortedInputs := append([]InputObject(nil), inputs...)
	sort.Slice(sortedInputs, func(i, j int) bool {
		if sortedInputs[i].SourceID != sortedInputs[j].SourceID { return sortedInputs[i].SourceID < sortedInputs[j].SourceID }
		return sortedInputs[i].ObjectID < sortedInputs[j].ObjectID
	})
	inputIDs := make([]inputIdentity, 0, len(sortedInputs))
	for _, input := range sortedInputs {
		inputIDs = append(inputIDs, inputIdentity{SourceID: input.SourceID, ObjectID: input.ObjectID, SHA256: input.SHA256, TimestampUnit: input.TimestampUnit})
	}
	identity := snapshotIdentity{SchemaVersion: SchemaVersion, AdapterVersion: AdapterVersion, Symbol: symbol, Interval: interval, StartMS: startMS, EndMS: endMS, Inputs: inputIDs}
	identityBytes, err := json.Marshal(identity)
	if err != nil { return "", Manifest{}, err }
	identityHash := sha256.Sum256(identityBytes)
	snapshotID := hex.EncodeToString(identityHash[:])
	if err := os.MkdirAll(outputRoot, 0o755); err != nil { return "", Manifest{}, err }
	target := filepath.Join(outputRoot, snapshotID)
	if existing, err := readExistingSnapshot(target, snapshotID); err == nil {
		return target, existing, nil
	} else if !errors.Is(err, os.ErrNotExist) {
		return "", Manifest{}, err
	}
	tempDir, err := os.MkdirTemp(outputRoot, ".snapshot-*")
	if err != nil { return "", Manifest{}, err }
	defer os.RemoveAll(tempDir)

	candlesFile, err := os.OpenFile(filepath.Join(tempDir, "candles.csv"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o600)
	if err != nil { return "", Manifest{}, err }
	candleHash := sha256.New()
	if err := writeCandleCSV(io.MultiWriter(candlesFile, candleHash), sortedRows); err != nil {
		_ = candlesFile.Close()
		return "", Manifest{}, err
	}
	if err := candlesFile.Sync(); err != nil { _ = candlesFile.Close(); return "", Manifest{}, err }
	if err := candlesFile.Close(); err != nil { return "", Manifest{}, err }

	sourceIDs := []string{SourceFixture}
	manifest := Manifest{
		SchemaVersion: SchemaVersion, SnapshotID: snapshotID, SnapshotVersion: "1", CreatedAt: createdAt.UTC(),
		SourceIDs: sourceIDs, SourcePolicyReference: "fixture-only-no-grant", Inputs: sortedInputs, AdapterVersion: AdapterVersion,
		Venue: VenueBinance, MarketType: MarketSpot, NativeSymbol: symbol, Interval: interval,
		RangeStartMS: startMS, RangeEndMS: endMS, RowCount: len(sortedRows), CandlesSHA256: hex.EncodeToString(candleHash.Sum(nil)),
		TimestampPolicy: "source-unit-explicit; normalized UTC milliseconds", ClosedBarPolicy: "closed bars only; close_time < ingestion clock",
		RevisionCount: result.Report.RevisionRows, ConflictCount: result.Report.ConflictCount, Gaps: result.Report.Gaps,
		QualityPassed: result.Report.QualityPassed, RightsEligible: false, AvailabilityPolicy: "synthetic fixture; no production availability claim",
	}
	quality := QualityArtifact{Report: result.Report, Conflicts: result.Conflicts}
	if err := writeJSONFile(filepath.Join(tempDir, "quality.json"), quality); err != nil { return "", Manifest{}, err }
	if err := writeJSONFile(filepath.Join(tempDir, "manifest.json"), manifest); err != nil { return "", Manifest{}, err }
	if err := os.Rename(tempDir, target); err != nil {
		if existing, readErr := readExistingSnapshot(target, snapshotID); readErr == nil {
			return target, existing, nil
		}
		return "", Manifest{}, fmt.Errorf("atomic snapshot publish failed: %w", err)
	}
	return target, manifest, nil
}

func writeCandleCSV(w io.Writer, rows []Candle) error {
	csvWriter := csv.NewWriter(w)
	if err := csvWriter.Write([]string{"schema_version", "venue", "market_type", "native_symbol", "interval", "open_time_utc", "close_time_utc", "is_closed", "open", "high", "low", "close", "base_volume", "quote_volume", "trade_count", "source_id", "source_object_id", "source_timestamp_unit", "source_open_timestamp", "source_close_timestamp", "available_at", "revision_id"}); err != nil { return err }
	for _, candle := range rows {
		record := []string{
			SchemaVersion, candle.Venue, candle.MarketType, candle.NativeSymbol, string(candle.Interval),
			time.UnixMilli(candle.OpenTimeMS).UTC().Format(time.RFC3339Nano), time.UnixMilli(candle.CloseTimeMS).UTC().Format(time.RFC3339Nano),
			"true", candle.Open, candle.High, candle.Low, candle.Close, candle.BaseVolume, candle.QuoteVolume,
			fmt.Sprint(candle.TradeCount), candle.SourceID, candle.SourceObjectID, string(candle.SourceTimestampUnit),
			fmt.Sprint(candle.SourceOpenTimestamp), fmt.Sprint(candle.SourceCloseTimestamp), candle.AvailableAt.UTC().Format(time.RFC3339Nano), candle.RevisionID,
		}
		if err := csvWriter.Write(record); err != nil { return err }
	}
	csvWriter.Flush()
	return csvWriter.Error()
}

func writeJSONFile(path string, value any) error {
	file, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o600)
	if err != nil { return err }
	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(value); err != nil { _ = file.Close(); return err }
	if err := file.Sync(); err != nil { _ = file.Close(); return err }
	return file.Close()
}

func readExistingSnapshot(path, snapshotID string) (Manifest, error) {
	manifestFile, err := os.Open(filepath.Join(path, "manifest.json"))
	if err != nil { return Manifest{}, err }
	defer manifestFile.Close()
	var manifest Manifest
	if err := json.NewDecoder(manifestFile).Decode(&manifest); err != nil { return Manifest{}, errors.New("existing snapshot manifest is invalid") }
	if manifest.SnapshotID != snapshotID || manifest.CandlesSHA256 == "" { return Manifest{}, errors.New("existing snapshot identity or checksum is invalid") }
	actualHash, err := hashFile(filepath.Join(path, "candles.csv"))
	if err != nil || actualHash != manifest.CandlesSHA256 { return Manifest{}, errors.New("existing immutable snapshot checksum mismatch") }
	return manifest, nil
}

