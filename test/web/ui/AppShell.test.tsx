// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {AppShell} from '@web/ui/AppShell';
import userEvent from '@testing-library/user-event';

// Mock TerminalDrawer to avoid xterm setup in AppShell test
vi.mock('@web/terminal/TerminalDrawer', () => ({
  TerminalDrawer: () => <div data-testid="mock-terminal-drawer" />,
}));

afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.clearAllMocks();
});

it('supports navbar drag/keyboard resizing and double-click reset', () => {
  const onLock = vi.fn();
  const {container} = render(
    <MemoryRouter>
      <AppShell onLock={onLock}>
        <div>Main content</div>
      </AppShell>
    </MemoryRouter>
  );

  const resizeHandle = screen.getByRole('separator', {name: 'Resize navigation sidebar'});
  expect(resizeHandle.getAttribute('aria-valuenow')).toBe('205');

  // Keyboard resize
  fireEvent.keyDown(resizeHandle, {key: 'ArrowRight'});
  expect(resizeHandle.getAttribute('aria-valuenow')).toBe('213');
  expect(localStorage.getItem('kestrel.nav.width')).toBe('213');

  // Double-click to reset
  fireEvent.doubleClick(resizeHandle);
  expect(resizeHandle.getAttribute('aria-valuenow')).toBe('205');
  expect(localStorage.getItem('kestrel.nav.width')).toBe('205');

  const shell = container.querySelector('.app-shell') as HTMLElement;
  expect(shell.style.getPropertyValue('--nav-width')).toBe('205px');
});

it('toggles mini icon-only navbar mode via logo, keyboard and Ctrl+B shortcut', async () => {
  const user = userEvent.setup();
  const onLock = vi.fn();
  const {container} = render(
    <MemoryRouter>
      <AppShell onLock={onLock}>
        <div>Main content</div>
      </AppShell>
    </MemoryRouter>
  );

  const toggleBtn = screen.getByRole('button', {name: /Collapse sidebar/});
  expect(toggleBtn).toBeDefined();
  expect(toggleBtn.querySelector('svg[aria-label="Kestrel"]')).not.toBeNull();
  expect(toggleBtn.getAttribute('aria-expanded')).toBe('true');
  expect(container.querySelector('.app-nav-toggle')).toBeNull();

  // Click collapse
  fireEvent.click(toggleBtn);
  const nav = container.querySelector('.app-nav') as HTMLElement;
  expect(nav.classList.contains('collapsed')).toBe(true);
  expect(localStorage.getItem('kestrel.nav.collapsed')).toBe('true');

  const shell = container.querySelector('.app-shell') as HTMLElement;
  expect(shell.style.getPropertyValue('--nav-width')).toBe('56px');
  expect(toggleBtn.getAttribute('aria-expanded')).toBe('false');

  toggleBtn.focus();
  await user.keyboard('{Enter}');
  expect(nav.classList.contains('collapsed')).toBe(false);
  expect(document.activeElement).toBe(toggleBtn);
  await user.keyboard(' ');
  expect(nav.classList.contains('collapsed')).toBe(true);

  // Shortcut Ctrl+B to expand back
  fireEvent.keyDown(window, {key: 'b', ctrlKey: true});
  expect(nav.classList.contains('collapsed')).toBe(false);
  expect(localStorage.getItem('kestrel.nav.collapsed')).toBe('false');
  expect(shell.style.getPropertyValue('--nav-width')).toBe('205px');
});

it('renders clean concise header without redundant disclaimers', () => {
  const onLock = vi.fn();
  render(
    <MemoryRouter>
      <AppShell onLock={onLock}>
        <div>Main content</div>
      </AppShell>
    </MemoryRouter>
  );

  expect(screen.getByText('VND')).toBeDefined();
  expect(screen.queryByText(/SSI production blocked/)).toBeNull();
});
