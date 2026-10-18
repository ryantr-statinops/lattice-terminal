package marketdata

import (
	"crypto/sha256"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math/big"
	"strconv"
	"strings"
	"time"
)

type ParseConfig struct {
	Symbol          string
	Interval        Interval
	TimestampUnit   TimestampUnit
	SourceID        string
	SourceObjectID  string
	RetrievedAt     time.Time
	Now             time.Time
}

func (c ParseConfig) validate() error {
	if c.Symbol != "BTCUSDT" && c.Symbol != "ETHUSDT" {
		return fmt.Errorf("unsupported spot symbol %q", c.Symbol)
	}
	if !c.Interval.Valid() {
		return fmt.Errorf("unsupported interval %q", c.Interval)
	}
	if c.TimestampUnit != TimestampMilliseconds && c.TimestampUnit != TimestampMicroseconds {
		return fmt.Errorf("unsupported timestamp unit %q", c.TimestampUnit)
	}
	if c.SourceID == "" || c.SourceObjectID == "" {
		return errors.New("source ID and source object ID are required")
	}
	if c.RetrievedAt.IsZero() || c.Now.IsZero() {
		return errors.New("retrieved-at and clock times are required")
	}
	return nil
}

func ParseArchiveCSV(r io.Reader, cfg ParseConfig) ([]Candle, error) {
	if err := cfg.validate(); err != nil {
		return nil, err
	}
	reader := csv.NewReader(r)
	reader.FieldsPerRecord = 12
	reader.ReuseRecord = false
	var candles []Candle
	line := 0
	for {
		row, err := reader.Read()
		if errors.Is(err, io.EOF) {
			break
		}
		line++
		if err != nil {
			return nil, fmt.Errorf("archive CSV row %d: %w", line, err)
		}
		if line == 1 && isCSVHeader(row[0]) {
			continue
		}
		candle, err := parseKlineFields(row, cfg)
		if err != nil {
			return nil, fmt.Errorf("archive CSV row %d: %w", line, err)
		}
		candles = append(candles, candle)
	}
	if len(candles) == 0 {
		return nil, errors.New("archive CSV contains no candle rows")
	}
	return candles, nil
}

func isCSVHeader(value string) bool {
	value = strings.TrimSpace(strings.ToLower(value))
	return value == "open time" || value == "open_time" || value == "open time (us)"
}

func ParseRESTKlines(r io.Reader, cfg ParseConfig) ([]Candle, error) {
	if err := cfg.validate(); err != nil {
		return nil, err
	}
	decoder := json.NewDecoder(io.LimitReader(r, 64<<20))
	var rows [][]json.RawMessage
	if err := decoder.Decode(&rows); err != nil {
		return nil, fmt.Errorf("invalid REST kline JSON: %w", err)
	}
	var extra any
	if err := decoder.Decode(&extra); err != io.EOF {
		return nil, errors.New("REST input must contain one JSON document")
	}
	if len(rows) == 0 {
		return nil, errors.New("REST response contains no candle rows")
	}
	candles := make([]Candle, 0, len(rows))
	for i, row := range rows {
		if len(row) != 12 {
			return nil, fmt.Errorf("REST kline row %d has %d fields; expected 12", i+1, len(row))
		}
		fields := make([]string, len(row))
		for j := range row {
			value, err := rawScalar(row[j])
			if err != nil {
				return nil, fmt.Errorf("REST kline row %d field %d: %w", i+1, j+1, err)
			}
			fields[j] = value
		}
		candle, err := parseKlineFields(fields, cfg)
		if err != nil {
			return nil, fmt.Errorf("REST kline row %d: %w", i+1, err)
		}
		candles = append(candles, candle)
	}
	return candles, nil
}

func rawScalar(raw json.RawMessage) (string, error) {
	var value string
	if err := json.Unmarshal(raw, &value); err == nil {
		return value, nil
	}
	var number json.Number
	decoder := json.NewDecoder(strings.NewReader(string(raw)))
	decoder.UseNumber()
	if err := decoder.Decode(&number); err != nil {
		return "", errors.New("expected string or number")
	}
	return number.String(), nil
}

func parseKlineFields(fields []string, cfg ParseConfig) (Candle, error) {
	openRaw, err := strconv.ParseInt(strings.TrimSpace(fields[0]), 10, 64)
	if err != nil {
		return Candle{}, errors.New("invalid open timestamp")
	}
	closeRaw, err := strconv.ParseInt(strings.TrimSpace(fields[6]), 10, 64)
	if err != nil {
		return Candle{}, errors.New("invalid close timestamp")
	}
	openMS, err := timestampToMilliseconds(openRaw, cfg.TimestampUnit)
	if err != nil {
		return Candle{}, err
	}
	closeMS, err := timestampToMilliseconds(closeRaw, cfg.TimestampUnit)
	if err != nil {
		return Candle{}, err
	}
	trades, err := strconv.ParseInt(strings.TrimSpace(fields[8]), 10, 64)
	if err != nil || trades < 0 {
		return Candle{}, errors.New("invalid trade count")
	}

	candle := Candle{
		Venue: VenueBinance, MarketType: MarketSpot, NativeSymbol: cfg.Symbol, Interval: cfg.Interval,
		OpenTimeMS: openMS, CloseTimeMS: closeMS, IsClosed: closeMS < cfg.Now.UTC().UnixMilli(),
		Open: strings.TrimSpace(fields[1]), High: strings.TrimSpace(fields[2]), Low: strings.TrimSpace(fields[3]), Close: strings.TrimSpace(fields[4]),
		BaseVolume: strings.TrimSpace(fields[5]), QuoteVolume: strings.TrimSpace(fields[7]), TradeCount: trades,
		SourceID: cfg.SourceID, SourceObjectID: cfg.SourceObjectID, SourceTimestampUnit: cfg.TimestampUnit,
		SourceOpenTimestamp: openRaw, SourceCloseTimestamp: closeRaw, AvailableAt: cfg.RetrievedAt.UTC(),
	}
	if err := validateCandle(candle); err != nil {
		return Candle{}, err
	}
	candle.RevisionID = revisionID(candle)
	return candle, nil
}

func timestampToMilliseconds(value int64, unit TimestampUnit) (int64, error) {
	switch unit {
	case TimestampMilliseconds:
		return value, nil
	case TimestampMicroseconds:
		return value / 1000, nil
	default:
		return 0, fmt.Errorf("unsupported timestamp unit %q", unit)
	}
}

func revisionID(c Candle) string {
	payload := strings.Join([]string{
		c.NaturalKey(), c.Open, c.High, c.Low, c.Close, c.BaseVolume, c.QuoteVolume, strconv.FormatInt(c.TradeCount, 10),
	}, "|")
	hash := sha256.Sum256([]byte(payload))
	return hex.EncodeToString(hash[:])
}

func validateCandle(c Candle) error {
	if c.Venue != VenueBinance || c.MarketType != MarketSpot || (c.NativeSymbol != "BTCUSDT" && c.NativeSymbol != "ETHUSDT") || !c.Interval.Valid() {
		return errors.New("unsupported candle identity")
	}
	durationMS := c.Interval.Duration().Milliseconds()
	if c.OpenTimeMS < 0 || c.CloseTimeMS != c.OpenTimeMS+durationMS-1 || c.OpenTimeMS%durationMS != 0 {
		return errors.New("candle timestamps do not match interval boundaries")
	}
	open, err := parseDecimal(c.Open)
	if err != nil { return fmt.Errorf("invalid open price: %w", err) }
	high, err := parseDecimal(c.High)
	if err != nil { return fmt.Errorf("invalid high price: %w", err) }
	low, err := parseDecimal(c.Low)
	if err != nil { return fmt.Errorf("invalid low price: %w", err) }
	closeValue, err := parseDecimal(c.Close)
	if err != nil { return fmt.Errorf("invalid close price: %w", err) }
	baseVolume, err := parseDecimal(c.BaseVolume)
	if err != nil { return fmt.Errorf("invalid base volume: %w", err) }
	quoteVolume, err := parseDecimal(c.QuoteVolume)
	if err != nil { return fmt.Errorf("invalid quote volume: %w", err) }
	zero := new(big.Rat)
	if high.Cmp(low) < 0 || high.Cmp(open) < 0 || high.Cmp(closeValue) < 0 || low.Cmp(open) > 0 || low.Cmp(closeValue) > 0 || baseVolume.Cmp(zero) < 0 || quoteVolume.Cmp(zero) < 0 || c.TradeCount < 0 {
		return errors.New("candle OHLCV invariants failed")
	}
	return nil
}

func parseDecimal(value string) (*big.Rat, error) {
	if value == "" || strings.TrimSpace(value) != value || strings.ContainsAny(value, "eE+") {
		return nil, errors.New("decimal must be a plain non-negative base-10 value")
	}
	parts := strings.Split(value, ".")
	if len(parts) > 2 || parts[0] == "" {
		return nil, errors.New("invalid decimal syntax")
	}
	for _, part := range parts {
		if part == "" && len(parts) == 2 || !allDigits(part) {
			return nil, errors.New("invalid decimal syntax")
		}
	}
	number, ok := new(big.Rat).SetString(value)
	if !ok || number.Sign() < 0 {
		return nil, errors.New("invalid non-negative decimal")
	}
	return number, nil
}

func allDigits(value string) bool {
	if value == "" { return false }
	for _, r := range value { if r < '0' || r > '9' { return false } }
	return true
}
