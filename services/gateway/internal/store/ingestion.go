package store

import (
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"regexp"
	"strconv"
	"strings"
	"time"
)

type IngestionJob struct {
	ID               string               `json:"id"`
	ProviderID       string               `json:"provider_id"`
	CapabilityID     string               `json:"capability_id"`
	Dataset          string               `json:"dataset"`
	AssetClass       string               `json:"asset_class"`
	Venue            string               `json:"venue,omitempty"`
	Status           string               `json:"status"`
	ProcessedRecords int64                `json:"processed_records"`
	TotalRecords     int64                `json:"total_records"`
	ErrorCode        string               `json:"error_code,omitempty"`
	Checkpoint       *IngestionCheckpoint `json:"checkpoint,omitempty"`
	CreatedAt        string               `json:"created_at"`
	UpdatedAt        string               `json:"updated_at"`
}

type IngestionCheckpoint struct {
	Version int64  `json:"version"`
	Kind    string `json:"kind"`
	Value   string `json:"value"`
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
		checkpoint_version INTEGER NOT NULL DEFAULT 0,
		cursor_kind TEXT NOT NULL DEFAULT '',
		cursor_value TEXT NOT NULL DEFAULT '',
		created_at TEXT NOT NULL,
		updated_at TEXT NOT NULL
	);
	CREATE INDEX IF NOT EXISTS ingestion_jobs_recent ON ingestion_jobs(created_at DESC);`)
	if err != nil {
		return err
	}
	rows, err := s.DB.Query("PRAGMA table_info(ingestion_jobs)")
	if err != nil {
		return err
	}
	columns := map[string]bool{}
	for rows.Next() {
		var cid, notNull, primaryKey int
		var name, kind string
		var defaultValue sql.NullString
		if err = rows.Scan(&cid, &name, &kind, &notNull, &defaultValue, &primaryKey); err != nil {
			rows.Close()
			return err
		}
		columns[name] = true
	}
	if err = rows.Err(); err != nil {
		rows.Close()
		return err
	}
	if err = rows.Close(); err != nil {
		return err
	}
	for name, declaration := range map[string]string{
		"checkpoint_version": "INTEGER NOT NULL DEFAULT 0",
		"cursor_kind":        "TEXT NOT NULL DEFAULT ''",
		"cursor_value":       "TEXT NOT NULL DEFAULT ''",
	} {
		if !columns[name] {
			if _, err = s.DB.Exec("ALTER TABLE ingestion_jobs ADD COLUMN " + name + " " + declaration); err != nil {
				return err
			}
		}
	}
	_, err = s.DB.Exec(`UPDATE ingestion_jobs SET status='interrupted',error_code='process_restarted',updated_at=? WHERE status='running'`, Now())
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
	var version int64
	var kind, value string
	err := s.DB.QueryRow(`SELECT id,provider_id,capability_id,dataset,asset_class,venue,status,processed_records,total_records,error_code,checkpoint_version,cursor_kind,cursor_value,created_at,updated_at
		FROM ingestion_jobs WHERE id=?`, id).Scan(
		&job.ID, &job.ProviderID, &job.CapabilityID, &job.Dataset, &job.AssetClass, &job.Venue,
		&job.Status, &job.ProcessedRecords, &job.TotalRecords, &job.ErrorCode, &version, &kind, &value, &job.CreatedAt, &job.UpdatedAt,
	)
	if err == nil && version > 0 {
		job.Checkpoint = &IngestionCheckpoint{Version: version, Kind: kind, Value: value}
	}
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
	valid := current == status && current == "running" || current == "queued" && (status == "running" || status == "failed" || status == "cancelled" || status == "interrupted") || current == "running" && (status == "completed" || status == "failed" || status == "cancelled" || status == "interrupted") || current == "interrupted" && status == "running"
	if !valid {
		return errors.New("invalid ingestion job state transition")
	}
	if (current == "running" || current == "interrupted") && processed < previousProcessed {
		return errors.New("ingestion progress cannot move backwards")
	}
	if (current == "running" || current == "interrupted") && previousTotal > 0 && total != previousTotal {
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

func validateIngestionCheckpoint(checkpoint IngestionCheckpoint) error {
	if checkpoint.Version < 1 || len(checkpoint.Value) == 0 || len(checkpoint.Value) > 2048 || strings.TrimSpace(checkpoint.Value) != checkpoint.Value {
		return errors.New("ingestion checkpoint requires a positive version and bounded cursor value")
	}
	switch checkpoint.Kind {
	case "page", "offset", "sequence":
		value, err := strconv.ParseUint(checkpoint.Value, 10, 63)
		if err != nil || checkpoint.Kind == "page" && value == 0 {
			return errors.New("ingestion numeric cursor is invalid")
		}
	case "timestamp":
		if _, err := time.Parse(time.RFC3339Nano, checkpoint.Value); err != nil {
			return errors.New("ingestion timestamp cursor is invalid")
		}
	default:
		return errors.New("unsupported ingestion cursor kind")
	}
	return nil
}

// SaveIngestionCheckpoint advances the resumable cursor and record counts as one
// SQLite transaction. Versioned repeats are accepted only when the content agrees.
func (s *Store) SaveIngestionCheckpoint(id string, checkpoint IngestionCheckpoint, processed, total int64) error {
	if err := validateIngestionCheckpoint(checkpoint); err != nil {
		return err
	}
	if processed < 0 || total < 0 || (total > 0 && processed > total) {
		return errors.New("ingestion progress counts are invalid")
	}
	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var status, currentKind, currentValue string
	var currentVersion, previousProcessed, previousTotal int64
	err = tx.QueryRow(`SELECT status,checkpoint_version,cursor_kind,cursor_value,processed_records,total_records
		FROM ingestion_jobs WHERE id=?`, id).Scan(&status, &currentVersion, &currentKind, &currentValue, &previousProcessed, &previousTotal)
	if err != nil {
		return err
	}
	if status != "running" {
		return errors.New("ingestion checkpoint requires a running job")
	}
	if checkpoint.Version == currentVersion {
		if checkpoint.Kind == currentKind && checkpoint.Value == currentValue && processed == previousProcessed && total == previousTotal {
			return nil
		}
		return errors.New("conflicting duplicate ingestion checkpoint")
	}
	if checkpoint.Version != currentVersion+1 {
		return errors.New("ingestion checkpoint version must advance by one")
	}
	if processed < previousProcessed || previousTotal > 0 && total != previousTotal {
		return errors.New("ingestion progress cannot move backwards or change a known total")
	}
	if _, err = tx.Exec(`UPDATE ingestion_jobs SET checkpoint_version=?,cursor_kind=?,cursor_value=?,processed_records=?,total_records=?,updated_at=? WHERE id=?`,
		checkpoint.Version, checkpoint.Kind, checkpoint.Value, processed, total, Now(), id); err != nil {
		return err
	}
	return tx.Commit()
}

func safeIngestionErrorCode(code string) string {
	if code != "" && !ingestionErrorCode.MatchString(code) {
		return "provider_error"
	}
	return code
}
