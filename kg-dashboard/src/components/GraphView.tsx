import { useEffect, useMemo, useRef } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import type cytoscape from 'cytoscape';
import type { GraphEdge, GraphNode, GraphViewMode } from '../types/graph';
import { getCollapsedCountLabel, getEdgeId, getNodeLabel } from '../utils/graph-model';

function getEdgeCompareKey(edge: GraphEdge): string {
  return `${edge.data.source}|${edge.data.target}`;
}

interface GraphViewProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  compareDiff?: {
    addedNodeIds: Set<string>;
    removedNodeIds: Set<string>;
    changedNodeIds: Set<string>;
    addedEdgeIds: Set<string>;
    removedEdgeIds: Set<string>;
    changedEdgeIds: Set<string>;
  } | null;
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  viewMode: GraphViewMode;
  hubThreshold: number;
  degreeById: Map<string, number>;
  onSelectNode: (nodeId: string | null) => void;
  onSelectEdge: (edgeId: string | null) => void;
}

export function GraphView({
  nodes,
  edges,
  selectedNodeId,
  selectedEdgeId,
  viewMode,
  hubThreshold,
  degreeById,
  onSelectNode,
  onSelectEdge,
  compareDiff = null,
}: GraphViewProps) {
  const cyRef = useRef<cytoscape.Core | null>(null);
  const selectedNode = useMemo(
    () => nodes.find((node) => node.data.id === selectedNodeId) ?? null,
    [nodes, selectedNodeId],
  );
  const modeLabel =
    viewMode === 'summary' ? 'Summary layout' : viewMode === 'search' ? 'Search layout' : 'Ego layout';

  const nodeTypeById = useMemo(
    () => new Map(nodes.map((node) => [node.data.id, node.data.type])),
    [nodes],
  );

  const elements = useMemo(() => {
    const normalizedNodes = nodes.map((node) => ({
      ...node,
      selected: node.data.id === selectedNodeId,
      classes: [
        `node-${String(node.data.type).toLowerCase()}`,
        (degreeById.get(node.data.id) ?? 0) >= hubThreshold ? 'hub-node' : '',
        viewMode === 'summary' && getCollapsedCountLabel(node) ? 'collapsed-summary-node' : '',
        compareDiff?.addedNodeIds.has(node.data.id) ? 'compare-node-added' : '',
        compareDiff?.removedNodeIds.has(node.data.id) ? 'compare-node-removed' : '',
        compareDiff?.changedNodeIds.has(node.data.id) ? 'compare-node-changed' : '',
      ]
        .filter(Boolean)
        .join(' '),
      data: {
        ...node.data,
        displayLabel:
          viewMode === 'summary' && getCollapsedCountLabel(node)
            ? `${getNodeLabel(node)}\n${getCollapsedCountLabel(node)}`
            : getNodeLabel(node),
      },
    }));

    const normalizedEdges = edges.map((edge) => ({
      ...edge,
      selected: getEdgeId(edge) === selectedEdgeId,
      classes:
        [
          nodeTypeById.get(edge.data.source) === 'LogisticsIssue' ||
          nodeTypeById.get(edge.data.target) === 'LogisticsIssue'
            ? 'issue-edge'
            : '',
          getEdgeId(edge) === selectedEdgeId ? 'selected-edge' : '',
          compareDiff?.addedEdgeIds.has(getEdgeCompareKey(edge)) ? 'compare-edge-added' : '',
          compareDiff?.removedEdgeIds.has(getEdgeCompareKey(edge)) ? 'compare-edge-removed' : '',
          compareDiff?.changedEdgeIds.has(getEdgeCompareKey(edge)) ? 'compare-edge-changed' : '',
        ]
          .filter(Boolean)
          .join(' '),
      data: {
        ...edge.data,
        id: getEdgeId(edge),
      },
    }));

    return [...normalizedNodes, ...normalizedEdges];
  }, [
    compareDiff,
    degreeById,
    edges,
    hubThreshold,
    nodeTypeById,
    nodes,
    selectedEdgeId,
    selectedNodeId,
    viewMode,
  ]);

  const stylesheet = useMemo<cytoscape.StylesheetStyle[]>(
    () => [
      {
        selector: 'node',
        style: {
          label: 'data(displayLabel)',
          'text-wrap': 'wrap',
          'text-max-width': '120px',
          'text-valign': 'bottom',
          'text-margin-y': 8,
          'font-size': nodes.length > 80 ? 11 : 13,
          'min-zoomed-font-size': nodes.length > 80 ? 12 : 0,
          'font-weight': 'normal',
          color: '#111827',
          'text-outline-width': 3,
          'text-outline-color': '#f7f5ef',
          'background-color': '#a8a29e',
          width: 20,
          height: 20,
          'border-width': 1.5,
          'border-color': '#f8fafc',
        },
      },
      {
        selector: 'node:selected',
        style: {
          'border-width': 4,
          'border-color': '#0f172a',
          'z-index': 999,
        },
      },
      {
        selector: 'node.hub-node',
        style: {
          width: 34,
          height: 34,
          'font-size': 14,
          'font-weight': 'bold',
        },
      },
      {
        selector: 'node.collapsed-summary-node',
        style: {
          'text-wrap': 'wrap',
          'text-max-width': '170px',
          'font-size': 12,
          'text-margin-y': 12,
        },
      },
      {
        selector: 'node[type = "LogisticsIssue"]',
        style: {
          'background-color': '#df4a3a',
          shape: 'round-rectangle',
          width: 34,
          height: 34,
        },
      },
      {
        selector: 'node[type = "Shipment"]',
        style: {
          'background-color': '#2b6cb0',
          width: 18,
          height: 18,
        },
      },
      {
        selector: 'node[type = "Vessel"]',
        style: {
          'background-color': '#c97a10',
          shape: 'diamond',
          width: 24,
          height: 24,
        },
      },
      {
        selector: 'node[type = "Site"]',
        style: {
          'background-color': '#0f9d7a',
          shape: 'hexagon',
          width: 28,
          height: 28,
        },
      },
      {
        selector: 'node[type = "Warehouse"]',
        style: {
          'background-color': '#4f772d',
          shape: 'round-rectangle',
          width: 28,
          height: 28,
        },
      },
      {
        selector: 'node[type = "Hub"]',
        style: {
          'background-color': '#111827',
          color: '#111827',
          shape: 'star',
          width: 44,
          height: 44,
        },
      },
      {
        selector: 'edge',
        style: {
          width: 1,
          'line-color': '#d4d4d8',
          'curve-style': 'bezier',
          opacity: 0.7,
          'target-arrow-color': '#d4d4d8',
          'target-arrow-shape': 'triangle',
        },
      },
      {
        selector: 'edge.issue-edge',
        style: {
          width: 2,
          'line-color': '#f5b4a9',
          'target-arrow-color': '#f5b4a9',
          opacity: 0.9,
        },
      },
      {
        selector: 'edge.selected-edge',
        style: {
          width: 3,
          'line-color': '#0f766e',
          'target-arrow-color': '#0f766e',
          opacity: 1,
        },
      },

      {
        selector: 'node.compare-node-added',
        style: {
          'border-width': 4,
          'border-color': '#15803d',
        },
      },
      {
        selector: 'node.compare-node-removed',
        style: {
          'border-width': 4,
          'border-color': '#b91c1c',
          'border-style': 'dashed',
          opacity: 0.75,
        },
      },
      {
        selector: 'node.compare-node-changed',
        style: {
          'border-width': 4,
          'border-color': '#d97706',
        },
      },
      {
        selector: 'edge.compare-edge-added',
        style: {
          width: 3,
          'line-color': '#15803d',
          'target-arrow-color': '#15803d',
          opacity: 1,
        },
      },
      {
        selector: 'edge.compare-edge-removed',
        style: {
          width: 3,
          'line-color': '#b91c1c',
          'target-arrow-color': '#b91c1c',
          'line-style': 'dashed',
          opacity: 0.85,
        },
      },
      {
        selector: 'edge.compare-edge-changed',
        style: {
          width: 3,
          'line-color': '#d97706',
          'target-arrow-color': '#d97706',
          opacity: 1,
        },
      },
    ],
    [nodes.length],
  );

  const layout = useMemo(() => {
    if (viewMode === 'ego') {
      return {
        name: 'breadthfirst',
        fit: true,
        padding: 24,
        directed: false,
        spacingFactor: 0.9,
      };
    }

    if (viewMode === 'search') {
      return {
        name: 'concentric',
        fit: true,
        padding: 24,
        spacingFactor: 0.85,
        concentric: (element: cytoscape.NodeSingular) => degreeById.get(element.id()) ?? 1,
        levelWidth: () => 2,
      };
    }

    return {
      name: 'concentric',
      fit: true,
      padding: 32,
      minNodeSpacing: 16,
      spacingFactor: 0.9,
      concentric: (element: cytoscape.NodeSingular) => degreeById.get(element.id()) ?? 1,
      levelWidth: () => 3,
    };
  }, [degreeById, viewMode]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) {
      return;
    }

    const handleNodeTap = (event: cytoscape.EventObject) => {
      onSelectNode(event.target.id());
    };
    const handleEdgeTap = (event: cytoscape.EventObject) => {
      const tappedEdgeId = event.target.data('id') as string | undefined;
      onSelectEdge(tappedEdgeId ?? null);
    };
    const handleCanvasTap = (event: cytoscape.EventObject) => {
      if (event.target === cy) {
        onSelectEdge(null);
        onSelectNode(null);
      }
    };

    cy.on('tap', 'node', handleNodeTap);
    cy.on('tap', 'edge', handleEdgeTap);
    cy.on('tap', handleCanvasTap);

    return () => {
      cy.off('tap', 'node', handleNodeTap);
      cy.off('tap', 'edge', handleEdgeTap);
      cy.off('tap', handleCanvasTap);
    };
  }, [onSelectEdge, onSelectNode]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy || !selectedNodeId) {
      return;
    }

    const selected = cy.$id(selectedNodeId);
    if (selected.nonempty()) {
      cy.animate({
        center: { eles: selected },
        duration: 180,
      });
    }
  }, [selectedNodeId]);

  return (
    <div className="graph-canvas-shell" role="application" aria-label="Knowledge graph canvas">
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: '0 0 auto 0',
          zIndex: 4,
          display: 'flex',
          justifyContent: 'space-between',
          gap: '1rem',
          padding: '0.85rem 1rem',
          color: '#334155',
          fontSize: '0.8rem',
          lineHeight: 1.4,
          pointerEvents: 'none',
        }}
      >
        <span>{selectedNode ? getNodeLabel(selectedNode) : `${nodes.length} nodes · ${edges.length} edges`}</span>
        <span>
          {modeLabel}
          {' · '}
          Tap a node to inspect, tap empty space to clear.
        </span>
      </div>
      <CytoscapeComponent
        elements={elements}
        stylesheet={stylesheet}
        layout={layout}
        style={{ width: '100%', height: '100%' }}
        cy={(cy) => {
          cyRef.current = cy;
        }}
      />
    </div>
  );
}

export default GraphView;
