import type { GraphNode } from '../types/graph';
import { getCollapsedCountSummary, getIssueSlug } from '../utils/graph-model';

export interface NodeInspectorProps {
  node: GraphNode | null;
  degree: number | null;
  onClose: () => void;
}

const STANDARD_FIELDS = new Set([
  'id',
  'label',
  'type',
  'rdf-schema#label',
]);

function formatValue(value: string | number | boolean | undefined): string {
  if (typeof value === 'boolean') {
    return value ? 'true' : 'false';
  }

  if (typeof value === 'number') {
    return new Intl.NumberFormat('en-US').format(value);
  }

  return value ? String(value) : '—';
}

export function NodeInspector({ node, degree, onClose }: NodeInspectorProps) {
  if (!node) {
    return (
      <aside className="panel inspector">
        <div className="panel-header">
          <div>
            <div className="section-label">Inspector</div>
            <h2 className="section-title">No node selected</h2>
          </div>
          <button type="button" className="ghost-button" onClick={onClose}>
            Close
          </button>
        </div>
        <p className="empty-copy">
          Select a node to see its label, type, identifiers, and source-link details.
        </p>
      </aside>
    );
  }

  const issueSlug = node.data.type === 'LogisticsIssue' ? getIssueSlug(node.data.id) : null;
  const obsidianPath = issueSlug ? `vault/wiki/analyses/${issueSlug}.md` : null;
  const collapsedCounts = getCollapsedCountSummary(node);
  const extraFields = Object.entries(node.data)
    .filter(([key, value]) => !STANDARD_FIELDS.has(key) && value !== undefined && value !== null)
    .sort(([left], [right]) => left.localeCompare(right));

  return (
    <aside className="panel inspector">
      <div className="panel-header">
        <div>
          <div className="section-label">Inspector</div>
          <h2 className="section-title">{node.data['rdf-schema#label'] ?? node.data.label}</h2>
        </div>
        <button type="button" className="ghost-button" onClick={onClose}>
          Close
        </button>
      </div>

      <div className="inspector-badges">
        <span className="pill pill--accent">{node.data.type}</span>
        <span className="pill">{node.data.id}</span>
      </div>

      <div className="details-grid">
        <div className="detail-card">
          <span className="detail-card__label">Label</span>
          <strong className="detail-card__value">{node.data.label}</strong>
        </div>
        <div className="detail-card">
          <span className="detail-card__label">Resolved label</span>
          <strong className="detail-card__value">
            {node.data['rdf-schema#label'] ?? 'Not provided'}
          </strong>
        </div>
        <div className="detail-card">
          <span className="detail-card__label">Degree</span>
          <strong className="detail-card__value">
            {typeof degree === 'number' ? new Intl.NumberFormat('en-US').format(degree) : '—'}
          </strong>
        </div>
      </div>

      {collapsedCounts ? (
        <div className="details-grid">
          <div className="detail-card">
            <span className="detail-card__label">Collapsed shipments</span>
            <strong className="detail-card__value">
              {new Intl.NumberFormat('en-US').format(collapsedCounts.shipment)}
            </strong>
          </div>
          <div className="detail-card">
            <span className="detail-card__label">Collapsed vessels</span>
            <strong className="detail-card__value">
              {new Intl.NumberFormat('en-US').format(collapsedCounts.vessel)}
            </strong>
          </div>
          <div className="detail-card">
            <span className="detail-card__label">Collapsed vendors</span>
            <strong className="detail-card__value">
              {new Intl.NumberFormat('en-US').format(collapsedCounts.vendor)}
            </strong>
          </div>
        </div>
      ) : null}

      {obsidianPath ? (
        <a
          className="obsidian-link"
          href={`obsidian://open?vault=mcp_obsidian&file=${obsidianPath}`}
          target="_blank"
          rel="noreferrer"
        >
          Open linked Obsidian note
        </a>
      ) : null}

      {extraFields.length > 0 ? (
        <section className="field-list" aria-label="Node metadata">
          {extraFields.map(([key, value]) => (
            <div className="field-list__row" key={key}>
              <span className="field-list__key">{key}</span>
              <span className="field-list__value">{formatValue(value)}</span>
            </div>
          ))}
        </section>
      ) : (
        <p className="empty-copy">This node has no extra metadata beyond the standard graph fields.</p>
      )}
    </aside>
  );
}
