import {useState} from 'react';
import {useQuery,useQueryClient} from '@tanstack/react-query';
import {request,send} from './api';
import {PageHeader,Panel,PanelHeader,Toolbar} from './ui/layout';
import {Button} from './ui/buttons';
import {Field,Select} from './ui/fields';
import {StatusLabel} from './ui/data';
import {EmptyState,ErrorState,LoadingState} from './ui/feedback';

export type ProviderStatus = {
  id: string;
  name: string;
  category: 'community' | 'broker_api' | 'local' | 'synthetic';
  state: 'connected' | 'offline' | 'blocked' | 'fixture';
  latency_ms: number | null;
  capabilities: string[];
  description: string;
  error?: string | null;
  configured: boolean;
};

export type RoutingPolicy = {
  historical_provider: string;
  realtime_provider: string;
  financials_provider: string;
  fallback_enabled: boolean;
};

export function Providers() {
  const client = useQueryClient();
  const [pinging, setPinging] = useState<string | null>(null);
  const [localPings, setLocalPings] = useState<Record<string, {latency_ms: number | null; state: string; error?: string}>>({});

  const providers = useQuery({
    queryKey: ['providers'],
    queryFn: () => request<ProviderStatus[]>('/providers'),
  });

  const routing = useQuery({
    queryKey: ['providers-routing'],
    queryFn: () => request<RoutingPolicy>('/providers/routing'),
  });

  const handlePing = async (id: string) => {
    setPinging(id);
    try {
      const res = await send<ProviderStatus>(`/providers/${encodeURIComponent(id)}/ping`, {});
      setLocalPings(prev => ({
        ...prev,
        [id]: {latency_ms: res.latency_ms, state: res.state, error: res.error ?? undefined},
      }));
      await client.invalidateQueries({queryKey: ['providers']});
    } catch (err) {
      setLocalPings(prev => ({
        ...prev,
        [id]: {latency_ms: null, state: 'offline', error: err instanceof Error ? err.message : String(err)},
      }));
    } finally {
      setPinging(null);
    }
  };

  const updateRouting = async (patch: Partial<RoutingPolicy>) => {
    await send<RoutingPolicy>('/providers/routing', patch, 'PUT');
    await client.invalidateQueries({queryKey: ['providers-routing']});
  };

  const getTone = (state: string): 'positive' | 'warning' | 'negative' | 'info' => {
    if (state === 'connected') return 'positive';
    if (state === 'fixture') return 'info';
    if (state === 'blocked') return 'warning';
    return 'negative';
  };

  return (
    <section className="providers-page">
      <PageHeader
        title="Data Providers"
        actions={<StatusLabel tone="positive">MULTI-SOURCE ROUTER ACTIVE</StatusLabel>}
      />

      <Toolbar>
        <Button pending={providers.isFetching} onClick={() => void providers.refetch()}>
          Refresh Feeds
        </Button>
        <span className="muted">
          Primary: <strong>{routing.data?.historical_provider.toUpperCase() ?? 'VNDIRECT'}</strong> · Fallback:{' '}
          {routing.data?.fallback_enabled ? 'ON' : 'OFF'}
        </span>
      </Toolbar>

      {providers.isPending && <LoadingState>Querying provider health registry…</LoadingState>}
      <ErrorState error={providers.error || routing.error} onRetry={() => { void providers.refetch(); void routing.refetch(); }} />

      {providers.data && (
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 12, margin: '12px 0'}}>
          {providers.data.map(p => {
            const currentPing = localPings[p.id];
            const activeState = currentPing?.state ?? p.state;
            const latency = currentPing?.latency_ms ?? p.latency_ms;

            return (
              <Panel key={p.id} style={{display: 'flex', flexDirection: 'column', margin: 0}}>
                <PanelHeader
                  title={p.name}
                  actions={
                    <div style={{display: 'flex', gap: 6, alignItems: 'center'}}>
                      <StatusLabel tone={getTone(activeState)}>{activeState.toUpperCase()}</StatusLabel>
                      {latency !== null && latency !== undefined && (
                        <span style={{fontSize: 11, color: latency < 100 ? 'var(--positive)' : 'var(--warning)'}}>
                          {latency}ms
                        </span>
                      )}
                    </div>
                  }
                />
                <div className="panel-content" style={{flex: 1, display: 'flex', flexDirection: 'column', gap: 8}}>
                  <p style={{margin: 0, fontSize: 12, color: 'var(--secondary)'}}>{p.description}</p>

                  <div style={{display: 'flex', flexWrap: 'wrap', gap: 4}}>
                    <span className="badge" style={{fontSize: 10}}>{p.category.toUpperCase()}</span>
                    {p.capabilities.map(cap => (
                      <span key={cap} className="badge" style={{fontSize: 10, borderColor: 'var(--border)'}}>
                        {cap}
                      </span>
                    ))}
                  </div>

                  {(currentPing?.error || p.error) && (
                    <p className="error" style={{fontSize: 11, margin: 0}}>
                      {currentPing?.error || p.error}
                    </p>
                  )}

                  <div style={{marginTop: 'auto', paddingTop: 8, display: 'flex', justifyContent: 'flex-end'}}>
                    <Button
                      pending={pinging === p.id}
                      onClick={() => handlePing(p.id)}
                      title={`Send health probe to ${p.name}`}
                    >
                      Ping Test
                    </Button>
                  </div>
                </div>
              </Panel>
            );
          })}
        </div>
      )}

      {routing.data && (
        <Panel>
          <PanelHeader title="DATA ROUTING & DISPATCH POLICY" />
          <div className="panel-content">

            <div className="form-grid" style={{marginTop: 12}}>
              <Field label="Historical EOD & Backtest Feed">
                <Select
                  value={routing.data.historical_provider}
                  onChange={e => updateRouting({historical_provider: e.target.value})}
                >
                  <option value="vndirect">VNDIRECT (Dchart TradingView UDF - Free)</option>
                  <option value="tcbs">TCBS (Vnstock Stock-Insight - Free)</option>
                  <option value="fixture">Synthetic Fixture (Offline local baseline)</option>
                </Select>
              </Field>

              <Field label="Realtime Market Quotes Feed">
                <Select
                  value={routing.data.realtime_provider}
                  onChange={e => updateRouting({realtime_provider: e.target.value})}
                >
                  <option value="fixture">Synthetic Fixture (Offline safe replay)</option>
                  <option value="dnse">DNSE OpenAPI (LightSpeed WebSocket - Requires Key)</option>
                  <option value="ssi">SSI FastConnect (Production blocked)</option>
                </Select>
              </Field>

              <Field label="Financial Statements & Ratios Feed">
                <Select
                  value={routing.data.financials_provider}
                  onChange={e => updateRouting({financials_provider: e.target.value})}
                >
                  <option value="tcbs">TCBS (Vnstock Corporate Ratios - Free)</option>
                  <option value="fixture">Synthetic Financial Fixtures</option>
                </Select>
              </Field>
            </div>

            <div style={{marginTop: 12}}>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={routing.data.fallback_enabled}
                  onChange={e => updateRouting({fallback_enabled: e.target.checked})}
                />
                <span>
                  <strong>Auto fallback:</strong> Revert to secondary feeds or local cache on error.
                </span>
              </label>
            </div>
          </div>
        </Panel>
      )}

      {!providers.isPending && !providers.error && (!providers.data || providers.data.length === 0) && (
        <EmptyState>No data providers registered in engine.</EmptyState>
      )}
    </section>
  );
}
