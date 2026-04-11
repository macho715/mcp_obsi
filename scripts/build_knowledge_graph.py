import os
import glob
import re

import pandas as pd
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS


def build_graph():
    excel_path = "Logi ontol core doc/HVDC STATUS.xlsx"
    if not os.path.exists(excel_path):
        print(f"File not found: {excel_path}")
        return

    print("Loading Excel data...")
    df = pd.read_excel(excel_path)
    
    g = Graph()
    HVDC = Namespace("http://hvdc.logistics/ontology/")
    g.bind("hvdc", HVDC)
    
    # Base Classes
    g.add((HVDC.Shipment, RDF.type, RDFS.Class))
    g.add((HVDC.Order, RDF.type, RDFS.Class))
    g.add((HVDC.Vendor, RDF.type, RDFS.Class))
    g.add((HVDC.Vessel, RDF.type, RDFS.Class))
    g.add((HVDC.Hub, RDF.type, RDFS.Class))
    g.add((HVDC.Warehouse, RDF.type, RDFS.Class))
    g.add((HVDC.Site, RDF.type, RDFS.Class))
    g.add((HVDC.LogisticsIssue, RDF.type, RDFS.Class))

    warehouses = [
        "DSV Indoor", "DSV Outdoor", "DSV MZD", "DSV Kizad", 
        "JDN MZD", "JDN Waterfront", "AAA Storage", "ZENER (WH)", 
        "Hauler DG Storage", "Vijay Tanks"
    ]
    sites = ["SHU", "MIR", "DAS", "AGI"]
    
    print(f"Processing {len(df)} rows from Excel...")
    
    for _idx, row in df.iterrows():
        ship_no = str(row.get("SCT SHIP NO.", "")).strip()
        if not ship_no or ship_no.lower() == "nan" or ship_no == "none":
            continue
            
        ship_uri = URIRef(HVDC[f"shipment/{ship_no.replace(' ', '_')}"])
        g.add((ship_uri, RDF.type, HVDC.Shipment))
        g.add((ship_uri, RDFS.label, Literal(ship_no)))
        
        # hasOrder -> LPO NO
        po_no = str(row.get("PO No.", "")).strip()
        if po_no and po_no.lower() != "nan" and po_no != "none":
            order_uri = URIRef(HVDC[f"order/{po_no.replace(' ', '_')}"])
            g.add((order_uri, RDF.type, HVDC.Order))
            g.add((order_uri, RDFS.label, Literal(po_no)))
            g.add((ship_uri, HVDC.hasOrder, order_uri))
            
        # suppliedBy -> VENDOR
        vendor = str(row.get("VENDOR", "")).strip()
        if vendor and vendor.lower() != "nan" and vendor != "none":
            vendor_uri = URIRef(HVDC[f"vendor/{vendor.replace(' ', '_')}"])
            g.add((vendor_uri, RDF.type, HVDC.Vendor))
            g.add((vendor_uri, RDFS.label, Literal(vendor)))
            g.add((ship_uri, HVDC.suppliedBy, vendor_uri))
            
        # transportedBy -> VESSEL NAME/ FLIGHT No.
        vessel = str(row.get("VESSEL NAME/ FLIGHT No.", "")).strip()
        if vessel and vessel.lower() != "nan" and vessel != "none":
            vessel_uri = URIRef(HVDC[f"vessel/{vessel.replace(' ', '_')}"])
            g.add((vessel_uri, RDF.type, HVDC.Vessel))
            g.add((vessel_uri, RDFS.label, Literal(vessel)))
            g.add((ship_uri, HVDC.transportedBy, vessel_uri))
            
        # consolidatedAt -> Hub (MOSB)
        mosb = str(row.get("MOSB", "")).strip()
        if mosb and mosb.lower() != "nan" and mosb != "none":
            hub_uri = URIRef(HVDC["hub/MOSB"])
            g.add((hub_uri, RDF.type, HVDC.Hub))
            g.add((hub_uri, RDFS.label, Literal("MOSB")))
            g.add((ship_uri, HVDC.consolidatedAt, hub_uri))
            
        # storedAt -> Warehouses
        for wh in warehouses:
            wh_val = str(row.get(wh, "")).strip()
            if wh_val and wh_val.lower() != "nan" and wh_val != "none":
                wh_uri = URIRef(HVDC[f"warehouse/{wh.replace(' ', '_')}"])
                g.add((wh_uri, RDF.type, HVDC.Warehouse))
                g.add((wh_uri, RDFS.label, Literal(wh)))
                g.add((ship_uri, HVDC.storedAt, wh_uri))
                
        # deliveredTo -> Sites
        for site in sites:
            site_val = str(row.get(site, "")).strip()
            if site_val and site_val.lower() != "nan" and site_val != "none":
                site_uri = URIRef(HVDC[f"site/{site.replace(' ', '_')}"])
                g.add((site_uri, RDF.type, HVDC.Site))
                g.add((site_uri, RDFS.label, Literal(site)))
                g.add((ship_uri, HVDC.deliveredTo, site_uri))
                
    print("Processing markdown files from vault/wiki/analyses/...")
    md_files = glob.glob("vault/wiki/analyses/*.md")
    for md_file in md_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Failed to read {md_file}: {e}")
            continue
            
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            continue
            
        frontmatter = match.group(1)
        
        slug_match = re.search(r"^slug:\s*(.+)$", frontmatter, re.MULTILINE)
        title_match = re.search(r"^title:\s*(.+)$", frontmatter, re.MULTILINE)
        
        if not slug_match or not title_match:
            continue
            
        slug = slug_match.group(1).strip().strip("\"'")
        title = title_match.group(1).strip().strip("\"'")
        
        issue_uri = URIRef(HVDC[f"issue/{slug}"])
        g.add((issue_uri, RDF.type, HVDC.LogisticsIssue))
        g.add((issue_uri, RDFS.label, Literal(title)))
        
        tags = []
        in_tags = False
        for line in frontmatter.split('\n'):
            line = line.strip()
            if line.startswith('tags:'):
                in_tags = True
                inline = re.match(r"tags:\s*\[(.*?)\]", line)
                if inline:
                    tags.extend([t.strip().strip("\"'") for t in inline.group(1).split(",") if t.strip()])
                    in_tags = False
            elif in_tags:
                if line.startswith('-'):
                    tags.append(line[1:].strip().strip("\"'"))
                elif line != '' and ':' in line: # simplistic check for exiting list
                    in_tags = False
                    
        for tag in tags:
            t_lower = tag.lower()
            if t_lower in ['shu', 'mir', 'das', 'agi']:
                g.add((issue_uri, HVDC.occursAt, URIRef(HVDC[f"site/{t_lower.upper()}"])))
            elif t_lower == 'jpt71':
                g.add((issue_uri, HVDC.relatedTo, URIRef(HVDC["vessel/JPT71"])))
            elif t_lower in ['abu_dhabi', 'mosb']:
                g.add((issue_uri, HVDC.occursAt, URIRef(HVDC["hub/MOSB"])))
            elif t_lower == 'dsv':
                g.add((issue_uri, HVDC.occursAt, URIRef(HVDC["warehouse/DSV_Indoor"])))

    out_path = "vault/knowledge_graph.ttl"
    os.makedirs("vault", exist_ok=True)
    g.serialize(destination=out_path, format="turtle")
    print(f"Graph built and saved to {out_path}. Total Triples: {len(g)}")

if __name__ == "__main__":
    build_graph()
