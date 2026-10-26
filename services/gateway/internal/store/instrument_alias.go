package store

import (
	"database/sql"
	"errors"
	"strings"
	"time"
)

// ProviderInstrumentAlias preserves a provider's identifier and symbol history
// while keeping the local instrument identity stable.
type ProviderInstrumentAlias struct {
	StableInstrumentID   string     `json:"stable_instrument_id"`
	ProviderID           string     `json:"provider_id"`
	ProviderInstrumentID string     `json:"provider_instrument_id"`
	NativeSymbol         string     `json:"native_symbol"`
	Venue                *string    `json:"venue"`
	EffectiveFrom        time.Time  `json:"effective_from"`
	EffectiveTo          *time.Time `json:"effective_to"`
}

func aliasInstant(value time.Time) string {
	return value.UTC().Format("2006-01-02T15:04:05.000000000Z")
}

func (s *Store) instrumentAliasSchema() error {
	_, err := s.DB.Exec(`CREATE TABLE IF NOT EXISTS provider_instrument_aliases(
		provider_id TEXT NOT NULL,
		provider_instrument_id TEXT NOT NULL,
		stable_instrument_id TEXT NOT NULL,
		native_symbol TEXT NOT NULL,
		venue TEXT,
		effective_from TEXT NOT NULL,
		effective_to TEXT,
		PRIMARY KEY(provider_id,provider_instrument_id,effective_from),
		CHECK(effective_to IS NULL OR effective_to > effective_from)
	);
	CREATE INDEX IF NOT EXISTS provider_instrument_alias_lookup
		ON provider_instrument_aliases(provider_id,provider_instrument_id,effective_from,effective_to);`)
	return err
}

func normalizeAlias(alias ProviderInstrumentAlias) (ProviderInstrumentAlias, error) {
	if strings.TrimSpace(alias.StableInstrumentID) == "" ||
		strings.TrimSpace(alias.ProviderID) == "" ||
		strings.TrimSpace(alias.ProviderInstrumentID) == "" ||
		strings.TrimSpace(alias.NativeSymbol) == "" ||
		alias.EffectiveFrom.IsZero() {
		return ProviderInstrumentAlias{}, errors.New("stable and provider instrument identities, symbol, and effective_from are required")
	}
	if alias.Venue != nil {
		venue := strings.TrimSpace(*alias.Venue)
		if venue == "" {
			alias.Venue = nil
		} else {
			alias.Venue = &venue
		}
	}
	alias.StableInstrumentID = strings.TrimSpace(alias.StableInstrumentID)
	alias.ProviderID = strings.TrimSpace(alias.ProviderID)
	alias.ProviderInstrumentID = strings.TrimSpace(alias.ProviderInstrumentID)
	alias.NativeSymbol = strings.TrimSpace(alias.NativeSymbol)
	alias.EffectiveFrom = alias.EffectiveFrom.UTC()
	if alias.EffectiveTo != nil {
		end := alias.EffectiveTo.UTC()
		if !end.After(alias.EffectiveFrom) {
			return ProviderInstrumentAlias{}, errors.New("effective_to must be later than effective_from")
		}
		alias.EffectiveTo = &end
	}
	return alias, nil
}

func aliasEqual(a, b ProviderInstrumentAlias) bool {
	if a.StableInstrumentID != b.StableInstrumentID || a.ProviderID != b.ProviderID ||
		a.ProviderInstrumentID != b.ProviderInstrumentID || a.NativeSymbol != b.NativeSymbol ||
		!a.EffectiveFrom.Equal(b.EffectiveFrom) || (a.EffectiveTo == nil) != (b.EffectiveTo == nil) ||
		(a.Venue == nil) != (b.Venue == nil) {
		return false
	}
	if a.EffectiveTo != nil && !a.EffectiveTo.Equal(*b.EffectiveTo) {
		return false
	}
	return a.Venue == nil || *a.Venue == *b.Venue
}

func (s *Store) PutProviderInstrumentAlias(input ProviderInstrumentAlias) error {
	alias, err := normalizeAlias(input)
	if err != nil {
		return err
	}
	from := aliasInstant(alias.EffectiveFrom)
	to := any(nil)
	if alias.EffectiveTo != nil {
		to = aliasInstant(*alias.EffectiveTo)
	}
	venue := any(nil)
	if alias.Venue != nil {
		venue = *alias.Venue
	}

	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	rows, err := tx.Query(`SELECT stable_instrument_id,provider_id,provider_instrument_id,native_symbol,venue,effective_from,effective_to
		FROM provider_instrument_aliases WHERE provider_id=? AND provider_instrument_id=?`, alias.ProviderID, alias.ProviderInstrumentID)
	if err != nil {
		return err
	}
	for rows.Next() {
		var existing ProviderInstrumentAlias
		var existingFrom string
		var existingTo sql.NullString
		var existingVenue sql.NullString
		if err = rows.Scan(&existing.StableInstrumentID, &existing.ProviderID, &existing.ProviderInstrumentID, &existing.NativeSymbol, &existingVenue, &existingFrom, &existingTo); err != nil {
			rows.Close()
			return err
		}
		if existingVenue.Valid {
			v := existingVenue.String
			existing.Venue = &v
		}
		if existing.EffectiveFrom, err = time.Parse(time.RFC3339Nano, existingFrom); err != nil {
			rows.Close()
			return err
		}
		if existingTo.Valid {
			v, parseErr := time.Parse(time.RFC3339Nano, existingTo.String)
			if parseErr != nil {
				rows.Close()
				return parseErr
			}
			existing.EffectiveTo = &v
		}
		if existing.EffectiveFrom.Equal(alias.EffectiveFrom) {
			rows.Close()
			if aliasEqual(existing, alias) {
				return nil
			}
			return errors.New("provider instrument alias conflicts with an existing effective period")
		}
		if (existing.EffectiveTo == nil || alias.EffectiveFrom.Before(*existing.EffectiveTo)) &&
			(alias.EffectiveTo == nil || existing.EffectiveFrom.Before(*alias.EffectiveTo)) {
			rows.Close()
			return errors.New("provider instrument alias effective periods overlap")
		}
	}
	if err = rows.Err(); err != nil {
		rows.Close()
		return err
	}
	if err = rows.Close(); err != nil {
		return err
	}
	if _, err = tx.Exec(`INSERT INTO provider_instrument_aliases
		(provider_id,provider_instrument_id,stable_instrument_id,native_symbol,venue,effective_from,effective_to)
		VALUES(?,?,?,?,?,?,?)`, alias.ProviderID, alias.ProviderInstrumentID, alias.StableInstrumentID, alias.NativeSymbol, venue, from, to); err != nil {
		return err
	}
	return tx.Commit()
}

func (s *Store) ProviderInstrumentAliases(providerID, providerInstrumentID string) ([]ProviderInstrumentAlias, error) {
	rows, err := s.DB.Query(`SELECT stable_instrument_id,provider_id,provider_instrument_id,native_symbol,venue,effective_from,effective_to
		FROM provider_instrument_aliases WHERE (?='' OR provider_id=?) AND (?='' OR provider_instrument_id=?)
		ORDER BY provider_id,provider_instrument_id,effective_from`, providerID, providerID, providerInstrumentID, providerInstrumentID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	result := []ProviderInstrumentAlias{}
	for rows.Next() {
		var alias ProviderInstrumentAlias
		var from string
		var to sql.NullString
		var venue sql.NullString
		if err = rows.Scan(&alias.StableInstrumentID, &alias.ProviderID, &alias.ProviderInstrumentID, &alias.NativeSymbol, &venue, &from, &to); err != nil {
			return nil, err
		}
		if venue.Valid {
			v := venue.String
			alias.Venue = &v
		}
		if alias.EffectiveFrom, err = time.Parse(time.RFC3339Nano, from); err != nil {
			return nil, err
		}
		if to.Valid {
			v, parseErr := time.Parse(time.RFC3339Nano, to.String)
			if parseErr != nil {
				return nil, parseErr
			}
			alias.EffectiveTo = &v
		}
		result = append(result, alias)
	}
	return result, rows.Err()
}

func (s *Store) ResolveProviderInstrument(providerID, providerInstrumentID string, at time.Time) (ProviderInstrumentAlias, error) {
	instant := aliasInstant(at)
	var alias ProviderInstrumentAlias
	var from string
	var to sql.NullString
	var venue sql.NullString
	err := s.DB.QueryRow(`SELECT stable_instrument_id,provider_id,provider_instrument_id,native_symbol,venue,effective_from,effective_to
		FROM provider_instrument_aliases WHERE provider_id=? AND provider_instrument_id=? AND effective_from<=? AND (effective_to IS NULL OR effective_to>?)
		ORDER BY effective_from DESC LIMIT 1`, providerID, providerInstrumentID, instant, instant).
		Scan(&alias.StableInstrumentID, &alias.ProviderID, &alias.ProviderInstrumentID, &alias.NativeSymbol, &venue, &from, &to)
	if err != nil {
		return ProviderInstrumentAlias{}, err
	}
	if venue.Valid {
		v := venue.String
		alias.Venue = &v
	}
	if alias.EffectiveFrom, err = time.Parse(time.RFC3339Nano, from); err != nil {
		return ProviderInstrumentAlias{}, err
	}
	if to.Valid {
		v, parseErr := time.Parse(time.RFC3339Nano, to.String)
		if parseErr != nil {
			return ProviderInstrumentAlias{}, parseErr
		}
		alias.EffectiveTo = &v
	}
	return alias, nil
}
