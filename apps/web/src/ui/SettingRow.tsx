import type {ReactNode} from 'react';

type Props = {
  label: string;
  description?: string;
  children: ReactNode;
};

export function SettingRow({label, description, children}: Props) {
  return (
    <div className="setting-row">
      <div className="setting-info">
        <span className="setting-label">{label}</span>
        {description && <span className="setting-desc">{description}</span>}
      </div>
      <div className="setting-control">{children}</div>
    </div>
  );
}
