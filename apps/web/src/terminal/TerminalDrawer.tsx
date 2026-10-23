import {useEffect,useRef,useState} from 'react';
import {Terminal} from '@xterm/xterm';
import '@xterm/xterm/css/xterm.css';
import {useAppearance} from '../theme/store';
import {fontFamilies} from '../theme/tokens';
import {Button} from '../ui/buttons';
import {send} from '../api';

type Props = {
  open: boolean;
  onToggle: () => void;
  cwd?: string;
};

export function TerminalDrawer({open, onToggle, cwd = ''}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<Terminal | null>(null);
  const sessionRef = useRef<string>('');
  const eventSourceRef = useRef<EventSource | null>(null);
  const appearance = useAppearance();
  const [connected, setConnected] = useState<boolean>(false);

  useEffect(() => {
    if (!open || !containerRef.current) return;

    const c = appearance.colors;
    const term = new Terminal({
      theme: {
        background: c.canvas,
        foreground: c.text,
        cursor: c.accent,
        selectionBackground: c.selection,
      },
      fontFamily: fontFamilies[appearance.font],
      fontSize: appearance.fontSize,
      cursorBlink: true,
      convertEol: true,
    });

    term.open(containerRef.current);
    termRef.current = term;

    let cancelled = false;

    // Create session on gateway
    void send<{session_id: string}>('/terminal/session', {cwd})
      .then(res => {
        if (cancelled) return;
        const sessionId = res.session_id;
        sessionRef.current = sessionId;
        setConnected(true);

        // Connect SSE output stream
        const es = new EventSource(`/api/v1/terminal/events?session_id=${encodeURIComponent(sessionId)}`);
        eventSourceRef.current = es;

        es.onmessage = evt => {
          if (!evt.data) return;
          try {
            const raw = atob(evt.data);
            term.write(raw);
          } catch {
            term.write(evt.data);
          }
        };

        es.addEventListener('close', () => {
          term.write('\r\n[Session closed]\r\n');
          setConnected(false);
        });

        // Capture user keyboard input and send to gateway stdin
        term.onData(data => {
          void send('/terminal/input', {session_id: sessionId, data});
        });
      })
      .catch(err => {
        if (!cancelled) {
          term.write(`\r\nFailed to start terminal session: ${err instanceof Error ? err.message : String(err)}\r\n`);
        }
      });

    return () => {
      cancelled = true;
      eventSourceRef.current?.close();
      if (sessionRef.current) {
        void send('/terminal/kill', {session_id: sessionRef.current});
        sessionRef.current = '';
      }
      term.dispose();
      termRef.current = null;
      setConnected(false);
    };
  }, [open, cwd, appearance]);

  return (
    <aside
      className="terminal-drawer"
      aria-label="Interactive terminal"
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: open ? 260 : 32,
        background: 'var(--panel)',
        borderTop: '1px solid var(--border)',
        zIndex: 50,
        display: 'flex',
        flexDirection: 'column',
        transition: 'height 0.2s ease',
      }}
    >
      <div
        className="terminal-header"
        style={{
          display: 'flex',
          justifyContent:'space-between',
          alignItems: 'center',
          padding: '2px 8px',
          background: 'var(--raised)',
          borderBottom: open ? '1px solid var(--border)' : 'none',
          minHeight: 31,
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
          <Button onClick={onToggle} title="Toggle terminal drawer (Ctrl+`)">
            {open ? '▼ Terminal' : '▲ Terminal'}
          </Button>
          {open && (
            <span style={{fontSize: 11, color: connected ? 'var(--positive)' : 'var(--muted)'}}>
              {connected ? '● Connected' : '○ Disconnected'}
            </span>
          )}
        </div>
        {open && (
          <div style={{display: 'flex', gap: 6}}>
            <Button
              onClick={() => {
                if (sessionRef.current) {
                  void send('/terminal/input', {session_id: sessionRef.current, data: 'cls\r\n'});
                }
              }}
              title="Clear terminal screen"
            >
              Clear
            </Button>
            <Button onClick={onToggle} title="Close terminal drawer">
              ×
            </Button>
          </div>
        )}
      </div>

      {open && (
        <div
          ref={containerRef}
          className="terminal-body"
          style={{
            flex: 1,
            overflow: 'hidden',
            padding: '4px 8px',
            background: 'var(--canvas)',
          }}
        />
      )}
    </aside>
  );
}
