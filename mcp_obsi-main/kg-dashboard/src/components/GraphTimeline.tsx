import type { GraphTimelineRow } from '../types/graph';

interface GraphTimelineProps {
  rows: GraphTimelineRow[];
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
}

export function GraphTimeline({ rows, selectedNodeId, onSelectNode }: GraphTimelineProps) {
  if (rows.length === 0) {
    return (
      <section className="companion-surface" aria-label="Timeline view">
        <p className="empty-copy">No shipment timing rows are available for the current slice.</p>
      </section>
    );
  }

  return (
    <section className="companion-surface timeline-list" aria-label="Timeline view">
      {rows.map((row) => (
        <button
          key={row.id}
          type="button"
          className={row.id === selectedNodeId ? 'timeline-row is-active' : 'timeline-row'}
          onClick={() => onSelectNode(row.id)}
        >
          <strong>{row.label}</strong>
          <span>ATD {row.atd || '—'}</span>
          <span>ATA {row.ata || '—'}</span>
          <span>{row.status}</span>
        </button>
      ))}
    </section>
  );
}

export default GraphTimeline;
