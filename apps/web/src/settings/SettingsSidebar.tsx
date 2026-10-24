export type SettingsCategory = 'appearance' | 'colors' | 'sources' | 'profile';

type CategoryItem = {
  id: SettingsCategory;
  label: string;
  icon: string;
  description: string;
};

export const SETTINGS_CATEGORIES: CategoryItem[] = [
  {
    id: 'appearance',
    label: 'Appearance & Font',
    icon: '🎨',
    description: 'Theme preset, density scale and typography',
  },
  {
    id: 'colors',
    label: 'Role Colors',
    icon: '🌈',
    description: 'Semantic colors and contrast profiles',
  },
  {
    id: 'sources',
    label: 'Source Evidence',
    icon: '🔌',
    description: 'Market data permissions and capabilities',
  },
  {
    id: 'profile',
    label: 'Local Profile',
    icon: '👤',
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
            <span aria-hidden="true">{cat.icon}</span>
            <span>{cat.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
