package store

import (
	"database/sql"
	"path/filepath"
	"testing"

	_ "modernc.org/sqlite"
)

func TestIngestionJobStateAndProgressPersist(t *testing.T) {
	root := t.TempDir()
	s, err := Open(root)
	if err != nil {
		t.Fatal(err)
	}
	input := IngestionJob{ID: "job-ssi-instrument", ProviderID: "ssi", CapabilityID: "ssi:market-data:instruments.equity:HOSE", Dataset: "instruments", AssetClass: "equity", Venue: "HOSE"}
	if err = s.CreateIngestionJob(input); err != nil {
		t.Fatal(err)
	}
	if err = s.UpdateIngestionJob(input.ID, "running", 3, 10, ""); err != nil {
		t.Fatal(err)
	}
	if err = s.UpdateIngestionJob(input.ID, "running", 2, 10, ""); err == nil {
		t.Fatal("backward progress was accepted")
	}
	if err = s.UpdateIngestionJob(input.ID, "running", 4, 0, ""); err == nil {
		t.Fatal("known ingestion total was cleared")
	}
	if err = s.UpdateIngestionJob(input.ID, "completed", 9, 10, ""); err == nil {
		t.Fatal("incomplete ingestion was marked completed")
	}
	if err = s.UpdateIngestionJob(input.ID, "completed", 10, 10, ""); err != nil {
		t.Fatal(err)
	}
	if err = s.Close(); err != nil {
		t.Fatal(err)
	}
	s, err = Open(root)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	job, err := s.IngestionJob(input.ID)
	if err != nil || job.Status != "completed" || job.ProcessedRecords != 10 || job.TotalRecords != 10 || job.ProviderID != "ssi" {
		t.Fatalf("persisted ingestion job = %#v, %v", job, err)
	}
}

func TestIngestionCheckpointResumesWithAtomicMonotonicProgress(t *testing.T) {
	root := t.TempDir()
	s, err := Open(root)
	if err != nil {
		t.Fatal(err)
	}
	job := IngestionJob{ID: "resume", ProviderID: "ssi", CapabilityID: "ssi:bars:1d", Dataset: "candles.1d", AssetClass: "equity"}
	if err = s.CreateIngestionJob(job); err != nil {
		t.Fatal(err)
	}
	if err = s.UpdateIngestionJob(job.ID, "running", 0, 4, ""); err != nil {
		t.Fatal(err)
	}
	first := IngestionCheckpoint{Version: 1, Kind: "page", Value: "2"}
	if err = s.SaveIngestionCheckpoint(job.ID, first, 2, 4); err != nil {
		t.Fatal(err)
	}
	if err = s.SaveIngestionCheckpoint(job.ID, first, 2, 4); err != nil {
		t.Fatalf("exact checkpoint replay should be idempotent: %v", err)
	}
	if err = s.Close(); err != nil {
		t.Fatal(err)
	}
	s, err = Open(root)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	if err = s.SaveIngestionCheckpoint(job.ID, IngestionCheckpoint{Version: 3, Kind: "page", Value: "4"}, 4, 4); err == nil {
		t.Fatal("checkpoint version gap was accepted")
	}
	if err = s.SaveIngestionCheckpoint(job.ID, IngestionCheckpoint{Version: 2, Kind: "page", Value: "3"}, 3, 4); err != nil {
		t.Fatal(err)
	}
	got, err := s.IngestionJob(job.ID)
	if err != nil || got.Checkpoint == nil || got.Checkpoint.Version != 2 || got.Checkpoint.Value != "3" || got.ProcessedRecords != 3 {
		t.Fatalf("resumable checkpoint = %#v, %v", got, err)
	}
	if err = s.SaveIngestionCheckpoint(job.ID, IngestionCheckpoint{Version: 3, Kind: "page", Value: "4"}, 2, 4); err == nil {
		t.Fatal("backward checkpoint progress was accepted")
	}
}

func TestIngestionCheckpointMigrationAddsCursorColumnsToExistingQueue(t *testing.T) {
	root := t.TempDir()
	path := filepath.Join(root, "kestrel.sqlite")
	db, err := sql.Open("sqlite", path)
	if err != nil {
		t.Fatal(err)
	}
	_, err = db.Exec(`CREATE TABLE ingestion_jobs(
		id TEXT PRIMARY KEY,provider_id TEXT NOT NULL,capability_id TEXT NOT NULL,dataset TEXT NOT NULL,
		asset_class TEXT NOT NULL,venue TEXT NOT NULL DEFAULT '',status TEXT NOT NULL,
		processed_records INTEGER NOT NULL DEFAULT 0,total_records INTEGER NOT NULL DEFAULT 0,
		error_code TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL,updated_at TEXT NOT NULL
	)`)
	if err != nil {
		t.Fatal(err)
	}
	if err = db.Close(); err != nil {
		t.Fatal(err)
	}
	s, err := Open(root)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	job := IngestionJob{ID: "old-queue", ProviderID: "ssi", CapabilityID: "ssi:bars:1d", Dataset: "candles.1d", AssetClass: "equity"}
	if err = s.CreateIngestionJob(job); err != nil {
		t.Fatal(err)
	}
	if err = s.UpdateIngestionJob(job.ID, "running", 0, 1, ""); err != nil {
		t.Fatal(err)
	}
	if err = s.SaveIngestionCheckpoint(job.ID, IngestionCheckpoint{Version: 1, Kind: "offset", Value: "100"}, 1, 1); err != nil {
		t.Fatal(err)
	}
}

func TestIngestionJobsRejectInvalidInitialStateAndSensitiveErrorDetails(t *testing.T) {
	s, err := Open(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	job := IngestionJob{ID: "job-invalid", ProviderID: "ssi", CapabilityID: "ssi:dataset", Dataset: "bars", AssetClass: "equity", Status: "running"}
	if err = s.CreateIngestionJob(job); err == nil {
		t.Fatal("new ingestion job bypassed the queued state")
	}
	job.Status = ""
	if err = s.CreateIngestionJob(job); err != nil {
		t.Fatal(err)
	}
	if err = s.UpdateIngestionJob(job.ID, "failed", 0, 0, "provider returned private token"); err == nil {
		t.Fatal("free-text provider error was accepted")
	}
	if err = s.UpdateIngestionJob(job.ID, "failed", 0, 0, ""); err == nil {
		t.Fatal("failed ingestion job without a reason code was accepted")
	}
	if err = s.UpdateIngestionJob(job.ID, "completed", 0, 0, ""); err == nil {
		t.Fatal("queued ingestion job skipped its running state")
	}
}
