package store

import (
	"database/sql"
	"errors"
	"time"
)

func (s *Store) PaperCursor(id string) (string, int64, error) {
	var snapshot string
	var seq int64
	err := s.DB.QueryRow("SELECT snapshot,sequence FROM paper_cursors WHERE allocation_id=?", id).Scan(&snapshot, &seq)
	if err == sql.ErrNoRows {
		return "", 0, nil
	}
	return snapshot, seq, err
}
func (s *Store) AdvanceCursor(id, snapshot string, seq int64, at, symbol, bid, ask string) error {
	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err = s.advanceCursor(tx, id, snapshot, seq, at, symbol, bid, ask); err != nil {
		return err
	}
	return tx.Commit()
}
func (s *Store) advanceCursor(tx *sql.Tx, id, snapshot string, seq int64, at, symbol, bid, ask string) error {
	when, err := time.Parse(time.RFC3339Nano, at)
	if err != nil {
		return err
	}
	if _, err = amount(bid, false); err != nil {
		return err
	}
	if _, err = amount(ask, false); err != nil {
		return err
	}
	var old string
	var previous int64
	err = tx.QueryRow("SELECT snapshot,sequence FROM paper_cursors WHERE allocation_id=?", id).Scan(&old, &previous)
	if err != nil && err != sql.ErrNoRows {
		return err
	}
	if previous >= seq && old == snapshot {
		return nil
	}
	if (old != "" && old != snapshot) || seq != previous+1 {
		return errors.New("paper cursor source/sequence gap")
	}
	if err = settleSecurities(tx, id, when); err != nil {
		return err
	}
	if err = settleCash(tx, id, when); err != nil {
		return err
	}
	_, err = tx.Exec("INSERT INTO paper_cursors VALUES(?,?,?,?) ON CONFLICT(allocation_id) DO UPDATE SET snapshot=excluded.snapshot,sequence=excluded.sequence,event_time=excluded.event_time", id, snapshot, seq, when.UTC().Format(time.RFC3339Nano))
	if err != nil {
		return err
	}
	price := d(bid).Add(d(ask)).Div(d("2")).String()
	var current string
	err = tx.QueryRow("SELECT event_time FROM marks WHERE instrument_id=?", symbol).Scan(&current)
	if err != nil && err != sql.ErrNoRows {
		return err
	}
	newer := err == sql.ErrNoRows
	if !newer {
		t, parse := time.Parse(time.RFC3339Nano, current)
		newer = parse == nil && !t.After(when)
	}
	if newer {
		_, err = tx.Exec("INSERT INTO marks VALUES(?,?,?,'SYNTHETIC-FIXTURE') ON CONFLICT(instrument_id) DO UPDATE SET price=excluded.price,event_time=excluded.event_time,source=excluded.source", symbol, price, when.UTC().Format(time.RFC3339Nano))
		if err != nil {
			return err
		}
	}
	return nil
}
