import type { GraphNode } from '../types/graph';
import { getCollapsedCountSummary } from '../utils/graph-model';

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

function formatCount(value: number | null): string {
  return typeof value === 'number' ? new Intl.NumberFormat('en-US').format(value) : '—';
}

function buildObsidianOpenHref(vault: string, file: string): string {
  return `obsidian://open?vault=${encodeURIComponent(vault)}&file=${encodeURIComponent(file)}`;
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

  const analysisVault = typeof node.data.analysisVault === 'string' ? node.data.analysisVault : null;
  const analysisPath = typeof node.data.analysisPath === 'string' ? node.data.analysisPath : null;
  const obsidianPath =
    (node.data.type === 'LogisticsIssue' || node.data.type === 'IncidentLesson') &&
    analysisVault &&
    analysisPath
      ? { vault: analysisVault, file: analysisPath }
      : null;
  const collapsedCounts = getCollapsedCountSummary(node);
  const extraFields = Object.entries(node.data)
    .filter(([key, value]) => !STANDARD_FIELDS.has(key) && value !== undefined && value !== null)
    .sort(([left], [right]) => left.localeCompare(right));
  const resolvedLabel = node.data['rdf-schema#label'] ?? 'Not provided';
  const degreeLabel = formatCount(degree);
  const summaryRows = [
    ['Label', node.data.label],
    ['Resolved label', resolvedLabel],
    ['Degree', degreeLabel],
  ];

  if (collapsedCounts) {
    summaryRows.push(
      ['Collapsed shipments', formatCount(collapsedCounts.shipment)],
      ['Collapsed vessels', formatCount(collapsedCounts.vessel)],
      ['Collapsed vendors', formatCount(collapsedCounts.vendor)],
    );
  }

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

      <p className="panel-copy">
        {node.data.type} node · {degreeLabel} connections
        {obsidianPath ? ` · linked note ${analysisPath}` : ''}
      </p>

      <div className="inspector-badges">
        <span className="pill pill--accent">{node.data.type}</span>
        <span className="pill">{node.data.id}</span>
      </div>

      <section className="field-list" aria-label="Node summary">
        {summaryRows.map(([key, value]) => (
          <div className="field-list__row" key={key}>
            <span className="field-list__key">{key}</span>
            <span className="field-list__value">{value}</span>
          </div>
        ))}
      </section>

      {obsidianPath ? (
        <a
          className="obsidian-link"
          href={buildObsidianOpenHref(obsidianPath.vault, obsidianPath.file)}
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
