import type {ReactNode} from 'react';

type Props = {
  id?: string;
  label: string;
  description?: string;
  children: ReactNode;
};

export function SettingRow({id, label, description, children}: Props) {
  return (
    <div className="setting-row">
      <div className="setting-info">
        {id ? (
          <label htmlFor={id} className="setting-label">
            {label}
          </label>
        ) : (
          <span className="setting-label">{label}</span>
        )}
        {description && <span className="setting-desc">{description}</span>}
      </div>
      <div className="setting-control">{children}</div>
    </div>
  );
}
