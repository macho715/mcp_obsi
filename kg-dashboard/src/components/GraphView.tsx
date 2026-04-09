import React from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import { Stylesheet } from 'cytoscape';

interface GraphViewProps {
  nodes: any[];
  edges: any[];
}

export const GraphView: React.FC<GraphViewProps> = ({ nodes, edges }) => {
  const elements = [...nodes, ...edges];

  const stylesheet: Stylesheet[] = [
    {
      selector: 'node',
      style: {
        'label': 'data(label)',
        'background-color': '#ccc',
        'color': '#333',
        'text-valign': 'bottom',
        'font-size': '12px'
      }
    },
    {
      selector: 'node[type = "LogisticsIssue"]',
      style: { 'background-color': '#ff4d4f' }
    },
    {
      selector: 'node[type = "Shipment"]',
      style: { 'background-color': '#1890ff' }
    },
    {
      selector: 'node[type = "Vessel"]',
      style: { 'background-color': '#fa8c16' }
    },
    {
      selector: 'node[type = "Site"], node[type = "Warehouse"]',
      style: { 'background-color': '#52c41a' }
    },
    {
      selector: 'edge',
      style: {
        'width': 2,
        'line-color': '#999',
        'target-arrow-color': '#999',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'label': 'data(label)',
        'font-size': '10px',
        'text-rotation': 'autorotate'
      }
    }
  ];

  return (
    <div style={{ width: '100%', height: '100vh', display: 'flex' }}>
      <CytoscapeComponent
        elements={elements}
        stylesheet={stylesheet}
        style={{ width: '100%', height: '100%', flex: 1 }}
        layout={{ name: 'cose', padding: 50 }}
      />
    </div>
  );
};