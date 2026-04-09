import React from 'react';
import CytoscapeComponent from 'react-cytoscapejs';

interface GraphViewProps {
  nodes: any[];
  edges: any[];
}

export const GraphView: React.FC<GraphViewProps> = ({ nodes, edges }) => {
  const elements = [...nodes, ...edges];

  return (
    <div style={{ width: '100%', height: '100vh', border: '1px solid #ccc' }}>
      <CytoscapeComponent
        elements={elements}
        style={{ width: '100%', height: '100%' }}
        layout={{ name: 'cose' }}
      />
    </div>
  );
};
