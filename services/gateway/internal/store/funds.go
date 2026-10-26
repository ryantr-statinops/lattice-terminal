package store

import (
	"database/sql"
	"encoding/json"
	"errors"
	"github.com/shopspring/decimal"
	"kestrel-terminal/gateway/internal/host"
	"strings"
)

type Fund struct {
	ID       string `json:"id"`
	Name     string `json:"name"`
	Kind     string `json:"kind"`
	Currency string `json:"currency"`
	Cash     string `json:"unallocated_cash"`
	Archived bool   `json:"archived"`
}
type Allocation struct {
	ID         string `json:"id"`
	FundID     string `json:"fund_id"`
	Name       string `json:"name"`
	Mode       string `json:"mode"`
	Capital    string `json:"net_contributed"`
	Cash       string `json:"cash"`
	Reserved   string `json:"reserved"`
	Unsettled  string `json:"unsettled"`
	Status     string `json:"status"`
	Controller string `json:"controller_run_id"`
}
type Position struct {
	AllocationID string `json:"allocation_id"`
	InstrumentID string `json:"instrument_id"`
	Quantity     string `json:"quantity"`
	Settled      string `json:"settled_quantity"`
	AverageCost  string `json:"average_cost"`
	SellReserved string `json:"sell_reserved"`
}

func (s *Store) financeSchema() error {
	_, err := s.DB.Exec(`CREATE TABLE IF NOT EXISTS funds(id TEXT PRIMARY KEY,name TEXT NOT NULL,kind TEXT NOT NULL,currency TEXT NOT NULL,cash TEXT NOT NULL,archived INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS allocations(id TEXT PRIMARY KEY,fund_id TEXT NOT NULL REFERENCES funds(id),name TEXT NOT NULL,mode TEXT NOT NULL,capital TEXT NOT NULL,cash TEXT NOT NULL,reserved TEXT NOT NULL,unsettled TEXT NOT NULL,status TEXT NOT NULL,controller TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ledger(id TEXT PRIMARY KEY,request_key TEXT NOT NULL UNIQUE,kind TEXT NOT NULL,fund_id TEXT NOT NULL,allocation_id TEXT NOT NULL,payload TEXT NOT NULL,created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS positions(allocation_id TEXT NOT NULL REFERENCES allocations(id),instrument_id TEXT NOT NULL,quantity TEXT NOT NULL,settled TEXT NOT NULL,average_cost TEXT NOT NULL,sell_reserved TEXT NOT NULL,PRIMARY KEY(allocation_id,instrument_id));
CREATE TABLE IF NOT EXISTS security_settlements(id TEXT PRIMARY KEY,allocation_id TEXT NOT NULL REFERENCES allocations(id),instrument_id TEXT NOT NULL,quantity TEXT NOT NULL,due TEXT NOT NULL,done INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS paper_orders(id TEXT PRIMARY KEY,allocation_id TEXT NOT NULL REFERENCES allocations(id),instrument_id TEXT NOT NULL,side TEXT NOT NULL,price TEXT NOT NULL,quantity TEXT NOT NULL,remaining TEXT NOT NULL,reserve_rate TEXT NOT NULL,status TEXT NOT NULL,created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS settlements(id TEXT PRIMARY KEY,allocation_id TEXT NOT NULL REFERENCES allocations(id),instrument_id TEXT NOT NULL,quantity TEXT NOT NULL,cash TEXT NOT NULL,due TEXT NOT NULL,done INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS paper_cursors(allocation_id TEXT PRIMARY KEY REFERENCES allocations(id),snapshot TEXT NOT NULL,sequence INTEGER NOT NULL,event_time TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS marks(instrument_id TEXT PRIMARY KEY,price TEXT NOT NULL,event_time TEXT NOT NULL,source TEXT NOT NULL);
UPDATE allocations SET status='interrupted',controller='' WHERE status='running';`)
	return err
}
func amount(value string, zero bool) (decimal.Decimal, error) {
	if len(value) > 80 || strings.ContainsAny(value, "eE+") {
		return decimal.Zero, errors.New("use a plain decimal string of at most 80 characters")
	}
	v, err := decimal.NewFromString(value)
	if err != nil || v.IsNegative() || (!zero && v.IsZero()) {
		return decimal.Zero, errors.New("positive finite decimal required")
	}
	if v.Exponent() < -8 || v.Exponent() > 40 {
		return decimal.Zero, errors.New("decimal precision exceeds supported range")
	}
	return v, nil
}
func once(tx *sql.Tx, key, kind, fund, allocation string, payload any) (bool, error) {
	if len(key) < 1 || len(key) > 160 {
		return false, errors.New("request_key required (maximum 160 characters)")
	}
	raw, err := json.Marshal(payload)
	if err != nil {
		return false, err
	}
	var oldKind, old string
	err = tx.QueryRow("SELECT kind,payload FROM ledger WHERE request_key=?", key).Scan(&oldKind, &old)
	if err == nil {
		if oldKind != kind || old != string(raw) {
			return false, errors.New("idempotency key reused for different operation")
		}
		return false, nil
	}
	if err != sql.ErrNoRows {
		return false, err
	}
	_, err = tx.Exec("INSERT INTO ledger VALUES(?,?,?,?,?,?,?)", host.Token(), key, kind, fund, allocation, string(raw), Now())
	return true, err
}
func (s *Store) Funds() ([]Fund, error) {
	return listFunds(s.DB)
}

type queryer interface {
	Query(string, ...any) (*sql.Rows, error)
}

func listFunds(db queryer) ([]Fund, error) {
	rows, err := db.Query("SELECT id,name,kind,currency,cash,archived FROM funds ORDER BY name")
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	result := []Fund{}
	for rows.Next() {
		var v Fund
		if err = rows.Scan(&v.ID, &v.Name, &v.Kind, &v.Currency, &v.Cash, &v.Archived); err != nil {
			return nil, err
		}
		result = append(result, v)
	}
	return result, rows.Err()
}
func (s *Store) CreateFund(name, kind, capital, key string) (string, error) {
	name = strings.TrimSpace(name)
	if len(name) < 1 || len(name) > 120 || (kind != "paper" && kind != "tracking") {
		return "", errors.New("valid fund name and kind required")
	}
	value, err := amount(capital, true)
	if err != nil {
		return "", err
	}
	tx, err := s.DB.Begin()
	if err != nil {
		return "", err
	}
	defer tx.Rollback()
	payload := map[string]string{"name": name, "kind": kind, "capital": capital}
	var prior string
	if tx.QueryRow("SELECT fund_id FROM ledger WHERE request_key=?", key).Scan(&prior) == nil {
		ok, err := once(tx, key, "create_fund", prior, "", payload)
		if err != nil {
			return "", err
		}
		if !ok {
			return prior, nil
		}
	}
	id := host.Token()
	if _, err = tx.Exec("INSERT INTO funds(id,name,kind,currency,cash) VALUES(?,?,?,'VND',?)", id, name, kind, value.String()); err != nil {
		return "", err
	}
	if _, err = once(tx, key, "create_fund", id, "", payload); err != nil {
		return "", err
	}
	return id, tx.Commit()
}
func (s *Store) CashFlow(fund, kind, value, key string) error {
	v, err := amount(value, false)
	if err != nil {
		return err
	}
	if kind != "deposit" && kind != "withdraw" {
		return errors.New("unknown flow")
	}
	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	fresh, err := once(tx, key, kind, fund, "", map[string]string{"fund": fund, "amount": value})
	if err != nil || !fresh {
		return err
	}
	var cash string
	var archived bool
	if err = tx.QueryRow("SELECT cash,archived FROM funds WHERE id=?", fund).Scan(&cash, &archived); err != nil {
		return err
	}
	if archived {
		return errors.New("fund archived")
	}
	balance, _ := decimal.NewFromString(cash)
	if kind == "withdraw" {
		if balance.LessThan(v) {
			return errors.New("insufficient unallocated fund cash")
		}
		balance = balance.Sub(v)
	} else {
		balance = balance.Add(v)
	}
	if _, err = tx.Exec("UPDATE funds SET cash=? WHERE id=?", balance.String(), fund); err != nil {
		return err
	}
	return tx.Commit()
}
func (s *Store) Allocate(fund, name, mode, value, key string) (string, error) {
	v, err := amount(value, false)
	if err != nil {
		return "", err
	}
	if strings.TrimSpace(name) == "" || (mode != "manual" && mode != "strategy") {
		return "", errors.New("allocation name/mode required")
	}
	tx, err := s.DB.Begin()
	if err != nil {
		return "", err
	}
	defer tx.Rollback()
	payload := map[string]string{"fund": fund, "name": name, "mode": mode, "amount": value}
	var previous string
	if tx.QueryRow("SELECT allocation_id FROM ledger WHERE request_key=?", key).Scan(&previous) == nil {
		_, err := once(tx, key, "allocate", fund, previous, payload)
		return previous, err
	}
	var cash, kind string
	var archived bool
	if err = tx.QueryRow("SELECT cash,kind,archived FROM funds WHERE id=?", fund).Scan(&cash, &kind, &archived); err != nil {
		return "", err
	}
	if kind != "paper" || archived {
		return "", errors.New("only active paper funds can allocate simulation capital")
	}
	balance, _ := decimal.NewFromString(cash)
	if balance.LessThan(v) {
		return "", errors.New("insufficient unallocated fund cash")
	}
	id := host.Token()
	if _, err = tx.Exec("UPDATE funds SET cash=? WHERE id=?", balance.Sub(v).String(), fund); err != nil {
		return "", err
	}
	if _, err = tx.Exec("INSERT INTO allocations VALUES(?,?,?,?,?,?, '0','0','stopped','')", id, fund, name, mode, v.String(), v.String()); err != nil {
		return "", err
	}
	if _, err = once(tx, key, "allocate", fund, id, payload); err != nil {
		return "", err
	}
	return id, tx.Commit()
}
func scanAllocation(row interface{ Scan(...any) error }) (Allocation, error) {
	var v Allocation
	err := row.Scan(&v.ID, &v.FundID, &v.Name, &v.Mode, &v.Capital, &v.Cash, &v.Reserved, &v.Unsettled, &v.Status, &v.Controller)
	return v, err
}
func (s *Store) Allocation(id string) (Allocation, error) {
	return scanAllocation(s.DB.QueryRow("SELECT * FROM allocations WHERE id=?", id))
}
func (s *Store) Allocations() ([]Allocation, error) {
	return listAllocations(s.DB)
}
func listAllocations(db queryer) ([]Allocation, error) {
	rows, err := db.Query("SELECT * FROM allocations ORDER BY name")
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	result := []Allocation{}
	for rows.Next() {
		v, err := scanAllocation(rows)
		if err != nil {
			return nil, err
		}
		result = append(result, v)
	}
	return result, rows.Err()
}
func (s *Store) Release(id, value, key string) error {
	v, err := amount(value, false)
	if err != nil {
		return err
	}
	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	a, err := scanAllocation(tx.QueryRow("SELECT * FROM allocations WHERE id=?", id))
	if err != nil {
		return err
	}
	fresh, err := once(tx, key, "release", a.FundID, id, map[string]string{"allocation": id, "amount": value})
	if err != nil || !fresh {
		return err
	}
	cash, _ := decimal.NewFromString(a.Cash)
	capital, _ := decimal.NewFromString(a.Capital)
	if a.Status == "running" || cash.LessThan(v) {
		return errors.New("stop controller first; only settled available cash can be released")
	}
	var parent string
	if err = tx.QueryRow("SELECT cash FROM funds WHERE id=?", a.FundID).Scan(&parent); err != nil {
		return err
	}
	p, _ := decimal.NewFromString(parent)
	if _, err = tx.Exec("UPDATE funds SET cash=? WHERE id=?", p.Add(v).String(), a.FundID); err != nil {
		return err
	}
	if _, err = tx.Exec("UPDATE allocations SET cash=?,capital=? WHERE id=?", cash.Sub(v).String(), capital.Sub(v).String(), id); err != nil {
		return err
	}
	return tx.Commit()
}
func (s *Store) Transfer(from, to, value, key string) error {
	v, err := amount(value, false)
	if err != nil {
		return err
	}
	if from == to {
		return errors.New("different funds required")
	}
	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	fresh, err := once(tx, key, "transfer", from, "", map[string]string{"from": from, "to": to, "amount": value})
	if err != nil || !fresh {
		return err
	}
	var left, right, k1, k2 string
	var archived1, archived2 bool
	if err = tx.QueryRow("SELECT cash,kind,archived FROM funds WHERE id=?", from).Scan(&left, &k1, &archived1); err != nil {
		return err
	}
	if err = tx.QueryRow("SELECT cash,kind,archived FROM funds WHERE id=?", to).Scan(&right, &k2, &archived2); err != nil {
		return err
	}
	a, _ := decimal.NewFromString(left)
	b, _ := decimal.NewFromString(right)
	if k1 != k2 || archived1 || archived2 || a.LessThan(v) {
		return errors.New("transfer requires compatible active funds and available cash")
	}
	if _, err = tx.Exec("UPDATE funds SET cash=? WHERE id=?", a.Sub(v).String(), from); err != nil {
		return err
	}
	if _, err = tx.Exec("UPDATE funds SET cash=? WHERE id=?", b.Add(v).String(), to); err != nil {
		return err
	}
	return tx.Commit()
}
func (s *Store) BindController(id, run string) error {
	res, err := s.DB.Exec("UPDATE allocations SET status='running',controller=? WHERE id=? AND mode='strategy' AND status='stopped' AND controller=''", run, id)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n != 1 {
		return errors.New("strategy allocation unavailable or already controlled")
	}
	return nil
}
func (s *Store) EndController(id, run, status string) error {
	_, err := s.DB.Exec("UPDATE allocations SET status=?,controller='' WHERE id=? AND controller=?", status, id, run)
	return err
}
func (s *Store) Positions() ([]Position, error) {
	return listPositions(s.DB)
}
func listPositions(db queryer) ([]Position, error) {
	rows, err := db.Query("SELECT * FROM positions ORDER BY allocation_id,instrument_id")
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	result := []Position{}
	for rows.Next() {
		var p Position
		if err = rows.Scan(&p.AllocationID, &p.InstrumentID, &p.Quantity, &p.Settled, &p.AverageCost, &p.SellReserved); err != nil {
			return nil, err
		}
		result = append(result, p)
	}
	return result, rows.Err()
}
