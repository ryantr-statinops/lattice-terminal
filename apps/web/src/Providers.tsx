import {useState} from 'react';
import {useQuery,useQueryClient} from '@tanstack/react-query';
import {request,send} from './api';
import {PageHeader,Panel,PanelHeader,Toolbar} from './ui/layout';
import {Button} from './ui/buttons';
import {Field,Select} from './ui/fields';
import {StatusLabel} from './ui/data';
import {EmptyState,ErrorState,LoadingState} from './ui/feedback';
import {ProviderCredentialEditor} from './ProviderCredentialEditor';

export type ProviderStatus = {
  id: string;
  name: string;
  category: 'community' | 'broker_api' | 'local' | 'synthetic';
  state: 'connected' | 'offline' | 'blocked' | 'fixture' | 'unknown';
  latency_ms: number | null;
  capabilities: string[];
  description: string;
  error?: string | null;
  configured: boolean;
};

export type ProviderCapability = {
  capability_id: string;
  provider_id: string;
  service: string;
  dataset: string;
  asset_class: string;
  venue: string;
  venues: string[];
  documented: boolean;
  implemented: boolean;
  access_state: 'unknown' | 'configured' | 'available' | 'blocked';
  rights_state: 'unknown' | 'unverified' | 'approved' | 'denied';
  health_state: 'unknown' | 'connected' | 'offline' | 'blocked';
  evidence: string;
};

export type RoutingPolicy = {
  historical_provider: string;
  realtime_provider: string;
  financials_provider: string;
  fallback_enabled: boolean;
  datasets: Record<string, string>;
};

const routeCapabilityGroups = {
  historical_provider: ['historical_candles', 'intraday_candles', 'eod_daily'],
  realtime_provider: ['realtime_ticks', 'realtime_streaming', 'quotes', 'orderbook', 'offline_replay'],
  financials_provider: ['financials', 'valuation_ratios'],
} as const;
type ProviderRouteKey = keyof typeof routeCapabilityGroups;

function supportsRoute(provider: ProviderStatus, route: ProviderRouteKey) {
  return routeCapabilityGroups[route].some(capability => provider.capabilities.includes(capability));
}

function datasetRouteKey(capability: ProviderCapability) {
  return `${capability.dataset}:${capability.asset_class}:${capability.venue}`;
}

export function Providers() {
  const client = useQueryClient();
  const [pinging, setPinging] = useState<string | null>(null);
  const [credentialEditor, setCredentialEditor] = useState<string | null>(null);
  const [savedCredentialProvider, setSavedCredentialProvider] = useState<string | null>(null);
  const [routingError, setRoutingError] = useState<unknown>(null);
  const [localPings, setLocalPings] = useState<Record<string, {latency_ms: number | null; state: string; error?: string}>>({});

  const providers = useQuery({
    queryKey: ['providers'],
    queryFn: () => request<ProviderStatus[]>('/providers'),
  });

  const capabilities = useQuery({
    queryKey: ['providers-capabilities'],
    queryFn: () => request<ProviderCapability[]>('/providers/capabilities'),
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
    setRoutingError(null);
    try {
      await send<RoutingPolicy>('/providers/routing', patch, 'PUT');
      await client.invalidateQueries({queryKey: ['providers-routing']});
    } catch (error) {
      setRoutingError(error);
    }
  };

  const updateDatasetRoute = (routeKey: string, capabilityId: string) => {
    const datasets = {...(routing.data?.datasets ?? {})};
    if (capabilityId) datasets[routeKey] = capabilityId;
    else delete datasets[routeKey];
    void updateRouting({datasets});
  };

  const datasetRouteKeys = Array.from(new Set([
    ...Object.keys(routing.data?.datasets ?? {}),
    ...(capabilities.data ?? []).filter(capability => capability.implemented).map(datasetRouteKey),
  ])).sort();

  const getTone = (state: string): 'positive' | 'warning' | 'negative' | 'info' => {
    if (state === 'connected') return 'positive';
    if (state === 'fixture') return 'info';
    if (state === 'unknown') return 'info';
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

      {providers.isPending && <LoadingState>Loading provider configuration…</LoadingState>}
      <ErrorState error={providers.error || capabilities.error || routing.error || routingError} onRetry={() => { void providers.refetch(); void capabilities.refetch(); void routing.refetch(); }} />

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

                  <div aria-label={`${p.name} configuration and access status`} style={{display: 'grid', gap: 4, fontSize: 11}}>
                    <span>Configuration: {p.configured ? 'configured' : 'not configured'}</span>
                    <span>Connection check: {activeState}</span>
                    {capabilities.data
                      ?.filter(capability => capability.provider_id === p.id)
                      .map(capability => (
                        <div key={capability.capability_id} style={{borderTop: '1px solid var(--border)', paddingTop: 4}}>
                          <strong>{capability.service} · {capability.dataset} · {capability.asset_class} · {capability.venue}</strong>
                          <div>Documentation: {capability.documented ? 'documented' : 'unverified'}</div>
                          <div>Adapter: {capability.implemented ? 'implemented' : 'not implemented'}</div>
                          <div>Access: {capability.access_state}</div>
                          <div>Rights: {capability.rights_state}</div>
                          <div>Capability health: {capability.health_state}</div>
                          {capability.evidence && <div className="muted">{capability.evidence}</div>}
                        </div>
                      ))}
                  </div>

                  {(currentPing?.error || p.error) && (
                    <p className="error" style={{fontSize: 11, margin: 0}}>
                      {currentPing?.error || p.error}
                    </p>
                  )}

                  <div style={{marginTop: 'auto', paddingTop: 8, display: 'flex', justifyContent: 'flex-end'}}>
                    <div style={{display: 'flex', gap: 8}}>
                      <Button onClick={() => {setCredentialEditor(credentialEditor===p.id?null:p.id);setSavedCredentialProvider(null)}}>
                        Configure credentials
                      </Button>
                      <Button
                        pending={pinging === p.id}
                        onClick={() => handlePing(p.id)}
                        title={`Send health probe to ${p.name}`}
                      >
                        Ping Test
                      </Button>
                    </div>
                  </div>
                  {credentialEditor===p.id&&<ProviderCredentialEditor providerId={p.id} onCancel={()=>setCredentialEditor(null)} onSaved={()=>{setCredentialEditor(null);setSavedCredentialProvider(p.id);void client.invalidateQueries({queryKey:['providers']})}}/>}
                  {savedCredentialProvider===p.id&&<p role="status" className="muted">Credentials saved to the encrypted vault; provider access is unverified.</p>}
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
            <p className="muted">Choose a service capability for each dataset, asset class and venue. A declared adapter does not prove provider access or data rights.</p>

            <div className="form-grid" style={{marginTop: 12}}>
              {datasetRouteKeys.map(routeKey => {
                const choices = (capabilities.data ?? []).filter(capability => capability.implemented && datasetRouteKey(capability) === routeKey);
                const selected = routing.data?.datasets?.[routeKey] ?? '';
                return (
                  <Field key={routeKey} label={`Dataset route · ${routeKey}`}>
                    <Select
                      aria-label={`Dataset route · ${routeKey}`}
                      value={selected}
                      disabled={providers.isPending || capabilities.isPending || !capabilities.data}
                      onChange={event => updateDatasetRoute(routeKey, event.target.value)}
                    >
                      <option value="">No provider selected</option>
                      {selected && !choices.some(choice => choice.capability_id === selected) && (
                        <option value={selected} disabled>{selected} — unavailable</option>
                      )}
                      {choices.map(capability => {
                        const providerName = providers.data?.find(provider => provider.id === capability.provider_id)?.name ?? capability.provider_id;
                        return <option key={capability.capability_id} value={capability.capability_id}>{providerName} · {capability.service}</option>;
                      })}
                    </Select>
                  </Field>
                );
              })}
            </div>

            <div className="form-grid" style={{marginTop: 12}}>
              <Field label="Historical EOD & Backtest Feed">
                <Select
                  value={routing.data.historical_provider}
                  disabled={providers.isPending || !providers.data}
                  onChange={e => void updateRouting({historical_provider: e.target.value})}
                >
                  {!providers.data?.some(provider => provider.id === routing.data.historical_provider && supportsRoute(provider, 'historical_provider')) && (
                    <option value={routing.data.historical_provider} disabled>
                      {routing.data.historical_provider} — no declared coverage
                    </option>
                  )}
                  {providers.data
                    ?.filter(provider => supportsRoute(provider, 'historical_provider'))
                    .map(provider => <option key={provider.id} value={provider.id}>{provider.name}</option>)}
                </Select>
              </Field>

              <Field label="Realtime Market Quotes Feed">
                <Select
                  value={routing.data.realtime_provider}
                  disabled={providers.isPending || !providers.data}
                  onChange={e => void updateRouting({realtime_provider: e.target.value})}
                >
                  {!providers.data?.some(provider => provider.id === routing.data.realtime_provider && supportsRoute(provider, 'realtime_provider')) && (
                    <option value={routing.data.realtime_provider} disabled>
                      {routing.data.realtime_provider} — no declared coverage
                    </option>
                  )}
                  {providers.data
                    ?.filter(provider => supportsRoute(provider, 'realtime_provider'))
                    .map(provider => <option key={provider.id} value={provider.id}>{provider.name}</option>)}
                </Select>
              </Field>

              <Field label="Financial Statements & Ratios Feed">
                <Select
                  value={routing.data.financials_provider}
                  disabled={providers.isPending || !providers.data}
                  onChange={e => void updateRouting({financials_provider: e.target.value})}
                >
                  {!providers.data?.some(provider => provider.id === routing.data.financials_provider && supportsRoute(provider, 'financials_provider')) && (
                    <option value={routing.data.financials_provider} disabled>
                      {routing.data.financials_provider} — no declared coverage
                    </option>
                  )}
                  {providers.data
                    ?.filter(provider => supportsRoute(provider, 'financials_provider'))
                    .map(provider => <option key={provider.id} value={provider.id}>{provider.name}</option>)}
                </Select>
              </Field>
            </div>

            <div style={{marginTop: 12}}>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={routing.data.fallback_enabled}
                  onChange={e => void updateRouting({fallback_enabled: e.target.checked})}
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
