package store

import (
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"regexp"
	"strings"
)

type IngestionJob struct {
	ID               string `json:"id"`
	ProviderID       string `json:"provider_id"`
	CapabilityID     string `json:"capability_id"`
	Dataset          string `json:"dataset"`
	AssetClass       string `json:"asset_class"`
	Venue            string `json:"venue,omitempty"`
	Status           string `json:"status"`
	ProcessedRecords int64  `json:"processed_records"`
	TotalRecords     int64  `json:"total_records"`
	ErrorCode        string `json:"error_code,omitempty"`
	CreatedAt        string `json:"created_at"`
	UpdatedAt        string `json:"updated_at"`
}

var ingestionErrorCode = regexp.MustCompile(`^[a-z0-9][a-z0-9._-]{0,79}$`)

func (s *Store) ingestionJobSchema() error {
	_, err := s.DB.Exec(`CREATE TABLE IF NOT EXISTS ingestion_jobs(
		id TEXT PRIMARY KEY,
		provider_id TEXT NOT NULL,
		capability_id TEXT NOT NULL,
		dataset TEXT NOT NULL,
		asset_class TEXT NOT NULL,
		venue TEXT NOT NULL DEFAULT '',
		status TEXT NOT NULL CHECK(status IN ('queued','running','completed','failed','cancelled','interrupted')),
		processed_records INTEGER NOT NULL DEFAULT 0 CHECK(processed_records>=0),
		total_records INTEGER NOT NULL DEFAULT 0 CHECK(total_records>=0),
		error_code TEXT NOT NULL DEFAULT '',
		created_at TEXT NOT NULL,
		updated_at TEXT NOT NULL
	);
	CREATE INDEX IF NOT EXISTS ingestion_jobs_recent ON ingestion_jobs(created_at DESC);`)
	return err
}

func validIngestionJob(job IngestionJob) error {
	for name, value := range map[string]string{
		"job id": job.ID, "provider id": job.ProviderID,
		"capability id": job.CapabilityID, "dataset": job.Dataset,
		"asset class": job.AssetClass,
	} {
		if strings.TrimSpace(value) == "" || len(value) > 160 {
			return fmt.Errorf("%s is required and must be at most 160 characters", name)
		}
	}
	if len(job.Venue) > 80 {
		return errors.New("venue must be at most 80 characters")
	}
	return nil
}

func (s *Store) CreateIngestionJob(job IngestionJob) error {
	if err := validIngestionJob(job); err != nil {
		return err
	}
	if job.Status != "" && job.Status != "queued" {
		return errors.New("new ingestion job must start queued")
	}
	if job.ProcessedRecords != 0 || job.TotalRecords != 0 || job.ErrorCode != "" {
		return errors.New("new ingestion job cannot include progress or an error")
	}
	job.ID = strings.TrimSpace(job.ID)
	job.ProviderID = strings.TrimSpace(job.ProviderID)
	job.CapabilityID = strings.TrimSpace(job.CapabilityID)
	job.Dataset = strings.TrimSpace(job.Dataset)
	job.AssetClass = strings.TrimSpace(job.AssetClass)
	job.Venue = strings.TrimSpace(job.Venue)
	now := Now()
	_, err := s.DB.Exec(`INSERT INTO ingestion_jobs
		(id,provider_id,capability_id,dataset,asset_class,venue,status,processed_records,total_records,error_code,created_at,updated_at)
		VALUES(?,?,?,?,?,?,'queued',0,0,'',?,?)`, job.ID, job.ProviderID, job.CapabilityID, job.Dataset, job.AssetClass, job.Venue, now, now)
	return err
}

func (s *Store) IngestionJob(id string) (IngestionJob, error) {
	var job IngestionJob
	err := s.DB.QueryRow(`SELECT id,provider_id,capability_id,dataset,asset_class,venue,status,processed_records,total_records,error_code,created_at,updated_at
		FROM ingestion_jobs WHERE id=?`, id).Scan(
		&job.ID, &job.ProviderID, &job.CapabilityID, &job.Dataset, &job.AssetClass, &job.Venue,
		&job.Status, &job.ProcessedRecords, &job.TotalRecords, &job.ErrorCode, &job.CreatedAt, &job.UpdatedAt,
	)
	return job, err
}

func (s *Store) IngestionJobs() ([]IngestionJob, error) {
	rows, err := s.DB.Query(`SELECT id,provider_id,capability_id,dataset,asset_class,venue,status,processed_records,total_records,error_code,created_at,updated_at
		FROM ingestion_jobs ORDER BY created_at DESC,id LIMIT 100`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	result := []IngestionJob{}
	for rows.Next() {
		var job IngestionJob
		if err = rows.Scan(&job.ID, &job.ProviderID, &job.CapabilityID, &job.Dataset, &job.AssetClass, &job.Venue,
			&job.Status, &job.ProcessedRecords, &job.TotalRecords, &job.ErrorCode, &job.CreatedAt, &job.UpdatedAt); err != nil {
			return nil, err
		}
		result = append(result, job)
	}
	return result, rows.Err()
}

// UpdateIngestionJob moves one persisted job forward and stores its latest
// record counts. Error details are represented only by a bounded opaque code.
func (s *Store) UpdateIngestionJob(id, status string, processed, total int64, errorCode string) error {
	if processed < 0 || total < 0 || (total > 0 && processed > total) {
		return errors.New("ingestion progress counts are invalid")
	}
	if status != "running" && status != "completed" && status != "failed" && status != "cancelled" && status != "interrupted" {
		return errors.New("invalid ingestion job status")
	}
	if errorCode != "" && !ingestionErrorCode.MatchString(errorCode) {
		return errors.New("ingestion error must be a non-sensitive error code")
	}
	if status == "failed" && errorCode == "" {
		return errors.New("failed ingestion job requires a non-sensitive error code")
	}
	if status == "completed" && total > 0 && processed != total {
		return errors.New("ingestion job cannot complete with missing records")
	}
	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var current string
	var previousProcessed, previousTotal int64
	err = tx.QueryRow("SELECT status,processed_records,total_records FROM ingestion_jobs WHERE id=?", id).Scan(&current, &previousProcessed, &previousTotal)
	if err != nil {
		return err
	}
	valid := current == status && current == "running" || current == "queued" && (status == "running" || status == "failed" || status == "cancelled" || status == "interrupted") || current == "running" && (status == "completed" || status == "failed" || status == "cancelled" || status == "interrupted")
	if !valid {
		return errors.New("invalid ingestion job state transition")
	}
	if current == "running" && processed < previousProcessed {
		return errors.New("ingestion progress cannot move backwards")
	}
	if current == "running" && previousTotal > 0 && total != previousTotal {
		return errors.New("ingestion total cannot change after it is known")
	}
	if status == "running" && errorCode != "" {
		return errors.New("running ingestion job cannot include an error")
	}
	result, err := tx.Exec(`UPDATE ingestion_jobs SET status=?,processed_records=?,total_records=?,error_code=?,updated_at=? WHERE id=?`, status, processed, total, errorCode, Now(), id)
	if err != nil {
		return err
	}
	if n, _ := result.RowsAffected(); n != 1 {
		return sql.ErrNoRows
	}
	return tx.Commit()
}

func (job IngestionJob) MarshalJSON() ([]byte, error) {
	type public IngestionJob
	job.ErrorCode = safeIngestionErrorCode(job.ErrorCode)
	return json.Marshal(public(job))
}

func safeIngestionErrorCode(code string) string {
	if code != "" && !ingestionErrorCode.MatchString(code) {
		return "provider_error"
	}
	return code
}
