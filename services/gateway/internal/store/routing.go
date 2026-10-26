package store

type RoutingPolicy struct {
	HistoricalProvider string `json:"historical_provider"`
	RealtimeProvider   string `json:"realtime_provider"`
	FinancialsProvider string `json:"financials_provider"`
	FallbackEnabled    bool   `json:"fallback_enabled"`
}

func (s *Store) routingSchema() error {
	_, err := s.DB.Exec(`CREATE TABLE IF NOT EXISTS provider_routing_policy(
		id INTEGER PRIMARY KEY CHECK(id=1),
		historical_provider TEXT NOT NULL,
		realtime_provider TEXT NOT NULL,
		financials_provider TEXT NOT NULL,
		fallback_enabled INTEGER NOT NULL,
		updated_at TEXT NOT NULL
	);
	INSERT OR IGNORE INTO provider_routing_policy
		(id,historical_provider,realtime_provider,financials_provider,fallback_enabled,updated_at)
		VALUES(1,'vndirect','fixture','tcbs',1,'')`)
	return err
}

func (s *Store) RoutingPolicy() (RoutingPolicy, error) {
	var policy RoutingPolicy
	err := s.DB.QueryRow(`SELECT historical_provider,realtime_provider,financials_provider,fallback_enabled
		FROM provider_routing_policy WHERE id=1`).Scan(
		&policy.HistoricalProvider,
		&policy.RealtimeProvider,
		&policy.FinancialsProvider,
		&policy.FallbackEnabled,
	)
	return policy, err
}

func (s *Store) SetRoutingPolicy(policy RoutingPolicy) error {
	_, err := s.DB.Exec(`UPDATE provider_routing_policy SET historical_provider=?,realtime_provider=?,financials_provider=?,fallback_enabled=?,updated_at=? WHERE id=1`,
		policy.HistoricalProvider,
		policy.RealtimeProvider,
		policy.FinancialsProvider,
		policy.FallbackEnabled,
		Now(),
	)
	return err
}
