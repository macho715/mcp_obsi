import React, { useEffect, useState } from 'react';
import { GraphView } from './components/GraphView';

function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/data/nodes.json').then(res => res.json()),
      fetch('/data/edges.json').then(res => res.json())
    ]).then(([nodesData, edgesData]) => {
      setNodes(nodesData);
      setEdges(edgesData);
      setLoading(false);
    }).catch(err => {
      console.error('Failed to load graph data', err);
      setLoading(false);
    });
  }, []);

  if (loading) return <div>Loading Graph...</div>;

  return (
    <div className="App">
      <GraphView nodes={nodes} edges={edges} />
    </div>
  );
}

export default App;
