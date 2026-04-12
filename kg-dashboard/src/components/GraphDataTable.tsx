import type { GraphTableRow } from '../types/graph';

interface GraphDataTableProps {
  rows: GraphTableRow[];
  selectedNodeId: string | null;
  onSelectNode: (nodeId: string) => void;
}

export function GraphDataTable({ rows, selectedNodeId, onSelectNode }: GraphDataTableProps) {
  if (rows.length === 0) {
    return (
      <section className="companion-surface" aria-label="Table view">
        <p className="empty-copy">No visible rows are available for the current slice.</p>
      </section>
    );
  }

  return (
    <section className="companion-surface companion-table" aria-label="Table view">
      <div className="companion-table__header">
        <span>Label</span>
        <span>Type</span>
        <span>POL</span>
        <span>POD</span>
        <span>ATD</span>
        <span>ATA</span>
        <span>Degree</span>
      </div>
      {rows.map((row) => (
        <button
          key={row.id}
          type="button"
          className={row.id === selectedNodeId ? 'companion-table__row is-active' : 'companion-table__row'}
          onClick={() => onSelectNode(row.id)}
        >
          <strong>{row.label}</strong>
          <span>{row.type}</span>
          <span>{row.pol || '—'}</span>
          <span>{row.pod || '—'}</span>
          <span>{row.atd || '—'}</span>
          <span>{row.ata || '—'}</span>
          <span>{row.degree}</span>
        </button>
      ))}
    </section>
  );
}

export default GraphDataTable;
