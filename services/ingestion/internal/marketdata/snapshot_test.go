package marketdata

import (
	"archive/zip"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestPublishSnapshotIsDeterministicImmutableAndFixtureOnly(t *testing.T) {
	cfg := parserConfig(TimestampMilliseconds)
	candles, input, err := LoadArchiveFile("testdata/synthetic-archive-2024.csv", "", cfg)
	if err != nil { t.Fatal(err) }
	start := candles[0].OpenTimeMS
	end := start + Interval15m.Duration().Milliseconds()
	result, err := Reconcile(candles, "BTCUSDT", Interval15m, start, end)
	if err != nil { t.Fatal(err) }
	root := filepath.Join(t.TempDir(), "snapshots")
	createdAt := time.Date(2025, 1, 2, 1, 0, 0, 0, time.UTC)
	path, manifest, err := PublishSnapshot(root, result.Candles, []InputObject{input}, result, "BTCUSDT", Interval15m, start, end, createdAt)
	if err != nil { t.Fatal(err) }
	if manifest.RightsEligible || manifest.RowCount != 1 || manifest.CandlesSHA256 == "" {
		t.Fatalf("snapshot rights/data manifest is incorrect: %+v", manifest)
	}
	if _, err := os.Stat(filepath.Join(path, "candles.csv")); err != nil { t.Fatal(err) }
	var saved Manifest
	manifestBytes, err := os.ReadFile(filepath.Join(path, "manifest.json"))
	if err != nil { t.Fatal(err) }
	if err := json.Unmarshal(manifestBytes, &saved); err != nil { t.Fatal(err) }
	if saved.SnapshotID != manifest.SnapshotID || saved.CandlesSHA256 != manifest.CandlesSHA256 { t.Fatal("manifest did not round-trip") }

	replayAt := createdAt.Add(24 * time.Hour)
	replayPath, replayManifest, err := PublishSnapshot(root, result.Candles, []InputObject{input}, result, "BTCUSDT", Interval15m, start, end, replayAt)
	if err != nil { t.Fatal(err) }
	if replayPath != path || !replayManifest.CreatedAt.Equal(createdAt) { t.Fatal("identical input replay was not idempotent") }

	if err := os.WriteFile(filepath.Join(path, "candles.csv"), []byte("tampered"), 0o600); err != nil { t.Fatal(err) }
	if _, _, err := PublishSnapshot(root, result.Candles, []InputObject{input}, result, "BTCUSDT", Interval15m, start, end, replayAt); err == nil || !strings.Contains(err.Error(), "checksum mismatch") {
		t.Fatal("publisher replaced a modified immutable snapshot")
	}
}

func TestPublishSnapshotRejectsNonFixtureRightsAndConflicts(t *testing.T) {
	candle := testCandle(testStartMS, "11")
	result, err := Reconcile([]Candle{candle}, "BTCUSDT", Interval15m, testStartMS, testStartMS+Interval15m.Duration().Milliseconds())
	if err != nil { t.Fatal(err) }
	input := InputObject{SourceID: "BIN-SPOT-PUBLIC", ObjectID: strings.Repeat("a", 64), SHA256: strings.Repeat("a", 64), TimestampUnit: TimestampMilliseconds, RetrievedAt: time.Now().UTC()}
	if _, _, err := PublishSnapshot(t.TempDir(), result.Candles, []InputObject{input}, result, "BTCUSDT", Interval15m, testStartMS, testStartMS+Interval15m.Duration().Milliseconds(), time.Now().UTC()); err == nil {
		t.Fatal("persisted non-synthetic input while rights gate is closed")
	}
	conflicting := testCandle(testStartMS, "11.5")
	conflicting.SourceID, conflicting.SourceObjectID = SourceFixture, "another-object"
	conflicting.RevisionID = revisionID(conflicting)
	conflictResult, err := Reconcile([]Candle{candle, conflicting}, "BTCUSDT", Interval15m, testStartMS, testStartMS+Interval15m.Duration().Milliseconds())
	if err != nil { t.Fatal(err) }
	fixtureInput := fixtureInputForTest("b")
	if _, _, err := PublishSnapshot(t.TempDir(), conflictResult.Candles, []InputObject{fixtureInput}, conflictResult, "BTCUSDT", Interval15m, testStartMS, testStartMS+Interval15m.Duration().Milliseconds(), time.Now().UTC()); err == nil {
		t.Fatal("published conflicting revisions")
	}
}

func TestArchiveZipRequiresMatchingChecksum(t *testing.T) {
	dir := t.TempDir()
	zipPath := filepath.Join(dir, "synthetic.zip")
	file, err := os.Create(zipPath)
	if err != nil { t.Fatal(err) }
	writer := zip.NewWriter(file)
	entry, err := writer.Create("synthetic.csv")
	if err != nil { t.Fatal(err) }
	if _, err := entry.Write([]byte("1735688700000,10,12,9,11,1,1735689599999,12,2,1,5,0\n")); err != nil { t.Fatal(err) }
	if err := writer.Close(); err != nil { t.Fatal(err) }
	if err := file.Close(); err != nil { t.Fatal(err) }
	checksumPath := zipPath + ".CHECKSUM"
	if err := os.WriteFile(checksumPath, []byte(strings.Repeat("0", 64)+"  synthetic.zip\n"), 0o600); err != nil { t.Fatal(err) }
	if _, _, err := LoadArchiveFile(zipPath, checksumPath, parserConfig(TimestampMilliseconds)); err == nil || !strings.Contains(err.Error(), "checksum mismatch") {
		t.Fatal("accepted zip with bad SHA-256 checksum")
	}
}

func TestArchiveZipAcceptsVerifiedSyntheticFixture(t *testing.T) {
	dir := t.TempDir()
	zipPath := filepath.Join(dir, "synthetic.zip")
	file, err := os.Create(zipPath)
	if err != nil { t.Fatal(err) }
	writer := zip.NewWriter(file)
	entry, err := writer.Create("synthetic.csv")
	if err != nil { t.Fatal(err) }
	if _, err := entry.Write([]byte("1735688700000,10,12,9,11,1,1735689599999,12,2,1,5,0\n")); err != nil { t.Fatal(err) }
	if err := writer.Close(); err != nil { t.Fatal(err) }
	if err := file.Close(); err != nil { t.Fatal(err) }
	hash, err := hashFile(zipPath)
	if err != nil { t.Fatal(err) }
	if err := os.WriteFile(zipPath+".CHECKSUM", []byte(hash+"  synthetic.zip\n"), 0o600); err != nil { t.Fatal(err) }
	marker := `{"schema_version":"1","is_synthetic":true,"source_id":"fixture-only","sha256":"` + hash + `"}`
	if err := os.WriteFile(zipPath+".fixture.json", []byte(marker), 0o600); err != nil { t.Fatal(err) }
	candles, input, err := LoadArchiveFile(zipPath, "", parserConfig(TimestampMilliseconds))
	if err != nil { t.Fatal(err) }
	if len(candles) != 1 || input.SHA256 != hash || !input.syntheticVerified { t.Fatalf("unexpected loaded archive: %+v %+v", candles, input) }
}

func TestOfflineLoaderRequiresSyntheticMarkerAndMatchingHash(t *testing.T) {
	data, err := os.ReadFile("testdata/synthetic-archive-2024.csv")
	if err != nil { t.Fatal(err) }
	dir := t.TempDir()
	path := filepath.Join(dir, "copied.csv")
	if err := os.WriteFile(path, data, 0o600); err != nil { t.Fatal(err) }
	if _, _, err := LoadArchiveFile(path, "", parserConfig(TimestampMilliseconds)); err == nil {
		t.Fatal("accepted input without synthetic provenance marker")
	}
	hash, err := hashFile(path)
	if err != nil { t.Fatal(err) }
	wrongMarker := `{"schema_version":"1","is_synthetic":true,"source_id":"fixture-only","sha256":"` + strings.Repeat("0", 64) + `"}`
	if err := os.WriteFile(path+".fixture.json", []byte(wrongMarker), 0o600); err != nil { t.Fatal(err) }
	if _, _, err := LoadArchiveFile(path, "", parserConfig(TimestampMilliseconds)); err == nil {
		t.Fatal("accepted fixture marker with mismatched content hash")
	}
	correctMarker := `{"schema_version":"1","is_synthetic":true,"source_id":"fixture-only","sha256":"` + hash + `"}`
	if err := os.WriteFile(path+".fixture.json", []byte(correctMarker), 0o600); err != nil { t.Fatal(err) }
	if _, input, err := LoadArchiveFile(path, "", parserConfig(TimestampMilliseconds)); err != nil || !input.syntheticVerified {
		t.Fatalf("failed to accept correctly marked synthetic fixture: %v", err)
	}
}

func TestSnapshotPublishFailureLeavesNoPartialSnapshot(t *testing.T) {
	root := filepath.Join(t.TempDir(), "not-a-directory")
	if err := os.WriteFile(root, []byte("occupied"), 0o600); err != nil { t.Fatal(err) }
	candle := testCandle(testStartMS, "11")
	result, err := Reconcile([]Candle{candle}, "BTCUSDT", Interval15m, testStartMS, testStartMS+Interval15m.Duration().Milliseconds())
	if err != nil { t.Fatal(err) }
	input := fixtureInputForTest("c")
	if _, _, err := PublishSnapshot(root, result.Candles, []InputObject{input}, result, "BTCUSDT", Interval15m, testStartMS, testStartMS+Interval15m.Duration().Milliseconds(), time.Now().UTC()); err == nil {
		t.Fatal("publish unexpectedly succeeded when output root is not a directory")
	}
	entries, err := os.ReadDir(filepath.Dir(root))
	if err != nil { t.Fatal(err) }
	if len(entries) != 1 || entries[0].Name() != filepath.Base(root) { t.Fatal("failed publish left partial artifacts") }
}

func fixtureInputForTest(seed string) InputObject {
	hash := strings.Repeat(seed, 64)
	return InputObject{SourceID: SourceFixture, ObjectID: hash, SHA256: hash, TimestampUnit: TimestampMilliseconds, RetrievedAt: time.Now().UTC(), syntheticVerified: true}
}
