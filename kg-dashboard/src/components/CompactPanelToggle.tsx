type CompactPanelTab = 'controls' | 'inspector';

interface CompactPanelToggleProps {
  activeTab: CompactPanelTab;
  onChange: (tab: CompactPanelTab) => void;
  onClose: () => void;
}

export function CompactPanelToggle({
  activeTab,
  onChange,
  onClose,
}: CompactPanelToggleProps) {
  return (
    <div className="dashboard-overlay-header">
      <div className="segmented-control dashboard-compact-panel-toggle" role="tablist" aria-label="Panel tabs">
        <button
          type="button"
          role="tab"
          className={activeTab === 'controls' ? 'segmented-control__button is-active' : 'segmented-control__button'}
          onClick={() => onChange('controls')}
          aria-pressed={activeTab === 'controls'}
        >
          Controls
        </button>
        <button
          type="button"
          role="tab"
          className={activeTab === 'inspector' ? 'segmented-control__button is-active' : 'segmented-control__button'}
          onClick={() => onChange('inspector')}
          aria-pressed={activeTab === 'inspector'}
        >
          Inspector
        </button>
      </div>
      <button
        type="button"
        className="ghost-button overlay-close-button"
        onClick={onClose}
        aria-label="Close panel"
      >
        ✕
      </button>
    </div>
  );
}