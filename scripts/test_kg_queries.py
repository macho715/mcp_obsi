import os

from rdflib import Graph


def run_queries():
    graph_path = "vault/knowledge_graph.ttl"
    if not os.path.exists(graph_path):
        print(f"오류: {graph_path} 파일을 찾을 수 없습니다. 현재 디렉토리를 확인해주세요.")
        return

    g = Graph()
    print("지식 그래프(TTL)를 로드하는 중입니다. 잠시만 기다려주세요...")
    g.parse(graph_path, format="turtle")
    print(f"로드 완료: 총 {len(g)}개의 트리플이 로드되었습니다.\n")

    # 1. 모든 물류 이슈와 발생한 사이트/창고 조회
    query1 = """
    PREFIX hvdc: <http://hvdc.logistics/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?issueLabel ?locationLabel
    WHERE {
      ?issue rdf:type hvdc:LogisticsIssue ;
             rdfs:label ?issueLabel ;
             hvdc:occursAt ?location .
      ?location rdfs:label ?locationLabel .
    }
    """
    print("-" * 50)
    print("질의 1: 모든 물류 이슈와 발생 장소 (사이트/창고)")
    print("-" * 50)
    results1 = g.query(query1)
    count1 = 0
    for row in results1:
        count1 += 1
        print(f"이슈: {row.issueLabel} | 장소: {row.locationLabel}")
    if count1 == 0:
        print("조건에 맞는 이슈 내역이 없습니다.")

    # 2. 'Hitachi' 벤더의 배송품 중 'SHU' 사이트로 배송된 내역 조회
    query2 = """
    PREFIX hvdc: <http://hvdc.logistics/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?shipmentLabel ?vendorLabel
    WHERE {
      ?shipment rdf:type hvdc:Shipment ;
                rdfs:label ?shipmentLabel ;
                hvdc:suppliedBy ?vendor ;
                hvdc:deliveredTo ?site .
      ?vendor rdfs:label ?vendorLabel .
      ?site rdfs:label "SHU" .
      FILTER(CONTAINS(LCASE(STR(?vendorLabel)), "hitachi"))
    }
    """
    print("\n" + "-" * 50)
    print("질의 2: 'Hitachi' 벤더의 물품 중 'SHU' 사이트로 배송된 내역")
    print("-" * 50)
    results2 = g.query(query2)
    count2 = 0
    for row in results2:
        count2 += 1
        print(f"배송 번호: {row.shipmentLabel} | 벤더명: {row.vendorLabel}")
    if count2 == 0:
        print("조건에 맞는 배송 내역이 없습니다.")

    # 3. 물류 이슈가 가장 많이 발생한 선박 조회
    query3 = """
    PREFIX hvdc: <http://hvdc.logistics/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT ?vesselLabel (COUNT(?issue) AS ?issueCount)
    WHERE {
      ?issue rdf:type hvdc:LogisticsIssue ;
             hvdc:relatedTo ?vessel .
      ?vessel rdf:type hvdc:Vessel ;
              rdfs:label ?vesselLabel .
    }
    GROUP BY ?vesselLabel
    ORDER BY DESC(?issueCount)
    """
    print("\n" + "-" * 50)
    print("질의 3: 물류 이슈가 가장 많이 연관된 선박 (내림차순)")
    print("-" * 50)
    results3 = g.query(query3)
    count3 = 0
    for row in results3:
        count3 += 1
        print(f"선박명: {row.vesselLabel} | 연관된 이슈 수: {row.issueCount}건")
    if count3 == 0:
        print("연관된 이슈가 있는 선박이 없습니다.")


if __name__ == "__main__":
    run_queries()
