// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {Providers,type ProviderStatus,type RoutingPolicy} from './Providers';
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

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

it('renders provider cards and handles ping test probe', async () => {
  vi.mocked(request).mockImplementation(async path => {
    if (path === '/providers') return mockProviders;
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

  expect(await screen.findByText('VNDIRECT (Dchart UDF)')).toBeDefined();
  expect(screen.getByText('SSI FastConnect Data')).toBeDefined();
  expect(screen.getByText('38.5ms')).toBeDefined();

  // Test Ping button
  const pingButtons = screen.getAllByRole('button', {name: 'Ping Test'});
  fireEvent.click(pingButtons[0]);

  await waitFor(() => {
    expect(send).toHaveBeenCalledWith('/providers/vndirect/ping', {});
  });
});
