export type GraphNodeType =
  | 'LogisticsIssue'
  | 'Shipment'
  | 'Vessel'
  | 'Site'
  | 'Warehouse'
  | 'Hub'
  | 'Vendor'
  | 'Order'
  | 'rdf-schema#Class'
  | 'Unknown'
  | string;

export interface GraphNodeData {
  id: string;
  label: string;
  type: GraphNodeType;
  'rdf-schema#label'?: string;
  [key: string]: string | number | boolean | undefined;
}

export interface GraphNode {
  data: GraphNodeData;
}

export interface GraphEdgeData {
  id?: string;
  source: string;
  target: string;
  label?: string;
  evidencePath?: string;
  [key: string]: string | number | boolean | undefined;
}

export interface GraphEdge {
  data: GraphEdgeData;
}

export interface GraphSlice {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphMetrics {
  totalNodes: number;
  totalEdges: number;
  visibleNodes: number;
  visibleEdges: number;
  hiddenNodes: number;
  hiddenEdges: number;
  issueCount: number;
  hubCount: number;
}

export type GraphViewMode = 'summary' | 'issues' | 'search' | 'ego';
export type GraphCompanionView = 'graph' | 'table' | 'timeline' | 'schema';
export type GraphSearchField = 'all' | 'coe' | 'pol' | 'pod' | 'shipMode' | 'atd' | 'ata';
export type OntologyQueryPresetId = 'all' | 'issue_location' | 'shipment_route' | 'vendor_network';

export interface GraphQueryState {
  term: string;
  searchField: GraphSearchField;
  classFilter: string;
  propertyFilter: string;
  relationTypeFilter: string;
}

export interface SavedGraphQuery {
  id: string;
  name: string;
  query: GraphQueryState;
}

export interface GraphSelection {
  nodeId: string | null;
  source: GraphViewMode;
}

export interface GraphIndex {
  adjacency: Map<string, Set<string>>;
  degreeById: Map<string, number>;
  nodeById: Map<string, GraphNode>;
  edgesByNodeId: Map<string, GraphEdge[]>;
}

export interface SearchViewOptions {
  hubThreshold?: number;
  maxNeighborsPerHub?: number;
  searchField?: GraphSearchField;
}

export interface SearchMatch {
  node: GraphNode;
  matchedField: string;
  reasonLabel: string;
}

export interface GraphTableRow {
  id: string;
  label: string;
  type: GraphNodeType;
  pol: string;
  pod: string;
  atd: string;
  ata: string;
  degree: number;
}

export interface GraphTimelineRow {
  id: string;
  label: string;
  atd: string;
  ata: string;
  status: 'unknown' | 'departed' | 'arrived';
}

export interface GraphSchemaSummaryRow {
  type: string;
  count: number;
}
