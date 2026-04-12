import { useState } from 'react';

import type { GraphEdge, GraphNode, ProvenanceChain, VisibilityReason } from '../types/graph';
import { getCollapsedCountSummary, getEdgeId } from '../utils/graph-model';

export interface NodeInspectorProps {
  node: GraphNode | null;
  edge: GraphEdge | null;
  degree: number | null;
  provenance?: ProvenanceChain;
  visibilityReasons?: VisibilityReason[];
  onClose: () => void;
}

type InspectorTab = 'node' | 'edge' | 'evidence' | 'related';

const STANDARD_FIELDS = new Set(['id', 'label', 'type', 'rdf-schema#label']);
const HIDDEN_METADATA_FIELDS = new Set([
  'VESSEL NAME/ FLIGHT No.',
  'vesselName',
  'flightNo',
]);
const TABS: Array<{ id: InspectorTab; label: string }> = [
  { id: 'node', label: 'Node' },
  { id: 'edge', label: 'Edge' },
  { id: 'evidence', label: 'Evidence' },
  { id: 'related', label: 'Related' },
];

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

function buildNodeObsidianLink(target: GraphNode | null): { href: string; label: string } | null {
  if (!target) {
    return null;
  }

  const vault = typeof target.data.analysisVault === 'string' ? target.data.analysisVault : null;
  const file = typeof target.data.analysisPath === 'string' ? target.data.analysisPath : null;
  if (!vault || !file) {
    return null;
  }

  return {
    href: buildObsidianOpenHref(vault, file),
    label: getNodeLabel(target),
  };
}

function getNodeLabel(node: GraphNode): string {
  return node.data['rdf-schema#label'] ?? node.data.label ?? node.data.id;
}

export function NodeInspector({
  node,
  edge,
  degree,
  provenance,
  visibilityReasons = [],
  onClose,
}: NodeInspectorProps) {
  const [activeTab, setActiveTab] = useState<InspectorTab>(edge ? 'edge' : 'node');
  const [showWhyVisible, setShowWhyVisible] = useState(false);

  if (!node && !edge) {
    return (
      <aside className="panel inspector">
        <div className="panel-header">
          <div>
            <div className="section-label">Inspector</div>
            <h2 className="section-title">No selection</h2>
          </div>
          <button type="button" className="ghost-button" onClick={onClose}>
            Close
          </button>
        </div>
        <p className="empty-copy">
          Select a node or edge to see its metadata, evidence path, and related context.
        </p>
      </aside>
    );
  }

  const analysisVault = typeof node?.data.analysisVault === 'string' ? node.data.analysisVault : null;
  const analysisPath = typeof node?.data.analysisPath === 'string' ? node.data.analysisPath : null;
  const obsidianPath =
    node &&
    (node.data.type === 'LogisticsIssue' || node.data.type === 'IncidentLesson') &&
    analysisVault &&
    analysisPath
      ? { vault: analysisVault, file: analysisPath }
      : null;
  const collapsedCounts = node ? getCollapsedCountSummary(node) : null;
  const extraFields = node
    ? Object.entries(node.data)
        .filter(
          ([key, value]) =>
            !STANDARD_FIELDS.has(key) &&
            !HIDDEN_METADATA_FIELDS.has(key) &&
            value !== undefined &&
            value !== null,
        )
        .sort(([left], [right]) => left.localeCompare(right))
    : [];
  const evidenceItems: string[] = [];
  if (analysisPath) {
    evidenceItems.push(analysisPath);
  }
  if (typeof edge?.data.evidencePath === 'string' && edge.data.evidencePath.trim()) {
    evidenceItems.push(edge.data.evidencePath);
  }
  const provenanceLinks = [
    { key: 'source', label: 'Source', node: provenance?.source ?? null },
    { key: 'claim', label: 'Claim', node: provenance?.claim ?? null },
    { key: 'issueOrLesson', label: 'Issue / Lesson', node: provenance?.issueOrLesson ?? null },
  ].filter((item) => item.node);

  const summaryRows = node
    ? [
        ['Label', node.data.label],
        ['Resolved label', node.data['rdf-schema#label'] ?? 'Not provided'],
        ['Degree', formatCount(degree)],
      ]
    : [];

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
          <h2 className="section-title">
            {node ? node.data['rdf-schema#label'] ?? node.data.label : edge?.data.label ?? getEdgeId(edge!)}
          </h2>
        </div>
        <button type="button" className="ghost-button" onClick={onClose}>
          Close
        </button>
      </div>

      <p className="panel-copy">
        {node ? `${node.data.type} node` : 'Selected edge'}
        {node ? ` · ${formatCount(degree)} connections` : ''}
      </p>

      <div className="inspector-badges">
        {node ? <span className="pill pill--accent">{node.data.type}</span> : null}
        {node ? <span className="pill">{node.data.id}</span> : null}
        {edge ? <span className="pill">{getEdgeId(edge)}</span> : null}
      </div>
      <button type="button" className="ghost-button" onClick={() => setShowWhyVisible((prev) => !prev)}>
        Why visible?
      </button>
      {showWhyVisible ? (
        visibilityReasons.length > 0 ? (
          <section className="field-list" aria-label="Visibility reasons">
            {visibilityReasons.map((reason) => (
              <div className="field-list__row" key={`${reason.code}-${reason.label}`}>
                <span className="field-list__key">{reason.label}</span>
                <span className="field-list__value">{reason.detail}</span>
              </div>
            ))}
          </section>
        ) : (
          <p className="empty-copy">No specific visibility reason was captured for this selection.</p>
        )
      ) : null}

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

      <div className="segmented-control inspector-tabs" role="tablist" aria-label="Inspector tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={tab.id === activeTab ? 'segmented-control__button is-active' : 'segmented-control__button'}
            onClick={() => setActiveTab(tab.id)}
            aria-pressed={tab.id === activeTab}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {evidenceItems.length > 0 ? (
        <p className="panel-copy">Evidence path · {evidenceItems[0]}</p>
      ) : (
        <p className="empty-copy">No linked evidence is available for this selection.</p>
      )}
      {provenanceLinks.length > 0 ? (
        <section className="field-list" aria-label="Provenance chain preview">
          {provenanceLinks.map((item) => {
            const obsidianLink = buildNodeObsidianLink(item.node ?? null);
            return (
              <div className="field-list__row" key={`preview-${item.key}`}>
                <span className="field-list__key">{item.label}</span>
                <span className="field-list__value">
                  {obsidianLink ? (
                    <a href={obsidianLink.href} target="_blank" rel="noreferrer">
                      {obsidianLink.label}
                    </a>
                  ) : (
                    getNodeLabel(item.node!)
                  )}
                </span>
              </div>
            );
          })}
        </section>
      ) : null}

      {activeTab === 'node' ? (
        node ? (
          <>
            <section className="field-list" aria-label="Node summary">
              {summaryRows.map(([key, value]) => (
                <div className="field-list__row" key={key}>
                  <span className="field-list__key">{key}</span>
                  <span className="field-list__value">{value}</span>
                </div>
              ))}
            </section>

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
          </>
        ) : (
          <p className="empty-copy">No node is selected. Choose a node to inspect node-level details.</p>
        )
      ) : null}

      {activeTab === 'edge' ? (
        edge ? (
          <section className="field-list" aria-label="Edge details">
            <div className="field-list__row">
              <span className="field-list__key">Source</span>
              <span className="field-list__value">{edge.data.source}</span>
            </div>
            <div className="field-list__row">
              <span className="field-list__key">Target</span>
              <span className="field-list__value">{edge.data.target}</span>
            </div>
            <div className="field-list__row">
              <span className="field-list__key">Label</span>
              <span className="field-list__value">{edge.data.label ?? '—'}</span>
            </div>
            <div className="field-list__row">
              <span className="field-list__key">Edge id</span>
              <span className="field-list__value">{getEdgeId(edge)}</span>
            </div>
          </section>
        ) : (
          <p className="empty-copy">No edge is selected. Choose a relation to inspect edge details.</p>
        )
      ) : null}

      {activeTab === 'evidence' ? (
        evidenceItems.length > 0 ? (
          <>
            <section className="field-list" aria-label="Selection evidence">
              {evidenceItems.map((item) => (
                <div className="field-list__row" key={item}>
                  <span className="field-list__key">Path</span>
                  <span className="field-list__value">{item}</span>
                </div>
              ))}
            </section>
            {provenanceLinks.length > 0 ? (
              <section className="field-list" aria-label="Provenance chain">
                {provenanceLinks.map((item) => {
                  const obsidianLink = buildNodeObsidianLink(item.node ?? null);
                  return (
                    <div className="field-list__row" key={item.key}>
                      <span className="field-list__key">{item.label}</span>
                      <span className="field-list__value">
                        {obsidianLink ? (
                          <a href={obsidianLink.href} target="_blank" rel="noreferrer">
                            {obsidianLink.label}
                          </a>
                        ) : (
                          getNodeLabel(item.node!)
                        )}
                      </span>
                    </div>
                  );
                })}
              </section>
            ) : null}
          </>
        ) : (
          <p className="empty-copy">No linked evidence is available for this selection.</p>
        )
      ) : null}

      {activeTab === 'related' ? (
        <section className="field-list" aria-label="Related context">
          {node ? (
            <>
              <div className="field-list__row">
                <span className="field-list__key">Selection kind</span>
                <span className="field-list__value">Node</span>
              </div>
              <div className="field-list__row">
                <span className="field-list__key">Node id</span>
                <span className="field-list__value">{node.data.id}</span>
              </div>
              <div className="field-list__row">
                <span className="field-list__key">Visible reason</span>
                <span className="field-list__value">
                  {analysisPath ? 'Linked analysis note available' : 'Visible in current slice'}
                </span>
              </div>
            </>
          ) : edge ? (
            <>
              <div className="field-list__row">
                <span className="field-list__key">Selection kind</span>
                <span className="field-list__value">Edge</span>
              </div>
              <div className="field-list__row">
                <span className="field-list__key">Source to target</span>
                <span className="field-list__value">{`${edge.data.source} -> ${edge.data.target}`}</span>
              </div>
              <div className="field-list__row">
                <span className="field-list__key">Visible reason</span>
                <span className="field-list__value">Visible relation in current slice</span>
              </div>
            </>
          ) : null}
        </section>
      ) : null}
    </aside>
  );
}

export default NodeInspector;
