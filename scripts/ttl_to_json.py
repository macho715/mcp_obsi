"""Legacy TTL-to-JSON renderer.

The canonical export path for shipment-centric TTL exports is
`scripts/build_dashboard_graph_data.py`.
"""

import json
import os
import sys

from rdflib import BNode, Graph, URIRef

DEPRECATED_ENTRYPOINT_MESSAGE = (
    "Deprecated entrypoint: use scripts/build_dashboard_graph_data.py "
    "for shipment-centric TTL exports."
)


def parse_ttl(ttl_path: str, output_dir: str):
    g = Graph()
    g.parse(ttl_path, format="turtle")

    nodes_dict = {}
    edges = []

    for s, p, o in g:
        s_str = str(s)
        o_str = str(o)

        if s_str not in nodes_dict:
            nodes_dict[s_str] = {
                "data": {"id": s_str, "label": s_str.split("/")[-1], "type": "Unknown"}
            }

        if str(p) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type":
            nodes_dict[s_str]["data"]["type"] = o_str.split("/")[-1]
        elif isinstance(o, (URIRef, BNode)):
            if o_str not in nodes_dict:
                nodes_dict[o_str] = {
                    "data": {"id": o_str, "label": o_str.split("/")[-1], "type": "Unknown"}
                }
            edges.append(
                {"data": {"source": s_str, "target": o_str, "label": str(p).split("/")[-1]}}
            )
        else:
            nodes_dict[s_str]["data"][str(p).split("/")[-1]] = o_str

    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, "nodes.json"), "w", encoding="utf-8") as f:
        json.dump(list(nodes_dict.values()), f, ensure_ascii=False, indent=2)

    with open(os.path.join(output_dir, "edges.json"), "w", encoding="utf-8") as f:
        json.dump(edges, f, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    print(DEPRECATED_ENTRYPOINT_MESSAGE)
    if len(args) < 2:
        print("Usage: python scripts/ttl_to_json.py <input.ttl> <output_dir>")
        return 1
    parse_ttl(args[0], args[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
