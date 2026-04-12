import type { GraphCompanionView } from '../types/graph';

const TABS: GraphCompanionView[] = ['graph', 'table', 'timeline', 'schema'];

export function GraphCompanionTabs({
  activeView,
  onChange,
}: {
  activeView: GraphCompanionView;
  onChange: (view: GraphCompanionView) => void;
}) {
  return (
    <div className="segmented-control companion-tabs" role="tablist" aria-label="Companion views">
      {TABS.map((tab) => (
        <button
          key={tab}
          type="button"
          className={tab === activeView ? 'segmented-control__button is-active' : 'segmented-control__button'}
          onClick={() => onChange(tab)}
          aria-pressed={tab === activeView}
        >
          {tab[0].toUpperCase() + tab.slice(1)}
        </button>
      ))}
    </div>
  );
}

export default GraphCompanionTabs;
