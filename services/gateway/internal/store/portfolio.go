package store

import (
	"crypto/sha256"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/shopspring/decimal"
	"io"
	"regexp"
	"sort"
	"strings"
	"time"
	"unicode/utf8"
)

var TradeColumns = []string{"trade_id", "event_time", "instrument_id", "side", "quantity", "price", "fee", "tax", "settled"}
var recordedIdentifier = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$`)

type RecordedTrade struct {
	ID         string `json:"trade_id"`
	Time       string `json:"event_time"`
	Instrument string `json:"instrument_id"`
	Side       string `json:"side"`
	Quantity   string `json:"quantity"`
	Price      string `json:"price"`
	Fee        string `json:"fee"`
	Tax        string `json:"tax"`
	Settled    bool   `json:"settled"`
}
type ImportPreview struct {
	Hash   string          `json:"hash"`
	Rows   []RecordedTrade `json:"rows"`
	Errors []string        `json:"errors"`
}

func PreviewCSV(fund, text string) ImportPreview {
	sum := sha256.Sum256([]byte(fund + "\n" + text))
	result := ImportPreview{Hash: hex.EncodeToString(sum[:]), Rows: []RecordedTrade{}, Errors: []string{}}
	if !utf8.ValidString(text) || len(text) > 2*1024*1024 {
		result.Errors = append(result.Errors, "CSV must be UTF-8 and at most 2 MiB")
		return result
	}
	reader := csv.NewReader(strings.NewReader(strings.TrimPrefix(text, "\ufeff")))
	reader.FieldsPerRecord = len(TradeColumns)
	headers, err := reader.Read()
	if err != nil || strings.Join(headers, ",") != strings.Join(TradeColumns, ",") {
		result.Errors = append(result.Errors, "Expected header: "+strings.Join(TradeColumns, ","))
		return result
	}
	seen := map[string]bool{}
	for index := 2; ; index++ {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			result.Errors = append(result.Errors, fmt.Sprintf("row %d: invalid CSV width or quoting", index))
			continue
		}
		v := RecordedTrade{ID: record[0], Time: record[1], Instrument: record[2], Side: record[3], Quantity: record[4], Price: record[5], Fee: record[6], Tax: record[7], Settled: record[8] == "true"}
		if err = validateRecorded(v); err != nil {
			result.Errors = append(result.Errors, fmt.Sprintf("row %d: %s", index, err))
			continue
		}
		if seen[v.ID] {
			result.Errors = append(result.Errors, fmt.Sprintf("row %d: duplicate trade_id", index))
			continue
		}
		seen[v.ID] = true
		result.Rows = append(result.Rows, v)
		if len(result.Rows) > 5000 {
			result.Errors = append(result.Errors, "maximum 5000 trades per import")
			break
		}
	}
	if len(result.Rows) == 0 {
		result.Errors = append(result.Errors, "no valid trades")
	}
	return result
}
func validateRecorded(v RecordedTrade) error {
	if !recordedIdentifier.MatchString(v.ID) || len(v.ID) > 100 || !recordedIdentifier.MatchString(v.Instrument) || (v.Side != "buy" && v.Side != "sell") {
		return errors.New("trade id/instrument/side required")
	}
	if !v.Settled {
		return errors.New("only explicitly settled user-recorded trades supported")
	}
	if _, err := time.Parse(time.RFC3339Nano, v.Time); err != nil {
		return errors.New("event_time requires UTC/offset ISO timestamp")
	}
	for _, value := range []struct {
		Text string
		Zero bool
	}{{v.Quantity, false}, {v.Price, false}, {v.Fee, true}, {v.Tax, true}} {
		if _, err := amount(value.Text, value.Zero); err != nil {
			return err
		}
	}
	return nil
}
func (s *Store) RecordTrades(fund string, trades []RecordedTrade) error {
	if len(trades) == 0 {
		return errors.New("no trades")
	}
	for _, trade := range trades {
		if err := validateRecorded(trade); err != nil {
			return err
		}
	}
	trades = append([]RecordedTrade(nil), trades...)
	sort.SliceStable(trades, func(i, j int) bool {
		a, _ := time.Parse(time.RFC3339Nano, trades[i].Time)
		b, _ := time.Parse(time.RFC3339Nano, trades[j].Time)
		return a.Before(b)
	})
	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var kind, cash string
	if err = tx.QueryRow("SELECT kind,cash FROM funds WHERE id=? AND archived=0", fund).Scan(&kind, &cash); err != nil {
		return err
	}
	if kind != "tracking" {
		return errors.New("recorded trades require a tracking fund, not a paper book")
	}
	book := "tracking-" + fund
	if _, err = tx.Exec("INSERT OR IGNORE INTO allocations VALUES(?,?,?,'tracking','0','0','0','0','stopped','')", book, fund, "Recorded trade ledger"); err != nil {
		return err
	}
	balance := d(cash)
	var latest time.Time
	rows, err := tx.Query("SELECT payload FROM ledger WHERE fund_id=? AND kind='record_trade'", fund)
	if err != nil {
		return err
	}
	for rows.Next() {
		var raw string
		var previous RecordedTrade
		if err = rows.Scan(&raw); err != nil {
			rows.Close()
			return err
		}
		if err = json.Unmarshal([]byte(raw), &previous); err != nil {
			rows.Close()
			return err
		}
		stamp, parseErr := time.Parse(time.RFC3339Nano, previous.Time)
		if parseErr != nil {
			rows.Close()
			return parseErr
		}
		if stamp.After(latest) {
			latest = stamp
		}
	}
	if err = rows.Err(); err != nil {
		rows.Close()
		return err
	}
	rows.Close()
	for _, trade := range trades {
		sum := sha256.Sum256([]byte(fund + "/" + trade.ID))
		key := hex.EncodeToString(sum[:])
		fresh, err := once(tx, key, "record_trade", fund, book, trade)
		if err != nil {
			return err
		}
		if !fresh {
			continue
		}
		stamp, _ := time.Parse(time.RFC3339Nano, trade.Time)
		if stamp.Before(latest) {
			return errors.New("backdated trades require a separate tracking fund and chronological reimport")
		}
		latest = stamp
		p, err := position(tx, book, trade.Instrument)
		if err != nil {
			return err
		}
		quantity, price, fee, tax := d(trade.Quantity), d(trade.Price), d(trade.Fee), d(trade.Tax)
		gross := quantity.Mul(price)
		if trade.Side == "buy" {
			cost := gross.Add(fee).Add(tax)
			if cost.GreaterThan(balance) {
				return errors.New("recorded buy exceeds tracking cash")
			}
			old := d(p.Quantity)
			total := old.Add(quantity)
			p.AverageCost = d(p.AverageCost).Mul(old).Add(cost).Div(total).String()
			p.Quantity = total.String()
			p.Settled = total.String()
			balance = balance.Sub(cost)
		} else {
			if quantity.GreaterThan(d(p.Settled)) || fee.Add(tax).GreaterThan(gross) {
				return errors.New("recorded sell exceeds settled position or proceeds")
			}
			balance = balance.Add(gross.Sub(fee).Sub(tax))
			p.Quantity = d(p.Quantity).Sub(quantity).String()
			p.Settled = p.Quantity
			if d(p.Quantity).IsZero() {
				p.AverageCost = "0"
			}
		}
		if err = savePosition(tx, p); err != nil {
			return err
		}
	}
	if _, err = tx.Exec("UPDATE funds SET cash=? WHERE id=?", balance.String(), fund); err != nil {
		return err
	}
	return tx.Commit()
}

type PositionValue struct {
	Position
	Price  *string `json:"price"`
	Value  *string `json:"market_value"`
	AsOf   string  `json:"as_of"`
	Source string  `json:"source"`
}
type FundValue struct {
	Fund
	KnownValue  string       `json:"known_subtotal"`
	NAV         *string      `json:"nav"`
	NetFlows    string       `json:"net_external_flows"`
	PnL         *string      `json:"pnl"`
	Missing     []string     `json:"missing_prices"`
	Allocations []Allocation `json:"allocations"`
}

func (s *Store) Portfolio() (map[string]any, error) {
	tx, err := s.DB.Begin()
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	funds, err := listFunds(tx)
	if err != nil {
		return nil, err
	}
	allocations, err := listAllocations(tx)
	if err != nil {
		return nil, err
	}
	positions, err := listPositions(tx)
	if err != nil {
		return nil, err
	}
	type mark struct{ Price, Time, Source string }
	marks := map[string]mark{}
	rows, err := tx.Query("SELECT instrument_id,price,event_time,source FROM marks")
	if err != nil {
		return nil, err
	}
	for rows.Next() {
		var id string
		var v mark
		if err = rows.Scan(&id, &v.Price, &v.Time, &v.Source); err != nil {
			rows.Close()
			return nil, err
		}
		marks[id] = v
	}
	rows.Close()
	external := map[string]decimal.Decimal{}
	rows, err = tx.Query("SELECT kind,fund_id,payload FROM ledger WHERE kind IN ('create_fund','deposit','withdraw','transfer')")
	if err != nil {
		return nil, err
	}
	for rows.Next() {
		var kind, fund, raw string
		if err = rows.Scan(&kind, &fund, &raw); err != nil {
			rows.Close()
			return nil, err
		}
		var payload map[string]string
		json.Unmarshal([]byte(raw), &payload)
		value := payload["amount"]
		if kind == "create_fund" {
			value = payload["capital"]
		}
		switch kind {
		case "create_fund", "deposit":
			external[fund] = external[fund].Add(d(value))
		case "withdraw":
			external[fund] = external[fund].Sub(d(value))
		case "transfer":
			external[payload["from"]] = external[payload["from"]].Sub(d(value))
			external[payload["to"]] = external[payload["to"]].Add(d(value))
		}
	}
	rows.Close()
	books := map[string]string{}
	for _, a := range allocations {
		books[a.ID] = a.FundID
	}
	values := []PositionValue{}
	fundValues := []FundValue{}
	for _, fund := range funds {
		cash := d(fund.Cash)
		children := []Allocation{}
		missing := []string{}
		for _, a := range allocations {
			if a.FundID == fund.ID {
				children = append(children, a)
				cash = cash.Add(d(a.Cash)).Add(d(a.Reserved)).Add(d(a.Unsettled))
			}
		}
		for _, position := range positions {
			if books[position.AllocationID] != fund.ID || d(position.Quantity).IsZero() {
				continue
			}
			v := PositionValue{Position: position}
			if mark, ok := marks[position.InstrumentID]; ok {
				price := mark.Price
				value := d(price).Mul(d(position.Quantity)).String()
				v.Price = &price
				v.Value = &value
				v.AsOf = mark.Time
				v.Source = mark.Source
				cash = cash.Add(d(value))
			} else {
				missing = append(missing, position.InstrumentID)
			}
			values = append(values, v)
		}
		entry := FundValue{Fund: fund, KnownValue: cash.String(), NetFlows: external[fund.ID].String(), Missing: missing, Allocations: children}
		if len(missing) == 0 {
			nav := cash.String()
			pnl := cash.Sub(external[fund.ID]).String()
			entry.NAV = &nav
			entry.PnL = &pnl
		}
		fundValues = append(fundValues, entry)
	}
	return map[string]any{"funds": fundValues, "positions": values, "base_currency": "VND", "valuation": "last-observed source-marked prices; not broker balances or live quotes", "cost_basis": "weighted-average"}, nil
}
func (s *Store) RecordedTrades(fund string) ([]RecordedTrade, error) {
	rows, err := s.DB.Query("SELECT payload FROM ledger WHERE fund_id=? AND kind='record_trade' ORDER BY created", fund)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	result := []RecordedTrade{}
	for rows.Next() {
		var raw string
		var v RecordedTrade
		if err = rows.Scan(&raw); err != nil {
			return nil, err
		}
		if err = json.Unmarshal([]byte(raw), &v); err != nil {
			return nil, err
		}
		result = append(result, v)
	}
	return result, rows.Err()
}
