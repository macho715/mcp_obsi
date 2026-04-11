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
