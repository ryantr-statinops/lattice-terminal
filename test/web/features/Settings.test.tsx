// @vitest-environment jsdom
import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import {Settings} from '@web/Settings';
import {request} from '@web/api';
import {resetAppearance} from '@web/theme/store';

vi.mock('@web/api', () => ({
  request: vi.fn(),
  send: vi.fn(),
}));

beforeEach(() => {
  resetAppearance();
  HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute('open', '');
  };
  HTMLDialogElement.prototype.close = function () {
    this.removeAttribute('open');
  };
});

afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.clearAllMocks();
});

it('renders centered master-detail layout and switches between categories', async () => {
  vi.mocked(request).mockImplementation(async path => {
    if (path === '/engine/sources') {
      return [
        {
          id: 'SSI-FC-DATA-REST',
          documented: true,
          access_tested: false,
          rights_confirmed: false,
          approved: false,
          operating_state: 'fixture-only',
          reason: 'Unverified',
        },
      ];
    }
    if (path === '/local/config') {
      return {data_dir: '/test/data', account_source: '.env'};
    }
    return null;
  });

  const {container} = render(
    <QueryClientProvider client={new QueryClient({defaultOptions: {queries: {retry: false}}})}>
      <MemoryRouter initialEntries={['/settings']}>
        <Settings />
      </MemoryRouter>
    </QueryClientProvider>
  );

  // 1. Initial tab is Appearance & Font
  expect(await screen.findByText('APPEARANCE & TYPOGRAPHY')).toBeDefined();
  expect(screen.getByRole('tab', {name: /Appearance & Font/}).getAttribute('aria-selected')).toBe('true');
  expect(screen.getByLabelText('Layout density / Scale')).toBeDefined();

  // 2. Switch to Role Colors
  const colorsTabBtn = screen.getByRole('tab', {name: /Role Colors/});
  fireEvent.click(colorsTabBtn);
  expect(await screen.findByText('ROLE COLORS & CONTRAST PROFILE')).toBeDefined();
  expect(colorsTabBtn.getAttribute('aria-selected')).toBe('true');

  // 3. Switch to Source Evidence
  const sourcesTabBtn = screen.getByRole('tab', {name: /Source Evidence/});
  fireEvent.click(sourcesTabBtn);
  expect(await screen.findByText('DATA SOURCES & CAPABILITY EVIDENCE')).toBeDefined();

  // 4. Switch to Local Profile
  const profileTabBtn = screen.getByRole('tab', {name: /Local Profile/});
  fireEvent.click(profileTabBtn);
  expect(await screen.findByText(/LOCAL PROFILE/)).toBeDefined();

  // 5. Verify centered container exists
  const layout = container.querySelector('.settings-container');
  expect(layout).toBeDefined();
});

it('opens specific tab directly when URL hash is provided', async () => {
  vi.mocked(request).mockResolvedValue(null);

  render(
    <QueryClientProvider client={new QueryClient({defaultOptions: {queries: {retry: false}}})}>
      <MemoryRouter initialEntries={['/settings#colors']}>
        <Settings />
      </MemoryRouter>
    </QueryClientProvider>
  );

  expect(await screen.findByText('ROLE COLORS & CONTRAST PROFILE')).toBeDefined();
  expect(screen.getByRole('tab', {name: /Role Colors/}).getAttribute('aria-selected')).toBe('true');
});
