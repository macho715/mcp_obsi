import type {
  GraphEdge,
  GraphNode,
  GraphSchemaSummaryRow,
  GraphTableRow,
  GraphTimelineRow,
} from '../types/graph';

function asText(value: string | number | boolean | undefined): string {
  return typeof value === 'string' ? value : '';
}

export function buildTableRows(
  nodes: GraphNode[],
  degreeById: Map<string, number>,
): GraphTableRow[] {
  return nodes
    .map((node) => ({
      id: node.data.id,
      label: node.data['rdf-schema#label'] ?? node.data.label,
      type: node.data.type,
      pol: asText(node.data.portOfLoading),
      pod: asText(node.data.portOfDischarge),
      atd: asText(node.data.actualDeparture),
      ata: asText(node.data.actualArrival),
      degree: degreeById.get(node.data.id) ?? 0,
    }))
    .sort((left, right) => right.degree - left.degree || left.label.localeCompare(right.label));
}

export function buildTimelineRows(nodes: GraphNode[]): GraphTimelineRow[] {
  return nodes
    .filter((node) => node.data.type === 'Shipment')
    .map((node) => {
      const atd = asText(node.data.actualDeparture);
      const ata = asText(node.data.actualArrival);
      const status: GraphTimelineRow['status'] = ata
        ? 'arrived'
        : atd
          ? 'departed'
          : 'unknown';

      return {
        id: node.data.id,
        label: node.data['rdf-schema#label'] ?? node.data.label,
        atd,
        ata,
        status,
      };
    })
    .sort((left, right) => left.label.localeCompare(right.label));
}

export function buildSchemaSummaryRows(
  nodes: GraphNode[],
  edges: GraphEdge[],
): {
  nodeTypes: GraphSchemaSummaryRow[];
  edgeTypes: GraphSchemaSummaryRow[];
} {
  const nodeTypeCounts = new Map<string, number>();
  const edgeTypeCounts = new Map<string, number>();

  nodes.forEach((node) => {
    nodeTypeCounts.set(node.data.type, (nodeTypeCounts.get(node.data.type) ?? 0) + 1);
  });

  edges.forEach((edge) => {
    const edgeType = edge.data.label ?? 'unlabeled';
    edgeTypeCounts.set(edgeType, (edgeTypeCounts.get(edgeType) ?? 0) + 1);
  });

  return {
    nodeTypes: [...nodeTypeCounts.entries()]
      .map(([type, count]) => ({ type, count }))
      .sort((left, right) => left.type.localeCompare(right.type)),
    edgeTypes: [...edgeTypeCounts.entries()]
      .map(([type, count]) => ({ type, count }))
      .sort((left, right) => left.type.localeCompare(right.type)),
  };
}
