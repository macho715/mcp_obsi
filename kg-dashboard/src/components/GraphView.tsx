import React, { useState } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';

interface GraphViewProps {
  nodes: any[];
  edges: any[];
}

export const GraphView: React.FC<GraphViewProps> = ({ nodes, edges }) => {
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const elements = [...nodes, ...edges];

  const stylesheet: any[] = [
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

  const handleNodeClick = (event: any) => {
    setSelectedNode(event.target.data());
  };

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', position: 'relative' }}>
      <CytoscapeComponent
        elements={elements}
        stylesheet={stylesheet}
        style={{ width: '100%', height: '100%', flex: 1 }}
        layout={{ name: 'cose', padding: 50 }}
        cy={(cy) => {
          cy.on('tap', 'node', handleNodeClick);
          cy.on('tap', (event) => {
            if (event.target === cy) setSelectedNode(null);
          });
        }}
      />
      {selectedNode && (
        <div style={{ position: 'absolute', right: '20px', top: '20px', width: '250px', padding: '15px', background: 'white', border: '1px solid #ccc', borderRadius: '4px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
          <h4 style={{ marginTop: 0 }}>{selectedNode.label}</h4>
          <p><strong>Type:</strong> {selectedNode.type}</p>
          <p><strong>ID:</strong> <span style={{ fontSize: '10px', wordBreak: 'break-all' }}>{selectedNode.id}</span></p>
          {selectedNode.type === 'LogisticsIssue' && (
             <a href={`obsidian://open?vault=mcp_obsidian&file=vault/mcp_raw/${selectedNode.label}`} target="_blank" rel="noreferrer" style={{ color: '#1890ff', textDecoration: 'underline' }}>원본 Markdown 보기</a>
          )}
        </div>
      )}
    </div>
  );
};
