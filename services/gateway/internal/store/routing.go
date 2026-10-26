package store

import (
	"database/sql"
	"encoding/json"
	"errors"
	"strings"
)

type RoutingPolicy struct {
	HistoricalProvider string            `json:"historical_provider"`
	RealtimeProvider   string            `json:"realtime_provider"`
	FinancialsProvider string            `json:"financials_provider"`
	FallbackEnabled    bool              `json:"fallback_enabled"`
	Datasets           map[string]string `json:"datasets"`
}

func (s *Store) routingSchema() error {
	_, err := s.DB.Exec(`CREATE TABLE IF NOT EXISTS provider_routing_policy(
		id INTEGER PRIMARY KEY CHECK(id=1),
		historical_provider TEXT NOT NULL,
		realtime_provider TEXT NOT NULL,
		financials_provider TEXT NOT NULL,
		fallback_enabled INTEGER NOT NULL,
		dataset_routes TEXT NOT NULL DEFAULT '{}',
		updated_at TEXT NOT NULL
	);`)
	if err != nil {
		return err
	}
	if err = s.ensureDatasetRoutingColumn(); err != nil {
		return err
	}
	_, err = s.DB.Exec(`INSERT OR IGNORE INTO provider_routing_policy
		(id,historical_provider,realtime_provider,financials_provider,fallback_enabled,dataset_routes,updated_at)
		VALUES(1,'vndirect','fixture','tcbs',1,'{}','')`)
	return err
}

func (s *Store) RoutingPolicy() (RoutingPolicy, error) {
	var policy RoutingPolicy
	var routes string
	err := s.DB.QueryRow(`SELECT historical_provider,realtime_provider,financials_provider,fallback_enabled,dataset_routes
		FROM provider_routing_policy WHERE id=1`).Scan(
		&policy.HistoricalProvider,
		&policy.RealtimeProvider,
		&policy.FinancialsProvider,
		&policy.FallbackEnabled,
		&routes,
	)
	if err != nil {
		return policy, err
	}
	if err = json.Unmarshal([]byte(routes), &policy.Datasets); err != nil {
		return policy, errors.New("stored dataset routing policy is invalid")
	}
	if policy.Datasets == nil {
		policy.Datasets = map[string]string{}
	}
	return policy, err
}

func (s *Store) SetRoutingPolicy(policy RoutingPolicy) error {
	if policy.Datasets == nil {
		policy.Datasets = map[string]string{}
	}
	for dataset, provider := range policy.Datasets {
		if strings.TrimSpace(dataset) == "" || strings.TrimSpace(provider) == "" || len(dataset) > 160 || len(provider) > 160 {
			return errors.New("dataset routing entries require bounded dataset and provider identifiers")
		}
	}
	routes, err := json.Marshal(policy.Datasets)
	if err != nil {
		return err
	}
	_, err = s.DB.Exec(`UPDATE provider_routing_policy SET historical_provider=?,realtime_provider=?,financials_provider=?,fallback_enabled=?,dataset_routes=?,updated_at=? WHERE id=1`,
		policy.HistoricalProvider,
		policy.RealtimeProvider,
		policy.FinancialsProvider,
		policy.FallbackEnabled,
		string(routes),
		Now(),
	)
	return err
}

func (s *Store) ensureDatasetRoutingColumn() error {
	rows, err := s.DB.Query("PRAGMA table_info(provider_routing_policy)")
	if err != nil {
		return err
	}
	hasColumn := false
	for rows.Next() {
		var cid, notNull, primaryKey int
		var name, kind string
		var defaultValue sql.NullString
		if err = rows.Scan(&cid, &name, &kind, &notNull, &defaultValue, &primaryKey); err != nil {
			rows.Close()
			return err
		}
		if name == "dataset_routes" {
			hasColumn = true
		}
	}
	if err = rows.Err(); err != nil {
		rows.Close()
		return err
	}
	if err = rows.Close(); err != nil {
		return err
	}
	if !hasColumn {
		_, err = s.DB.Exec("ALTER TABLE provider_routing_policy ADD COLUMN dataset_routes TEXT NOT NULL DEFAULT '{}'")
	}
	return err
}
