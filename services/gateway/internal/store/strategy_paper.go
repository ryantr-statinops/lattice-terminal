package store

import (
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
)

type StrategyPaperMutation struct {
	Type    string          `json:"type"`
	Payload json.RawMessage `json:"payload"`
}

type strategyPaperStepRecord struct {
	Allocation string                  `json:"allocation_id"`
	Snapshot   string                  `json:"snapshot_id"`
	After      int64                   `json:"after_sequence"`
	Sequence   int64                   `json:"sequence"`
	Time       string                  `json:"event_time"`
	Instrument string                  `json:"instrument_id"`
	Bid        string                  `json:"bid"`
	Ask        string                  `json:"ask"`
	Mutations  []StrategyPaperMutation `json:"mutations"`
}

// ApplyStrategyStep commits all paper mutations caused by one market event and
// its cursor together, so recovery can never observe a fill without its event.
func (s *Store) ApplyStrategyStep(allocation, controller, key, snapshot string, after, sequence int64, at, instrument, bid, ask string, mutations []StrategyPaperMutation) error {
	if allocation == "" || controller == "" || key == "" || snapshot == "" || sequence != after+1 {
		return errors.New("invalid strategy paper step")
	}
	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	a, err := scanAllocation(tx.QueryRow("SELECT * FROM allocations WHERE id=?", allocation))
	if err != nil {
		return err
	}
	if a.Mode != "strategy" || a.Controller != controller || a.Status != "running" {
		return errors.New("strategy allocation lease missing")
	}
	var existingKey string
	err = tx.QueryRow("SELECT event_key FROM paper_steps WHERE allocation_id=? AND snapshot=? AND sequence=?", allocation, snapshot, sequence).Scan(&existingKey)
	if err == nil {
		if existingKey != key {
			return errors.New("conflicting paper step for an already committed market event")
		}
		return tx.Commit()
	}
	if err != sql.ErrNoRows {
		return err
	}
	var cursorSnapshot string
	var cursor int64
	err = tx.QueryRow("SELECT snapshot,sequence FROM paper_cursors WHERE allocation_id=?", allocation).Scan(&cursorSnapshot, &cursor)
	if err != nil && err != sql.ErrNoRows {
		return err
	}
	if cursor != after || (cursorSnapshot != "" && cursorSnapshot != snapshot) {
		return errors.New("paper cursor/source mismatch; reconcile before continuing")
	}
	for index, mutation := range mutations {
		mutationKey := fmt.Sprintf("%s-%d", key, index)
		switch mutation.Type {
		case "paper_order":
			var order PaperOrder
			if err = json.Unmarshal(mutation.Payload, &order); err != nil {
				return err
			}
			if order.AllocationID != allocation {
				return errors.New("paper order allocation mismatch")
			}
			if err = s.placePaper(tx, order, mutationKey, controller); err != nil {
				return err
			}
		case "paper_fill":
			var fill PaperFill
			if err = json.Unmarshal(mutation.Payload, &fill); err != nil {
				return err
			}
			order, scanErr := scanOrder(tx.QueryRow("SELECT * FROM paper_orders WHERE id=?", fill.OrderID))
			if scanErr != nil {
				return scanErr
			}
			if order.AllocationID != allocation {
				return errors.New("paper fill allocation mismatch")
			}
			if err = s.fillPaper(tx, fill, mutationKey); err != nil {
				return err
			}
		default:
			return fmt.Errorf("unsupported strategy paper mutation %q", mutation.Type)
		}
	}
	if err = s.advanceCursor(tx, allocation, snapshot, sequence, at, instrument, bid, ask); err != nil {
		return err
	}
	step := strategyPaperStepRecord{Allocation: allocation, Snapshot: snapshot, After: after, Sequence: sequence, Time: at, Instrument: instrument, Bid: bid, Ask: ask, Mutations: mutations}
	record, err := json.Marshal(step)
	if err != nil {
		return err
	}
	if _, err = tx.Exec("INSERT INTO paper_steps(allocation_id,snapshot,sequence,event_key,payload,created) VALUES(?,?,?,?,?,?)", allocation, snapshot, sequence, key, string(record), Now()); err != nil {
		return err
	}
	return tx.Commit()
}
