// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {TerminalDrawer} from './TerminalDrawer';
import {send} from '../api';

vi.mock('../api', () => ({
  send: vi.fn(),
  request: vi.fn(),
}));

// Mock @xterm/xterm Terminal
vi.mock('@xterm/xterm', () => {
  class MockTerminal {
    open = vi.fn();
    write = vi.fn();
    dispose = vi.fn();
    onData = vi.fn();
  }
  return {Terminal: MockTerminal};
});

class MockEventSource {
  onmessage: ((e: MessageEvent) => void) | null = null;
  listeners: Record<string, () => void> = {};
  close = vi.fn();
  addEventListener(event: string, cb: () => void) {
    this.listeners[event] = cb;
  }
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

it('renders collapsed drawer and toggles open to connect session and run commands', async () => {
  vi.stubGlobal('EventSource', MockEventSource);
  vi.mocked(send).mockResolvedValue({session_id: 'sess-123', status: 'ok'});

  const onToggle = vi.fn();
  const {rerender} = render(<TerminalDrawer open={false} onToggle={onToggle} />);

  const toggleBtn = screen.getByRole('button', {name: /Terminal/});
  expect(toggleBtn.textContent).toContain('▲ Terminal');

  fireEvent.click(toggleBtn);
  expect(onToggle).toHaveBeenCalled();

  // Rerender as open
  rerender(<TerminalDrawer open={true} onToggle={onToggle} />);

  await waitFor(() => {
    expect(send).toHaveBeenCalledWith('/terminal/session', {cwd: ''});
  });

  // Verify shortcuts rendered
  expect(screen.getByRole('button', {name: 'git status'})).toBeDefined();
  expect(screen.getByRole('button', {name: 'npm test'})).toBeDefined();
  expect(screen.getByRole('button', {name: 'pytest'})).toBeDefined();

  // Test running command via quick button
  fireEvent.click(screen.getByRole('button', {name: 'git status'}));
  expect(send).toHaveBeenCalledWith('/terminal/input', {session_id: 'sess-123', data: 'git status\r\n'});

  // Test typing in input box and running
  const input = screen.getByLabelText('Terminal command input');
  fireEvent.change(input, {target: {value: 'dir'}});
  fireEvent.click(screen.getByRole('button', {name: 'Run'}));
  expect(send).toHaveBeenCalledWith('/terminal/input', {session_id: 'sess-123', data: 'dir\r\n'});

  // Unmount terminates session
  rerender(<TerminalDrawer open={false} onToggle={onToggle} />);
  expect(send).toHaveBeenCalledWith('/terminal/kill', {session_id: 'sess-123'});
});
