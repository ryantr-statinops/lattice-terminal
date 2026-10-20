package store

import "errors"

// ReconcileInterrupted cancels unfilled remainder, preserving cash, positions,
// cursor and unsettled obligations. It does not infer any missing fills.
func (s *Store) ReconcileInterrupted(id, key string) error {
	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	a, err := scanAllocation(tx.QueryRow("SELECT * FROM allocations WHERE id=?", id))
	if err != nil {
		return err
	}
	fresh, err := once(tx, key, "reconcile", a.FundID, id, map[string]string{"allocation": id})
	if err != nil || !fresh {
		return err
	}
	if a.Status != "interrupted" || a.Controller != "" {
		return errors.New("only interrupted, uncontrolled allocations can be reconciled")
	}
	rows, err := tx.Query("SELECT id FROM paper_orders WHERE allocation_id=? AND status='open'", id)
	if err != nil {
		return err
	}
	ids := []string{}
	for rows.Next() {
		var v string
		if err = rows.Scan(&v); err != nil {
			rows.Close()
			return err
		}
		ids = append(ids, v)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	for _, order := range ids {
		if err = s.cancelPaper(tx, order, "recovery-"+order); err != nil {
			return err
		}
	}
	var reserved, unsettled string
	if err = tx.QueryRow("SELECT reserved,unsettled FROM allocations WHERE id=?", id).Scan(&reserved, &unsettled); err != nil {
		return err
	}
	if !d(reserved).IsZero() || !d(unsettled).IsZero() {
		return errors.New("unresolved reserved/unsettled obligations; manual investigation required")
	}
	if _, err = tx.Exec("UPDATE allocations SET status='stopped' WHERE id=?", id); err != nil {
		return err
	}
	return tx.Commit()
}
