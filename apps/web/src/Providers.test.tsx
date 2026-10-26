// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {Providers,type ProviderCapability,type ProviderStatus,type RoutingPolicy} from './Providers';
import {request,send} from './api';

vi.mock('./api', () => ({
  request: vi.fn(),
  send: vi.fn(),
}));

const mockProviders: ProviderStatus[] = [
  {
    id: 'vndirect',
    name: 'VNDIRECT (Dchart UDF)',
    category: 'community',
    state: 'connected',
    latency_ms: 38.5,
    capabilities: ['historical_candles', 'intraday_candles'],
    description: 'Public TradingView-compatible UDF feed.',
    configured: true,
  },
  {
    id: 'ssi',
    name: 'SSI FastConnect Data',
    category: 'broker_api',
    state: 'blocked',
    latency_ms: null,
    capabilities: ['historical_candles', 'realtime_streaming'],
    description: 'Institutional feed.',
    configured: false,
    error: 'Blocked by policy',
  },
];

const mockRouting: RoutingPolicy = {
  historical_provider: 'vndirect',
  realtime_provider: 'fixture',
  financials_provider: 'tcbs',
  fallback_enabled: true,
};

const mockCapabilities: ProviderCapability[] = [
  {
    provider_id: 'vndirect',
    dataset: 'candles.1d',
    asset_class: 'equity',
    venues: ['HOSE'],
    documented: false,
    implemented: true,
    access_state: 'unknown',
    rights_state: 'unverified',
    health_state: 'unknown',
    evidence: 'Adapter observed; access and rights remain unverified.',
  },
  {
    provider_id: 'ssi',
    dataset: 'market-data',
    asset_class: 'multiple',
    venues: [],
    documented: true,
    implemented: false,
    access_state: 'blocked',
    rights_state: 'unknown',
    health_state: 'blocked',
    evidence: 'Production access remains gated.',
  },
];

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

it('renders provider cards and handles ping test probe', async () => {
  vi.mocked(request).mockImplementation(async path => {
    if (path === '/providers') return mockProviders;
    if (path === '/providers/capabilities') return mockCapabilities;
    if (path === '/providers/routing') return mockRouting;
    return null;
  });

  vi.mocked(send).mockResolvedValue({
    id: 'vndirect',
    state: 'connected',
    latency_ms: 25.0,
  });

  render(
    <QueryClientProvider client={new QueryClient({defaultOptions: {queries: {retry: false}}})}>
      <Providers />
    </QueryClientProvider>
  );

  expect(await screen.findByText('38.5ms')).toBeDefined();
  expect(Array.from(document.querySelectorAll('.panel strong')).map(node => node.textContent)).toContain('VNDIRECT (Dchart UDF)');
  expect(Array.from(document.querySelectorAll('.panel strong')).map(node => node.textContent)).toContain('SSI FastConnect Data');

  // Test Ping button
  const pingButtons = screen.getAllByRole('button', {name: 'Ping Test'});
  fireEvent.click(pingButtons[0]);

  await waitFor(() => {
    expect(send).toHaveBeenCalledWith('/providers/vndirect/ping', {});
  });
});

it('limits routing choices to providers declaring matching capabilities', async () => {
  vi.mocked(request).mockImplementation(async path => {
    if (path === '/providers') return mockProviders;
    if (path === '/providers/capabilities') return mockCapabilities;
    if (path === '/providers/routing') return mockRouting;
    return null;
  });

  render(
    <QueryClientProvider client={new QueryClient({defaultOptions: {queries: {retry: false}}})}>
      <Providers />
    </QueryClientProvider>
  );

  const historical = await screen.findByLabelText('Historical EOD & Backtest Feed') as HTMLSelectElement;
  const realtime = screen.getByLabelText('Realtime Market Quotes Feed') as HTMLSelectElement;
  const financials = screen.getByLabelText('Financial Statements & Ratios Feed') as HTMLSelectElement;

  expect(Array.from(historical.options).map(option => option.value)).toEqual(['vndirect', 'ssi']);
  expect(Array.from(realtime.options).map(option => option.value)).toEqual(['fixture', 'ssi']);
  expect(realtime.options[0].disabled).toBe(true);
  expect(Array.from(financials.options).map(option => option.value)).toEqual(['tcbs']);
  expect(financials.options[0].disabled).toBe(true);
});

it('shows configuration, access rights, and connection health separately', async () => {
  vi.mocked(request).mockImplementation(async path => {
    if (path === '/providers') return mockProviders;
    if (path === '/providers/capabilities') return mockCapabilities;
    if (path === '/providers/routing') return mockRouting;
    return null;
  });

  render(
    <QueryClientProvider client={new QueryClient({defaultOptions: {queries: {retry: false}}})}>
      <Providers />
    </QueryClientProvider>
  );

  const ssiError = await screen.findByText('Blocked by policy');
  const ssiCard = ssiError.closest('.panel');
  expect(ssiCard?.textContent).toContain('Configuration: not configured');
  expect(ssiCard?.textContent).toContain('Connection check: blocked');
  expect(ssiCard?.textContent).toContain('Access: blocked');
  expect(ssiCard?.textContent).toContain('Rights: unknown');
  expect(screen.getByText('Rights: unverified')).toBeDefined();
});
