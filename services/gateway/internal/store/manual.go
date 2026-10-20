package store

import (
	"database/sql"
	"errors"
	"fmt"
)

func (s *Store) ManualStep(id, snapshot string, after, seq int64, at, symbol, bid, ask string, fills []PaperFill) error {
	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	a, err := scanAllocation(tx.QueryRow("SELECT * FROM allocations WHERE id=?", id))
	if err != nil {
		return err
	}
	if a.Mode != "manual" {
		return errors.New("not a manual allocation")
	}
	var cursor int64
	err = tx.QueryRow("SELECT sequence FROM paper_cursors WHERE allocation_id=?", id).Scan(&cursor)
	if err == sql.ErrNoRows {
		cursor = 0
	} else if err != nil {
		return err
	}
	if a.Status != "stopped" {
		return errors.New("reconcile interrupted allocation before advancing")
	}
	if cursor != after || seq != after+1 {
		return errors.New("paper cursor advanced; refresh state")
	}
	for _, fill := range fills {
		order, err := scanOrder(tx.QueryRow("SELECT * FROM paper_orders WHERE id=?", fill.OrderID))
		if err != nil {
			return err
		}
		if order.AllocationID != id {
			return errors.New("fill allocation mismatch")
		}
		key := fmt.Sprintf("manual-%s-%d-%s", id, seq, fill.OrderID)
		if len(key) > 160 {
			key = key[:160]
		}
		if err = s.fillPaper(tx, fill, key); err != nil {
			return err
		}
	}
	if err = s.advanceCursor(tx, id, snapshot, seq, at, symbol, bid, ask); err != nil {
		return err
	}
	return tx.Commit()
}
