package store

import (
	"database/sql"
	"encoding/json"
	"errors"
	"github.com/shopspring/decimal"
	"time"
)

type PaperOrder struct {
	ID           string `json:"id"`
	AllocationID string `json:"allocation_id"`
	InstrumentID string `json:"instrument_id"`
	Side         string `json:"side"`
	Price        string `json:"limit_price"`
	Quantity     string `json:"quantity"`
	Remaining    string `json:"remaining"`
	ReserveRate  string `json:"reserve_rate"`
	Status       string `json:"status"`
	Created      string `json:"created_at"`
}
type PaperFill struct {
	OrderID        string `json:"order_id"`
	InstrumentID   string `json:"instrument_id"`
	Side           string `json:"side"`
	Quantity       string `json:"quantity"`
	Price          string `json:"price"`
	Fee            string `json:"fee"`
	Tax            string `json:"tax"`
	EventID        string `json:"event_id"`
	EventTime      string `json:"event_time"`
	SettlementDate string `json:"settlement_date"`
	RulePack       string `json:"rule_pack_id"`
	Simulated      bool   `json:"simulated"`
	Model          string `json:"model"`
}

func position(tx *sql.Tx, allocation, symbol string) (Position, error) {
	p := Position{AllocationID: allocation, InstrumentID: symbol, Quantity: "0", Settled: "0", AverageCost: "0", SellReserved: "0"}
	err := tx.QueryRow("SELECT quantity,settled,average_cost,sell_reserved FROM positions WHERE allocation_id=? AND instrument_id=?", allocation, symbol).Scan(&p.Quantity, &p.Settled, &p.AverageCost, &p.SellReserved)
	if err == sql.ErrNoRows {
		return p, nil
	}
	return p, err
}
func savePosition(tx *sql.Tx, p Position) error {
	_, err := tx.Exec("INSERT INTO positions VALUES(?,?,?,?,?,?) ON CONFLICT(allocation_id,instrument_id) DO UPDATE SET quantity=excluded.quantity,settled=excluded.settled,average_cost=excluded.average_cost,sell_reserved=excluded.sell_reserved", p.AllocationID, p.InstrumentID, p.Quantity, p.Settled, p.AverageCost, p.SellReserved)
	return err
}
func settleSecurities(tx *sql.Tx, allocation string, day time.Time) error {
	rows, err := tx.Query("SELECT id,instrument_id,quantity FROM security_settlements WHERE allocation_id=? AND due<=? AND done=0 ORDER BY due,id", allocation, day.UTC().Format("2006-01-02"))
	if err != nil {
		return err
	}
	type dueShare struct{ id, instrument, quantity string }
	var matured []dueShare
	for rows.Next() {
		var item dueShare
		if err = rows.Scan(&item.id, &item.instrument, &item.quantity); err != nil {
			rows.Close()
			return err
		}
		matured = append(matured, item)
	}
	if err = rows.Err(); err != nil {
		rows.Close()
		return err
	}
	if err = rows.Close(); err != nil {
		return err
	}
	for _, item := range matured {
		p, err := position(tx, allocation, item.instrument)
		if err != nil {
			return err
		}
		p.Settled = d(p.Settled).Add(d(item.quantity)).String()
		if err = savePosition(tx, p); err != nil {
			return err
		}
		if _, err = tx.Exec("UPDATE security_settlements SET done=1 WHERE id=? AND done=0", item.id); err != nil {
			return err
		}
	}
	return nil
}
func d(v string) decimal.Decimal {
	result, err := decimal.NewFromString(v)
	if err != nil {
		panic("corrupt decimal in local ledger")
	}
	return result
}
func scanOrder(row interface{ Scan(...any) error }) (PaperOrder, error) {
	var v PaperOrder
	err := row.Scan(&v.ID, &v.AllocationID, &v.InstrumentID, &v.Side, &v.Price, &v.Quantity, &v.Remaining, &v.ReserveRate, &v.Status, &v.Created)
	return v, err
}
func (s *Store) PaperOrders(allocation string) ([]PaperOrder, error) {
	rows, err := s.DB.Query("SELECT * FROM paper_orders WHERE allocation_id=? ORDER BY created", allocation)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	result := []PaperOrder{}
	for rows.Next() {
		v, err := scanOrder(rows)
		if err != nil {
			return nil, err
		}
		result = append(result, v)
	}
	return result, rows.Err()
}
func (s *Store) PlacePaper(order PaperOrder, key, controller string) error {
	price, err := amount(order.Price, false)
	if err != nil {
		return err
	}
	qty, err := amount(order.Quantity, false)
	if err != nil {
		return err
	}
	rate, err := amount(order.ReserveRate, true)
	if err != nil || rate.GreaterThan(decimal.NewFromInt(1)) {
		return errors.New("invalid reserve fee rate")
	}
	if order.ID == "" || order.InstrumentID == "" || (order.Side != "buy" && order.Side != "sell") {
		return errors.New("invalid simulated order")
	}
	created, err := time.Parse(time.RFC3339Nano, order.Created)
	if err != nil {
		return errors.New("order timestamp required")
	}
	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	a, err := scanAllocation(tx.QueryRow("SELECT * FROM allocations WHERE id=?", order.AllocationID))
	if err != nil {
		return err
	}
	fresh, err := once(tx, key, "paper_order", a.FundID, a.ID, order)
	if err != nil || !fresh {
		return err
	}
	if a.Mode == "strategy" && (controller == "" || a.Controller != controller || a.Status != "running") {
		return errors.New("allocation has no matching strategy controller")
	}
	if a.Mode == "manual" && controller != "" {
		return errors.New("strategy cannot control manual allocation")
	}
	if a.Mode == "manual" && a.Status != "stopped" {
		return errors.New("reconcile interrupted manual allocation first")
	}
	if a.Mode != "manual" && a.Mode != "strategy" {
		return errors.New("not a paper allocation")
	}
	if err = settleSecurities(tx, a.ID, created); err != nil {
		return err
	}
	cash, reserved := d(a.Cash), d(a.Reserved)
	p, err := position(tx, a.ID, order.InstrumentID)
	if err != nil {
		return err
	}
	if order.Side == "buy" {
		budget := price.Mul(qty).Mul(decimal.NewFromInt(1).Add(rate))
		if budget.GreaterThan(cash) {
			return errors.New("insufficient allocated cash")
		}
		cash = cash.Sub(budget)
		reserved = reserved.Add(budget)
	} else {
		if qty.GreaterThan(d(p.Settled).Sub(d(p.SellReserved))) {
			return errors.New("settled shares unavailable")
		}
		p.SellReserved = d(p.SellReserved).Add(qty).String()
		if err = savePosition(tx, p); err != nil {
			return err
		}
	}
	if _, err = tx.Exec("INSERT INTO paper_orders VALUES(?,?,?,?,?,?,?,?,?,?)", order.ID, a.ID, order.InstrumentID, order.Side, price.String(), qty.String(), qty.String(), rate.String(), "open", order.Created); err != nil {
		return err
	}
	if _, err = tx.Exec("UPDATE allocations SET cash=?,reserved=? WHERE id=?", cash.String(), reserved.String(), a.ID); err != nil {
		return err
	}
	return tx.Commit()
}
func (s *Store) PaperOrderRequest(key string) (PaperOrder, error) {
	var kind, raw string
	var order PaperOrder
	if err := s.DB.QueryRow("SELECT kind,payload FROM ledger WHERE request_key=?", key).Scan(&kind, &raw); err != nil {
		return order, err
	}
	if kind != "paper_order" {
		return order, errors.New("idempotency key belongs to another operation")
	}
	if err := json.Unmarshal([]byte(raw), &order); err != nil {
		return order, err
	}
	return order, nil
}
func (s *Store) FillPaper(fill PaperFill, key string) error {
	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err = s.fillPaper(tx, fill, key); err != nil {
		return err
	}
	return tx.Commit()
}
func (s *Store) fillPaper(tx *sql.Tx, fill PaperFill, key string) error {
	q, err := amount(fill.Quantity, false)
	if err != nil {
		return err
	}
	price, err := amount(fill.Price, false)
	if err != nil {
		return err
	}
	fee, err := amount(fill.Fee, true)
	if err != nil {
		return err
	}
	tax, err := amount(fill.Tax, true)
	if err != nil {
		return err
	}
	if !fill.Simulated || fill.EventID == "" {
		return errors.New("simulated event provenance required")
	}
	at, err := time.Parse(time.RFC3339Nano, fill.EventTime)
	if err != nil {
		return err
	}
	settlementDate, err := time.Parse("2006-01-02", fill.SettlementDate)
	if err != nil || settlementDate.Before(time.Date(at.UTC().Year(), at.UTC().Month(), at.UTC().Day(), 0, 0, 0, 0, time.UTC)) {
		return errors.New("invalid settlement date")
	}
	tradeDate := time.Date(at.UTC().Year(), at.UTC().Month(), at.UTC().Day(), 0, 0, 0, 0, time.UTC)
	if fill.Side == "sell" && settlementDate.After(tradeDate) {
		return errors.New("non-immediate cash settlement requires verified availability-time model; capability blocked")
	}
	order, err := scanOrder(tx.QueryRow("SELECT * FROM paper_orders WHERE id=?", fill.OrderID))
	if err != nil {
		return err
	}
	a, err := scanAllocation(tx.QueryRow("SELECT * FROM allocations WHERE id=?", order.AllocationID))
	if err != nil {
		return err
	}
	fresh, err := once(tx, key, "paper_fill", a.FundID, a.ID, fill)
	if err != nil || !fresh {
		return err
	}
	if err = settleSecurities(tx, a.ID, at); err != nil {
		return err
	}
	created, err := time.Parse(time.RFC3339Nano, order.Created)
	if err != nil {
		return err
	}
	if !at.After(created) || order.Status != "open" || q.GreaterThan(d(order.Remaining)) || fill.Side != order.Side || fill.InstrumentID != order.InstrumentID {
		return errors.New("fill violates order/time/remaining constraints")
	}
	p, err := position(tx, a.ID, order.InstrumentID)
	if err != nil {
		return err
	}
	cash, reserved := d(a.Cash), d(a.Reserved)
	gross := price.Mul(q)
	if order.Side == "buy" {
		if price.GreaterThan(d(order.Price)) {
			return errors.New("buy fill above limit")
		}
		release := d(order.Price).Mul(q).Mul(decimal.NewFromInt(1).Add(d(order.ReserveRate)))
		cost := gross.Add(fee).Add(tax)
		if cost.GreaterThan(release) || release.GreaterThan(reserved) {
			return errors.New("fill costs exceed reservation")
		}
		cash = cash.Add(release.Sub(cost))
		reserved = reserved.Sub(release)
		oldQty := d(p.Quantity)
		total := oldQty.Add(q)
		p.AverageCost = d(p.AverageCost).Mul(oldQty).Add(cost).Div(total).String()
		p.Quantity = total.String()
		if settlementDate.After(tradeDate) {
			if _, err = tx.Exec("INSERT INTO security_settlements VALUES(?,?,?,?,?,0)", key, a.ID, order.InstrumentID, q.String(), settlementDate.Format("2006-01-02")); err != nil {
				return err
			}
		} else {
			p.Settled = d(p.Settled).Add(q).String()
		}
	} else {
		if price.LessThan(d(order.Price)) || q.GreaterThan(d(p.Settled)) || q.GreaterThan(d(p.SellReserved)) || fee.Add(tax).GreaterThan(gross) {
			return errors.New("invalid sell fill")
		}
		cash = cash.Add(gross.Sub(fee).Sub(tax))
		p.Quantity = d(p.Quantity).Sub(q).String()
		p.Settled = d(p.Settled).Sub(q).String()
		p.SellReserved = d(p.SellReserved).Sub(q).String()
		if d(p.Quantity).IsZero() {
			p.AverageCost = "0"
		}
	}
	if err = savePosition(tx, p); err != nil {
		return err
	}
	remaining := d(order.Remaining).Sub(q)
	status := "open"
	if remaining.IsZero() {
		status = "filled"
	}
	if _, err = tx.Exec("UPDATE paper_orders SET remaining=?,status=? WHERE id=?", remaining.String(), status, order.ID); err != nil {
		return err
	}
	if _, err = tx.Exec("UPDATE allocations SET cash=?,reserved=? WHERE id=?", cash.String(), reserved.String(), a.ID); err != nil {
		return err
	}
	return nil
}
func (s *Store) CancelPaper(id, key string) error {
	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if err = s.cancelPaper(tx, id, key); err != nil {
		return err
	}
	return tx.Commit()
}
func (s *Store) cancelPaper(tx *sql.Tx, id, key string) error {
	order, err := scanOrder(tx.QueryRow("SELECT * FROM paper_orders WHERE id=?", id))
	if err != nil {
		return err
	}
	a, err := scanAllocation(tx.QueryRow("SELECT * FROM allocations WHERE id=?", order.AllocationID))
	if err != nil {
		return err
	}
	fresh, err := once(tx, key, "paper_cancel", a.FundID, a.ID, map[string]string{"order_id": id})
	if err != nil || !fresh {
		return err
	}
	if order.Status != "open" {
		return errors.New("order is not open")
	}
	cash, reserved := d(a.Cash), d(a.Reserved)
	if order.Side == "buy" {
		release := d(order.Price).Mul(d(order.Remaining)).Mul(decimal.NewFromInt(1).Add(d(order.ReserveRate)))
		reserved = reserved.Sub(release)
		cash = cash.Add(release)
	} else {
		p, err := position(tx, a.ID, order.InstrumentID)
		if err != nil {
			return err
		}
		p.SellReserved = d(p.SellReserved).Sub(d(order.Remaining)).String()
		if err = savePosition(tx, p); err != nil {
			return err
		}
	}
	if _, err = tx.Exec("UPDATE allocations SET cash=?,reserved=? WHERE id=?", cash.String(), reserved.String(), a.ID); err != nil {
		return err
	}
	if _, err = tx.Exec("UPDATE paper_orders SET status='cancelled',remaining='0' WHERE id=?", id); err != nil {
		return err
	}
	return nil
}
