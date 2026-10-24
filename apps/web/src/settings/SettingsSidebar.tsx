export type SettingsCategory = 'appearance' | 'colors' | 'sources' | 'profile';

type CategoryItem = {
  id: SettingsCategory;
  label: string;
  description: string;
};

export const SETTINGS_CATEGORIES: CategoryItem[] = [
  {
    id: 'appearance',
    label: 'Appearance & Font',
    description: 'Theme preset, density scale and typography',
  },
  {
    id: 'colors',
    label: 'Role Colors',
    description: 'Semantic colors and contrast profiles',
  },
  {
    id: 'sources',
    label: 'Source Evidence',
    description: 'Market data permissions and capabilities',
  },
  {
    id: 'profile',
    label: 'Local Profile',
    description: 'Data directory and account configuration',
  },
];

type Props = {
  active: SettingsCategory;
  onSelect: (category: SettingsCategory) => void;
};

export function SettingsSidebar({active, onSelect}: Props) {
  return (
    <nav className="settings-nav" aria-label="Settings categories" role="tablist">
      {SETTINGS_CATEGORIES.map(cat => {
        const isActive = active === cat.id;
        return (
          <button
            key={cat.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            className={'settings-nav-item' + (isActive ? ' active' : '')}
            onClick={() => onSelect(cat.id)}
            title={cat.description}
          >
            <span>{cat.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
