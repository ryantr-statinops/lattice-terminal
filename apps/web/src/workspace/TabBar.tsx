import type {KeyboardEvent} from 'react';

type Props = {
  files: string[];
  active: string;
  buffers: Record<string, string>;
  saved: Record<string, string>;
  onSelect: (path: string) => void;
  onClose: (path: string) => void;
};

export function TabBar({files, active, buffers, saved, onSelect, onClose}: Props) {
  if (files.length === 0) return null;

  const handleKeyDown = (e: KeyboardEvent<HTMLButtonElement>, path: string) => {
    if (e.key === 'Delete' || ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'w')) {
      e.preventDefault();
      e.stopPropagation();
      onClose(path);
    }
  };

  return (
    <div className="tab-bar" role="tablist" aria-label="Open files">
      {files.map(path => {
        const isDirty = buffers[path] !== undefined && saved[path] !== undefined && buffers[path] !== saved[path];
        const isActive = path === active;
        const name = path.split('/').pop() || path;

        return (
          <div
            key={path}
            role="tab"
            aria-selected={isActive}
            tabIndex={isActive ? 0 : -1}
            className={'tab-item' + (isActive ? ' active' : '')}
            onClick={() => onSelect(path)}
            title={path}
          >
            {isDirty && <span className="tab-dirty" aria-label="unsaved changes" title="Unsaved changes" />}
            <span className="tab-name">{name}</span>
            <button
              type="button"
              className="tab-close"
              aria-label={`Close ${name}`}
              title={`Close ${name}`}
              onClick={e => {
                e.stopPropagation();
                onClose(path);
              }}
              onKeyDown={e => handleKeyDown(e, path)}
            >
              ×
            </button>
          </div>
        );
      })}
    </div>
  );
}
