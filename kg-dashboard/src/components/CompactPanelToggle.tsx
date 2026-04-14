type CompactPanelTab = 'controls' | 'inspector';

interface CompactPanelToggleProps {
  activeTab: CompactPanelTab;
  onChange: (tab: CompactPanelTab) => void;
}

export function CompactPanelToggle({
  activeTab,
  onChange,
}: CompactPanelToggleProps) {
  return (
    <div className="segmented-control dashboard-compact-panel-toggle" role="group" aria-label="Compact panels">
      <button
        type="button"
        className={activeTab === 'controls' ? 'segmented-control__button is-active' : 'segmented-control__button'}
        onClick={() => onChange('controls')}
        aria-pressed={activeTab === 'controls'}
      >
        Controls
      </button>
      <button
        type="button"
        className={activeTab === 'inspector' ? 'segmented-control__button is-active' : 'segmented-control__button'}
        onClick={() => onChange('inspector')}
        aria-pressed={activeTab === 'inspector'}
      >
        Inspector
      </button>
    </div>
  );
}