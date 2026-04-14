# KG Visualization Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 물류 및 HVDC 프로젝트의 지식 그래프(TTL)를 브라우저에서 고속으로 렌더링하고 필터링할 수 있는 인메모리 시각화 대시보드를 구축합니다.

**Architecture:** Python `rdflib`를 사용해 TTL 파일을 브라우저가 소비하기 쉬운 정적 JSON(nodes.json, edges.json)으로 사전 변환합니다. 프론트엔드는 Vite React와 Cytoscape.js를 사용하여 백엔드 서버 없이 정적 JSON 에셋을 메모리에 로드하고, 클라이언트 자원만으로 고속 렌더링 및 필터링을 수행합니다.

**Tech Stack:** Python (rdflib, pytest), React (Vite, TypeScript), Cytoscape.js, react-cytoscapejs

---

### Task 1: Python TTL to JSON 파서 (TTL to JSON Parser)

**Files:**
- Create: `scripts/ttl_to_json.py`
- Create: `tests/test_ttl_to_json.py`

- [ ] **Step 1: 실패하는 테스트 작성 (Write the failing test)**

```python
# tests/test_ttl_to_json.py
import os
import json
from scripts.ttl_to_json import parse_ttl

def test_parse_ttl(tmp_path):
    ttl_content = """
    @prefix ex: <http://example.org/> .
    ex:Issue1 a ex:LogisticsIssue ;
              ex:name "Port Delay" .
    ex:Shipment1 a ex:Shipment ;
                 ex:hasIssue ex:Issue1 .
    """
    ttl_file = tmp_path / "test.ttl"
    ttl_file.write_text(ttl_content)
    
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    
    parse_ttl(str(ttl_file), str(out_dir))
    
    nodes_file = out_dir / "nodes.json"
    edges_file = out_dir / "edges.json"
    
    assert nodes_file.exists()
    assert edges_file.exists()
    
    nodes = json.loads(nodes_file.read_text(encoding="utf-8"))
    edges = json.loads(edges_file.read_text(encoding="utf-8"))
    
    assert len(nodes) == 2
    assert any(n["data"]["id"] == "http://example.org/Issue1" for n in nodes)
    assert len(edges) == 1
    assert edges[0]["data"]["source"] == "http://example.org/Shipment1"
    assert edges[0]["data"]["target"] == "http://example.org/Issue1"
```

- [ ] **Step 2: 테스트 실행 및 실패 확인 (Run test to verify it fails)**

Run: `pytest tests/test_ttl_to_json.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.ttl_to_json'`

- [ ] **Step 3: 최소 구현 작성 (Write minimal implementation)**

```python
# scripts/ttl_to_json.py
import json
import os
from rdflib import Graph, URIRef, BNode

def parse_ttl(ttl_path: str, output_dir: str):
    g = Graph()
    g.parse(ttl_path, format="turtle")
    
    nodes_dict = {}
    edges = []
    
    for s, p, o in g:
        s_str = str(s)
        o_str = str(o)
        
        if s_str not in nodes_dict:
            nodes_dict[s_str] = {"data": {"id": s_str, "label": s_str.split("/")[-1], "type": "Unknown"}}
            
        if str(p) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type":
            nodes_dict[s_str]["data"]["type"] = o_str.split("/")[-1]
        elif isinstance(o, (URIRef, BNode)):
            if o_str not in nodes_dict:
                nodes_dict[o_str] = {"data": {"id": o_str, "label": o_str.split("/")[-1], "type": "Unknown"}}
            edges.append({"data": {"source": s_str, "target": o_str, "label": str(p).split("/")[-1]}})
        else:
            nodes_dict[s_str]["data"][str(p).split("/")[-1]] = o_str

    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, "nodes.json"), "w", encoding="utf-8") as f:
        json.dump(list(nodes_dict.values()), f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(output_dir, "edges.json"), "w", encoding="utf-8") as f:
        json.dump(edges, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        parse_ttl(sys.argv[1], sys.argv[2])
```

- [ ] **Step 4: 테스트 통과 확인 (Run test to verify it passes)**

Run: `pytest tests/test_ttl_to_json.py -v`
Expected: PASS

- [ ] **Step 5: 커밋 (Commit)**

```bash
git add scripts/ttl_to_json.py tests/test_ttl_to_json.py
git commit -m "feat: add python ttl to json parser"
```

### Task 2: React 앱 초기화 및 패키지 설치 (React App Init & Packages)

**Files:**
- Create: `kg-dashboard/package.json`
- Create: `kg-dashboard/vite.config.ts`

- [ ] **Step 1: Vite React TypeScript 템플릿으로 프로젝트 생성 (Create Project)**

```bash
npm create vite@latest kg-dashboard -- --template react-ts
cd kg-dashboard
npm install
```

- [ ] **Step 2: 시각화 및 스타일링 패키지 설치 (Install dependencies)**

```bash
cd kg-dashboard
npm install cytoscape react-cytoscapejs
npm install -D @types/cytoscape @types/react-cytoscapejs
```

- [ ] **Step 3: 정적 에셋 폴더 구성 (Setup static assets)**

```bash
cd kg-dashboard
mkdir -p public/data
echo "[]" > public/data/nodes.json
echo "[]" > public/data/edges.json
```

- [ ] **Step 4: 앱 빌드 확인 (Verify build)**

```bash
cd kg-dashboard && npm run build
```
Expected: PASS (build successful)

- [ ] **Step 5: 커밋 (Commit)**

```bash
git add kg-dashboard/
git commit -m "chore: initialize vite react app for kg-dashboard"
```

### Task 3: Cytoscape.js 그래프 뷰어 컴포넌트 (Graph Viewer Component)

**Files:**
- Create: `kg-dashboard/src/components/GraphView.tsx`
- Modify: `kg-dashboard/src/App.tsx`

- [ ] **Step 1: GraphView 컴포넌트 구현 (Implement GraphView)**

```tsx
// kg-dashboard/src/components/GraphView.tsx
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
```

- [ ] **Step 2: App.tsx에서 데이터 로드 및 렌더링 (Load data and render in App.tsx)**

```tsx
// kg-dashboard/src/App.tsx
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
```

- [ ] **Step 3: 타입스크립트 컴파일 확인 (Verify TypeScript compilation)**

```bash
cd kg-dashboard && npx tsc
```
Expected: PASS (No errors)

- [ ] **Step 4: 커밋 (Commit)**

```bash
git add kg-dashboard/src/components/GraphView.tsx kg-dashboard/src/App.tsx
git commit -m "feat: add cytoscape graph view component"
```

### Task 4: 엔티티 컬러 코딩 및 스타일링 (Entity Color Coding)

**Files:**
- Modify: `kg-dashboard/src/components/GraphView.tsx`

- [ ] **Step 1: 스타일시트 배열 정의 및 적용 (Define stylesheet array)**

```tsx
// kg-dashboard/src/components/GraphView.tsx
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
```

- [ ] **Step 2: 타입스크립트 컴파일 확인 (Verify TypeScript compilation)**

```bash
cd kg-dashboard && npx tsc
```
Expected: PASS

- [ ] **Step 3: 커밋 (Commit)**

```bash
git add kg-dashboard/src/components/GraphView.tsx
git commit -m "style: apply color coding based on entity type"
```

### Task 5: 레이아웃 패널 및 필터링 기능 (Layout Panel & Filtering)

**Files:**
- Modify: `kg-dashboard/src/App.tsx`
- Modify: `kg-dashboard/src/components/GraphView.tsx`

- [ ] **Step 1: App.tsx에 사이드바 및 필터 상태 추가 (Add sidebar & filter state)**

```tsx
// kg-dashboard/src/App.tsx
import React, { useEffect, useState } from 'react';
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
```

- [ ] **Step 2: GraphView.tsx에 노드 클릭 이벤트 및 상세 패널 추가 (Add node click details)**

```tsx
// kg-dashboard/src/components/GraphView.tsx
import React, { useState } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import { Stylesheet } from 'cytoscape';

interface GraphViewProps {
  nodes: any[];
  edges: any[];
}

export const GraphView: React.FC<GraphViewProps> = ({ nodes, edges }) => {
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
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
```

- [ ] **Step 3: 앱 빌드 확인 (Verify build)**

```bash
cd kg-dashboard && npx tsc && npm run build
```
Expected: PASS

- [ ] **Step 4: 커밋 (Commit)**

```bash
git add kg-dashboard/src/App.tsx kg-dashboard/src/components/GraphView.tsx
git commit -m "feat: add sidebar filtering and node details panel"
```