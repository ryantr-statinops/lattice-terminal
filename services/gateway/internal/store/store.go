package store

import (
	"database/sql"
	"encoding/json"
	"errors"
	_ "modernc.org/sqlite"
	"os"
	"path/filepath"
	"time"
)

type Store struct{ DB *sql.DB }
type Run struct {
	ID       string          `json:"id"`
	Kind     string          `json:"kind"`
	File     string          `json:"file"`
	Snapshot string          `json:"snapshot"`
	Status   string          `json:"status"`
	Created  string          `json:"created_at"`
	Params   json.RawMessage `json:"params"`
}
type Event struct {
	Seq     int64           `json:"seq"`
	Type    string          `json:"type"`
	Payload json.RawMessage `json:"payload"`
	Created string          `json:"created_at"`
}

func Open(root string) (*Store, error) {
	if err := os.MkdirAll(root, 0700); err != nil {
		return nil, err
	}
	db, err := sql.Open("sqlite", filepath.Join(root, "kestrel.sqlite"))
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(1)
	s := &Store{db}
	_, err = db.Exec(`PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000;
CREATE TABLE IF NOT EXISTS migrations(version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO migrations VALUES(1);
CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, kind TEXT NOT NULL, file TEXT NOT NULL, snapshot TEXT NOT NULL, status TEXT NOT NULL, created TEXT NOT NULL, params TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS run_events(run_id TEXT NOT NULL REFERENCES runs(id), seq INTEGER NOT NULL, type TEXT NOT NULL, payload TEXT NOT NULL, created TEXT NOT NULL, PRIMARY KEY(run_id,seq));
CREATE TABLE IF NOT EXISTS artifacts(run_id TEXT NOT NULL REFERENCES runs(id), name TEXT NOT NULL, path TEXT NOT NULL, hash TEXT NOT NULL, PRIMARY KEY(run_id,name));
UPDATE runs SET status='interrupted' WHERE status IN ('queued','running','stopping');`)
	if err != nil {
		db.Close()
		return nil, err
	}
	if err = s.financeSchema(); err != nil {
		db.Close()
		return nil, err
	}
	if err = s.routingSchema(); err != nil {
		db.Close()
		return nil, err
	}
	if err = s.instrumentAliasSchema(); err != nil {
		db.Close()
		return nil, err
	}
	return s, nil
}
func (s *Store) Close() error { return s.DB.Close() }
func Now() string             { return time.Now().UTC().Format(time.RFC3339Nano) }
func (s *Store) CreateRun(v Run) error {
	if v.Kind != "research" && v.Kind != "backtest" && v.Kind != "strategy" {
		return errors.New("invalid run kind")
	}
	var params map[string]any
	if json.Unmarshal(v.Params, &params) != nil || params == nil {
		return errors.New("invalid parameters")
	}
	_, err := s.DB.Exec("INSERT INTO runs VALUES(?,?,?,?,?,?,?)", v.ID, v.Kind, v.File, v.Snapshot, "queued", Now(), string(v.Params))
	return err
}
func (s *Store) Runs(kind string) ([]Run, error) {
	rows, err := s.DB.Query("SELECT id,kind,file,snapshot,status,created,params FROM runs WHERE kind=? ORDER BY created DESC LIMIT 100", kind)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	result := []Run{}
	for rows.Next() {
		var v Run
		var raw string
		if err = rows.Scan(&v.ID, &v.Kind, &v.File, &v.Snapshot, &v.Status, &v.Created, &raw); err != nil {
			return nil, err
		}
		v.Params = json.RawMessage(raw)
		result = append(result, v)
	}
	return result, rows.Err()
}
func (s *Store) Run(id string) (Run, error) {
	var v Run
	var raw string
	err := s.DB.QueryRow("SELECT id,kind,file,snapshot,status,created,params FROM runs WHERE id=?", id).Scan(&v.ID, &v.Kind, &v.File, &v.Snapshot, &v.Status, &v.Created, &raw)
	v.Params = json.RawMessage(raw)
	return v, err
}
func transition(from, to string) bool {
	if to == "" || from == to {
		return true
	}
	switch from {
	case "queued":
		return to == "running" || to == "cancelled" || to == "failed" || to == "interrupted"
	case "running":
		return to == "completed" || to == "failed" || to == "stopping" || to == "cancelled" || to == "interrupted"
	case "stopping":
		return to == "cancelled" || to == "failed" || to == "interrupted"
	}
	return false
}
func (s *Store) Append(id string, event Event, status string) error {
	if !json.Valid(event.Payload) || event.Seq < 1 {
		return errors.New("invalid event")
	}
	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var old string
	if err = tx.QueryRow("SELECT status FROM runs WHERE id=?", id).Scan(&old); err != nil {
		return err
	}
	res, err := tx.Exec("INSERT OR IGNORE INTO run_events VALUES(?,?,?,?,?)", id, event.Seq, event.Type, string(event.Payload), Now())
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		var kind, payload string
		if err = tx.QueryRow("SELECT type,payload FROM run_events WHERE run_id=? AND seq=?", id, event.Seq).Scan(&kind, &payload); err != nil {
			return err
		}
		if kind != event.Type || payload != string(event.Payload) {
			return errors.New("conflicting duplicate run event")
		}
		return nil
	}
	if !transition(old, status) {
		return errors.New("invalid run transition")
	}
	if status != "" {
		if _, err = tx.Exec("UPDATE runs SET status=? WHERE id=?", status, id); err != nil {
			return err
		}
	}
	if event.Type == "artifact" {
		var artifact Artifact
		if json.Unmarshal(event.Payload, &artifact) != nil || !validArtifact(id, artifact) {
			return errors.New("invalid artifact reference")
		}
		var oldHash string
		err = tx.QueryRow("SELECT hash FROM artifacts WHERE run_id=? AND name=?", id, artifact.Name).Scan(&oldHash)
		if err == nil && oldHash != artifact.Hash {
			return errors.New("artifact name already published with different content")
		}
		if err != nil && err != sql.ErrNoRows {
			return err
		}
		if _, err = tx.Exec("INSERT OR IGNORE INTO artifacts VALUES(?,?,?,?)", id, artifact.Name, artifact.Path, artifact.Hash); err != nil {
			return err
		}
	}
	return tx.Commit()
}
func (s *Store) Events(id string, after int64) ([]Event, error) {
	rows, err := s.DB.Query("SELECT seq,type,payload,created FROM run_events WHERE run_id=? AND seq>? ORDER BY seq LIMIT 200", id, after)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	result := []Event{}
	for rows.Next() {
		var v Event
		var raw string
		if err = rows.Scan(&v.Seq, &v.Type, &raw, &v.Created); err != nil {
			return nil, err
		}
		v.Payload = json.RawMessage(raw)
		result = append(result, v)
	}
	return result, rows.Err()
}
