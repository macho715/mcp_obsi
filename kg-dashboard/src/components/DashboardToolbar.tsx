import type { GraphMetrics } from '../types/graph';

interface DashboardToolbarProps {
  title: string;
  viewLabel: string;
  compareLabel?: string;
  metrics: GraphMetrics;
  onOpenPanel: () => void;
}

export function DashboardToolbar({
  title,
  viewLabel,
  compareLabel,
  metrics,
  onOpenPanel,
}: DashboardToolbarProps) {
  return (
    <header className="dashboard-toolbar" aria-label="Dashboard toolbar">
      <div className="dashboard-toolbar__identity">
        <strong className="dashboard-toolbar__title">{title}</strong>
        <span className="dashboard-toolbar__view">{viewLabel}</span>
        {compareLabel != null ? <span className="dashboard-toolbar__compare">{compareLabel}</span> : null}
      </div>
      <dl className="dashboard-toolbar__stats">
        <div>
          <dt>Visible</dt>
          <dd>
            {metrics.visibleNodes} / {metrics.visibleEdges}
          </dd>
        </div>
        <div>
          <dt>Hidden</dt>
          <dd>
            {metrics.hiddenNodes} / {metrics.hiddenEdges}
          </dd>
        </div>
        <div>
          <dt>Hotspots</dt>
          <dd>
            {metrics.issueCount} / {metrics.hubCount}
          </dd>
        </div>
      </dl>
      <button
        type="button"
        className="toolbar-panel-button"
        onClick={onOpenPanel}
        aria-label="Open controls panel"
      >
        ⚙ Controls
      </button>
    </header>
  );
}