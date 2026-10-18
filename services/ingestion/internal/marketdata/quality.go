package marketdata

import (
	"errors"
	"fmt"
	"sort"
)

func Reconcile(candles []Candle, symbol string, interval Interval, startMS, endMS int64) (ReconcileResult, error) {
	result := ReconcileResult{Report: QualityReport{InputRows: len(candles)}}
	if symbol != "BTCUSDT" && symbol != "ETHUSDT" {
		return result, fmt.Errorf("unsupported spot symbol %q", symbol)
	}
	duration := interval.Duration().Milliseconds()
	if duration == 0 || startMS < 0 || endMS <= startMS || startMS%duration != 0 || endMS%duration != 0 {
		return result, errors.New("range must be positive and aligned to the selected interval")
	}
	byKey := make(map[string]map[string]Candle)
	for _, candle := range candles {
		if err := validateCandle(candle); err != nil {
			return result, fmt.Errorf("invalid candle %s: %w", candle.NaturalKey(), err)
		}
		if candle.NativeSymbol != symbol || candle.Interval != interval || candle.Venue != VenueBinance || candle.MarketType != MarketSpot {
			return result, errors.New("input contains a candle outside the requested instrument or interval")
		}
		if candle.OpenTimeMS < startMS || candle.OpenTimeMS >= endMS {
			continue
		}
		if !candle.IsClosed {
			result.Report.RejectedRows++
			continue
		}
		key := candle.NaturalKey()
		if byKey[key] == nil {
			byKey[key] = make(map[string]Candle)
		}
		if previous, exists := byKey[key][candle.RevisionID]; exists {
			result.Report.DuplicateRows++
			if candle.SourceID < previous.SourceID || (candle.SourceID == previous.SourceID && candle.SourceObjectID < previous.SourceObjectID) {
				byKey[key][candle.RevisionID] = candle
			}
			continue
		}
		byKey[key][candle.RevisionID] = candle
	}

	openTimes := make([]int64, 0, len(byKey))
	for _, revisions := range byKey {
		var timeMS int64
		var key string
		for _, candle := range revisions {
			timeMS, key = candle.OpenTimeMS, candle.NaturalKey()
			break
		}
		openTimes = append(openTimes, timeMS)
		if len(revisions) > 1 {
			conflict := Conflict{NaturalKey: key}
			for _, candle := range revisions {
				conflict.RevisionIDs = append(conflict.RevisionIDs, candle.RevisionID)
				conflict.SourceIDs = append(conflict.SourceIDs, candle.SourceID)
			}
			sort.Strings(conflict.RevisionIDs)
			sort.Strings(conflict.SourceIDs)
			result.Conflicts = append(result.Conflicts, conflict)
			result.Report.RevisionRows += len(revisions) - 1
			continue
		}
		for _, candle := range revisions {
			result.Candles = append(result.Candles, candle)
		}
	}
	sort.Slice(openTimes, func(i, j int) bool { return openTimes[i] < openTimes[j] })
	sort.Slice(result.Candles, func(i, j int) bool { return result.Candles[i].OpenTimeMS < result.Candles[j].OpenTimeMS })
	sort.Slice(result.Conflicts, func(i, j int) bool { return result.Conflicts[i].NaturalKey < result.Conflicts[j].NaturalKey })
	result.Report.AcceptedRows = len(result.Candles)
	result.Report.ConflictCount = len(result.Conflicts)
	if len(openTimes) > 0 {
		result.Report.LatestClosedOpenTimeMS = openTimes[len(openTimes)-1]
	}
	result.Report.Gaps = calculateGaps(openTimes, startMS, endMS, duration)
	result.Report.QualityPassed = len(result.Conflicts) == 0
	return result, nil
}

func calculateGaps(present []int64, startMS, endMS, durationMS int64) []Gap {
	var gaps []Gap
	expected := startMS
	for _, openMS := range present {
		if openMS < expected || openMS >= endMS {
			continue
		}
		missing := (openMS - expected) / durationMS
		if missing > 0 {
			gaps = append(gaps, Gap{FromOpenTimeMS: expected, ToOpenTimeMS: openMS - durationMS, MissingBars: missing})
		}
		expected = openMS + durationMS
	}
	if expected < endMS {
		missing := (endMS - expected) / durationMS
		if missing > 0 {
			gaps = append(gaps, Gap{FromOpenTimeMS: expected, ToOpenTimeMS: endMS - durationMS, MissingBars: missing})
		}
	}
	return gaps
}
