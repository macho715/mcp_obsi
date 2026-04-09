import { useEffect, useState } from 'react';
import { GraphView } from './components/GraphView';

function App() {
  const [nodes, setNodes] = useState<any[]>([]);
  const [edges, setEdges] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [focusIssue, setFocusIssue] = useState(false);

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

  const filteredNodes = focusIssue 
    ? nodes.filter(n => n.data.type === 'LogisticsIssue' || edges.some(e => (e.data.source === n.data.id || e.data.target === n.data.id) && nodes.find(ni => ni.data.id === (e.data.source === n.data.id ? e.data.target : e.data.source))?.data.type === 'LogisticsIssue'))
    : nodes;

  const filteredEdges = focusIssue
    ? edges.filter(e => filteredNodes.some(n => n.data.id === e.data.source) && filteredNodes.some(n => n.data.id === e.data.target))
    : edges;

  if (loading) return <div>Loading Graph...</div>;

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <div style={{ width: '300px', padding: '20px', borderRight: '1px solid #ccc', background: '#f5f5f5' }}>
        <h3>지식 그래프 필터</h3>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
          <input 
            type="checkbox" 
            checked={focusIssue} 
            onChange={e => setFocusIssue(e.target.checked)} 
          />
          이슈 중심 보기 (Focus Mode)
        </label>
      </div>
      <div style={{ flex: 1 }}>
        <GraphView nodes={filteredNodes} edges={filteredEdges} />
      </div>
    </div>
  );
}

export default App;
