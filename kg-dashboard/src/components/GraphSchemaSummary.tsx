import type { GraphSchemaSummaryRow } from '../types/graph';

interface GraphSchemaSummaryProps {
  nodeTypes: GraphSchemaSummaryRow[];
  edgeTypes: GraphSchemaSummaryRow[];
}

export function GraphSchemaSummary({ nodeTypes, edgeTypes }: GraphSchemaSummaryProps) {
  return (
    <section className="companion-surface schema-grid" aria-label="Schema summary view">
      <div className="schema-group">
        <div className="panel-header">
          <div>
            <div className="section-label">Schema</div>
            <h2 className="section-title">Node types</h2>
          </div>
        </div>
        {nodeTypes.length > 0 ? (
          nodeTypes.map((row) => (
            <div className="schema-row" key={`node-${row.type}`}>
              <span>{row.type}</span>
              <strong>{row.count}</strong>
            </div>
          ))
        ) : (
          <p className="empty-copy">No node types are visible in the current slice.</p>
        )}
      </div>
      <div className="schema-group">
        <div className="panel-header">
          <div>
            <div className="section-label">Schema</div>
            <h2 className="section-title">Edge types</h2>
          </div>
        </div>
        {edgeTypes.length > 0 ? (
          edgeTypes.map((row) => (
            <div className="schema-row" key={`edge-${row.type}`}>
              <span>{row.type}</span>
              <strong>{row.count}</strong>
            </div>
          ))
        ) : (
          <p className="empty-copy">No edge types are visible in the current slice.</p>
        )}
      </div>
    </section>
  );
}

export default GraphSchemaSummary;
