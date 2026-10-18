package marketdata

import "time"

const (
	VenueBinance = "binance"
	MarketSpot   = "spot"
	SourceFixture = "fixture-only"
	SchemaVersion = "1"
	AdapterVersion = "marketdata-v1"
)

type Interval string

const (
	Interval15m Interval = "15m"
	Interval1h  Interval = "1h"
	Interval1d  Interval = "1d"
)

func (i Interval) Duration() time.Duration {
	switch i {
	case Interval15m:
		return 15 * time.Minute
	case Interval1h:
		return time.Hour
	case Interval1d:
		return 24 * time.Hour
	default:
		return 0
	}
}

func (i Interval) Valid() bool { return i.Duration() != 0 }

type TimestampUnit string

const (
	TimestampMilliseconds  TimestampUnit = "millisecond"
	TimestampMicroseconds TimestampUnit = "microsecond"
)

type Candle struct {
	Venue                  string        `json:"venue"`
	MarketType             string        `json:"market_type"`
	NativeSymbol           string        `json:"native_symbol"`
	Interval               Interval      `json:"interval"`
	OpenTimeMS             int64         `json:"open_time_ms"`
	CloseTimeMS            int64         `json:"close_time_ms"`
	IsClosed               bool          `json:"is_closed"`
	Open                   string        `json:"open"`
	High                   string        `json:"high"`
	Low                    string        `json:"low"`
	Close                  string        `json:"close"`
	BaseVolume             string        `json:"base_volume"`
	QuoteVolume            string        `json:"quote_volume,omitempty"`
	TradeCount             int64         `json:"trade_count,omitempty"`
	SourceID               string        `json:"source_id"`
	SourceObjectID         string        `json:"source_object_id"`
	SourceTimestampUnit    TimestampUnit `json:"source_timestamp_unit"`
	SourceOpenTimestamp    int64         `json:"source_open_timestamp"`
	SourceCloseTimestamp   int64         `json:"source_close_timestamp"`
	AvailableAt            time.Time     `json:"available_at"`
	RevisionID             string        `json:"revision_id"`
}

func (c Candle) NaturalKey() string {
	return c.Venue + "|" + c.MarketType + "|" + c.NativeSymbol + "|" + string(c.Interval) + "|" + time.UnixMilli(c.OpenTimeMS).UTC().Format(time.RFC3339Nano)
}

type InputObject struct {
	SourceID       string        `json:"source_id"`
	ObjectID       string        `json:"object_id"`
	SHA256         string        `json:"sha256"`
	TimestampUnit  TimestampUnit `json:"timestamp_unit"`
	RetrievedAt    time.Time     `json:"retrieved_at"`
	InputPath      string        `json:"input_path,omitempty"`
}

type Gap struct {
	FromOpenTimeMS int64 `json:"from_open_time_ms"`
	ToOpenTimeMS   int64 `json:"to_open_time_ms"`
	MissingBars    int64 `json:"missing_bars"`
}

type Conflict struct {
	NaturalKey string   `json:"natural_key"`
	RevisionIDs []string `json:"revision_ids"`
	SourceIDs []string `json:"source_ids"`
}

type Manifest struct {
	SchemaVersion       string        `json:"schema_version"`
	SnapshotID          string        `json:"snapshot_id"`
	SnapshotVersion     string        `json:"snapshot_version"`
	CreatedAt           time.Time     `json:"created_at"`
	SourceIDs           []string      `json:"source_ids"`
	Inputs              []InputObject `json:"inputs"`
	AdapterVersion      string        `json:"adapter_version"`
	Venue               string        `json:"venue"`
	MarketType          string        `json:"market_type"`
	NativeSymbol        string        `json:"native_symbol"`
	Interval            Interval      `json:"interval"`
	RangeStartMS        int64         `json:"range_start_ms"`
	RangeEndMS          int64         `json:"range_end_ms"`
	RowCount            int           `json:"row_count"`
	TimestampPolicy     string        `json:"timestamp_policy"`
	ClosedBarPolicy     string        `json:"closed_bar_policy"`
	RevisionCount       int           `json:"revision_count"`
	ConflictCount       int           `json:"conflict_count"`
	Gaps                []Gap         `json:"gaps"`
	QualityPassed       bool          `json:"quality_passed"`
	RightsEligible      bool          `json:"rights_eligible"`
	AvailabilityPolicy  string        `json:"availability_policy"`
}

type QualityReport struct {
	InputRows       int      `json:"input_rows"`
	AcceptedRows    int      `json:"accepted_rows"`
	DuplicateRows   int      `json:"duplicate_rows"`
	RevisionRows    int      `json:"revision_rows"`
	RejectedRows    int      `json:"rejected_rows"`
	ConflictCount   int      `json:"conflict_count"`
	Gaps            []Gap    `json:"gaps"`
	Errors          []string `json:"errors"`
}
