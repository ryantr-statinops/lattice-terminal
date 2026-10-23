import {useRef,useState,type ReactNode} from 'react';

type Props = {
  orientation?: 'horizontal' | 'vertical';
  initialRatio?: number;
  first: ReactNode;
  second: ReactNode;
  storageKey?: string;
  minRatio?: number;
  maxRatio?: number;
  className?: string;
};

const clamp = (val: number, min: number, max: number) => Math.max(min, Math.min(max, val));

export function SplitLayout({
  orientation = 'vertical',
  initialRatio = 0.5,
  first,
  second,
  storageKey,
  minRatio = 0.15,
  maxRatio = 0.85,
  className = '',
}: Props) {
  const [ratio, setRatio] = useState<number>(() => {
    if (!storageKey) return initialRatio;
    try {
      const saved = Number(localStorage.getItem(storageKey));
      if (Number.isFinite(saved) && saved >= minRatio && saved <= maxRatio) {
        return saved;
      }
    } catch {
      // fallback to initialRatio
    }
    return initialRatio;
  });

  const containerRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<boolean>(false);

  const updateRatio = (next: number) => {
    const clamped = clamp(next, minRatio, maxRatio);
    setRatio(clamped);
    if (storageKey) {
      try {
        localStorage.setItem(storageKey, String(clamped));
      } catch {
        // storage fallback
      }
    }
  };

  const handlePointerDown = (e: React.PointerEvent) => {
    e.preventDefault();
    e.currentTarget.setPointerCapture(e.pointerId);
    dragRef.current = true;
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!dragRef.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    if (orientation === 'vertical') {
      const x = e.clientX - rect.left;
      updateRatio(x / rect.width);
    } else {
      const y = e.clientY - rect.top;
      updateRatio(y / rect.height);
    }
  };

  const handlePointerUp = () => {
    dragRef.current = false;
  };

  const isVertical = orientation === 'vertical';

  return (
    <div
      ref={containerRef}
      className={`split-layout ${isVertical ? 'split-vertical' : 'split-horizontal'} ${className}`}
      style={{
        display: 'flex',
        flexDirection: isVertical ? 'row' : 'column',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      <div
        className="split-first"
        style={{
          flex: `0 0 ${ratio * 100}%`,
          overflow: 'hidden',
          minWidth: 0,
          minHeight: 0,
        }}
      >
        {first}
      </div>

      <div
        role="separator"
        tabIndex={0}
        aria-orientation={isVertical ? 'vertical' : 'horizontal'}
        aria-valuenow={Math.round(ratio * 100)}
        aria-label="Resize split panes"
        className={`split-divider ${isVertical ? 'split-divider-v' : 'split-divider-h'}`}
        style={{
          flex: '0 0 6px',
          background: 'var(--panel)',
          position: 'relative',
          cursor: isVertical ? 'col-resize' : 'row-resize',
          touchAction: 'none',
          userSelect: 'none',
        }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onDoubleClick={() => updateRatio(0.5)}
        onKeyDown={e => {
          if (isVertical && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
            e.preventDefault();
            updateRatio(ratio + (e.key === 'ArrowRight' ? 0.05 : -0.05));
          } else if (!isVertical && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
            e.preventDefault();
            updateRatio(ratio + (e.key === 'ArrowDown' ? 0.05 : -0.05));
          }
        }}
      />

      <div
        className="split-second"
        style={{
          flex: `1 1 0%`,
          overflow: 'hidden',
          minWidth: 0,
          minHeight: 0,
        }}
      >
        {second}
      </div>
    </div>
  );
}
