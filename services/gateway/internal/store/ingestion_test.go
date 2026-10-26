package store

import (
	"testing"
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
