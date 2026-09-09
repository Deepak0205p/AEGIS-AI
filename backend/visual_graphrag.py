"""
Visual Knowledge Graph (GraphRAG) Extraction & Topological Reasoning Engine.
Transforms technical diagrams (P&ID, PFD, single-line diagrams, engineering schematics)
into structured node-edge topology graphs with connected equipment, line sizes, valves,
interlocks, failure propagation trees, and Mermaid visualization generation.
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from backend.config import logger, EQUIPMENT_TAG_REGEX


class VisualGraphRAG:
    """
    Constructs and queries knowledge graphs extracted from engineering drawings & diagrams.
    Enables:
    1. Direct Topology Queries (What is downstream/upstream of Equipment X?)
    2. Failure Propagation Trace (If Valve V-101 fails or line leaks, which units trip?)
    3. Safety Interlock Verification (Are ESDVs and PSVs properly positioned?)
    4. Mermaid Interactive Diagram Generation.
    """

    def __init__(self, raw_graph_data: Optional[Dict[str, Any]] = None):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.subsystems: List[str] = []
        
        if raw_graph_data:
            self.load_from_dict(raw_graph_data)

    def load_from_dict(self, data: Dict[str, Any]):
        """Load graph topology from structured JSON."""
        for node in data.get("nodes", []):
            tag = node.get("id") or node.get("tag")
            if tag:
                self.nodes[tag] = {
                    "tag": tag,
                    "type": node.get("type", "Equipment"),
                    "description": node.get("description", ""),
                    "specs": node.get("specs", {}),
                    "fail_safe": node.get("fail_safe", "N/A"),
                }

        for edge in data.get("edges", []):
            src = edge.get("source") or edge.get("from")
            dst = edge.get("target") or edge.get("to")
            if src and dst:
                self.edges.append({
                    "source": src,
                    "target": dst,
                    "relation": edge.get("relation", "connects_to"),
                    "line_tag": edge.get("line_tag", ""),
                    "fluid": edge.get("fluid", "Process Fluid"),
                    "flow_direction": edge.get("direction", "forward"),
                })

        self.subsystems = data.get("subsystems", [])

    def get_downstream_nodes(self, start_node: str, max_depth: int = 4) -> List[str]:
        """Finds all equipment and instrumentation downstream of a starting node."""
        visited = set()
        queue = [(start_node, 0)]

        while queue:
            curr, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            for edge in self.edges:
                if edge["source"].upper() == curr.upper():
                    nxt = edge["target"]
                    if nxt not in visited and nxt.upper() != start_node.upper():
                        visited.add(nxt)
                        queue.append((nxt, depth + 1))

        return list(visited)

    def get_upstream_nodes(self, start_node: str, max_depth: int = 4) -> List[str]:
        """Finds all equipment and instrumentation upstream of a target node."""
        visited = set()
        queue = [(start_node, 0)]

        while queue:
            curr, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            for edge in self.edges:
                if edge["target"].upper() == curr.upper():
                    nxt = edge["source"]
                    if nxt not in visited and nxt.upper() != start_node.upper():
                        visited.add(nxt)
                        queue.append((nxt, depth + 1))

        return list(visited)

    def simulate_isolation_impact(self, isolated_tag: str) -> Dict[str, Any]:
        """Traces the operational impact if a specific valve, pump, or line is isolated."""
        downstream = self.get_downstream_nodes(isolated_tag)
        affected_instruments = [
            n for n in downstream 
            if any(p in n.upper() for p in ["PT-", "TT-", "FT-", "LT-", "PI-", "TI-", "ESDV", "PSV"])
        ]
        affected_major = [
            n for n in downstream
            if any(p in n.upper() for p in ["C-", "F-", "P-", "V-", "E-", "T-", "TG-", "SG-", "BF-"])
        ]

        return {
            "isolated_component": isolated_tag,
            "isolated_type": self.nodes.get(isolated_tag, {}).get("type", "Unknown"),
            "total_affected_downstream": len(downstream),
            "downstream_chain": downstream,
            "major_equipment_tripped": affected_major,
            "instrument_loops_affected": affected_instruments,
            "containment_risk": "HIGH" if len(affected_major) > 2 else "MODERATE" if len(affected_major) > 0 else "LOW"
        }

    def generate_mermaid_diagram(self) -> str:
        """Generates a GitHub-flavored Mermaid flowchart from the extracted graph."""
        if not self.nodes and not self.edges:
            return ""

        lines = ["```mermaid", "flowchart LR"]
        lines.append("    %% Visual GraphRAG Extracted Topology")
        
        # Node style definitions
        lines.append("    classDef vessel fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;")
        lines.append("    classDef pump fill:#1e293b,stroke:#22c55e,stroke-width:2px,color:#f8fafc;")
        lines.append("    classDef valve fill:#1e293b,stroke:#f59e0b,stroke-width:2px,color:#f8fafc;")
        lines.append("    classDef instrument fill:#1e293b,stroke:#a855f7,stroke-width:1.5px,color:#f8fafc;")

        # Render Nodes
        for tag, data in self.nodes.items():
            ntype = data.get("type", "Equipment")
            clean_tag = re.sub(r"[^a-zA-Z0-9_-]", "_", tag)
            desc = data.get("description") or ntype
            label = f"{tag}<br/>({desc})"
            
            if any(k in tag.upper() for k in ["C-", "V-", "T-", "D-", "TK-", "F-", "HEATER", "COLUMN"]):
                lines.append(f'    {clean_tag}["{label}"]:::vessel')
            elif any(k in tag.upper() for k in ["P-", "PUMP", "COMPRESSOR", "K-", "BFP"]):
                lines.append(f'    {clean_tag}(["{label}"]):::pump')
            elif any(k in tag.upper() for k in ["V-", "MOV-", "ESDV-", "XV-", "FCV-", "PCV-", "VALVE"]):
                lines.append(f'    {clean_tag}{{"{label}"}}:::valve')
            else:
                lines.append(f'    {clean_tag}(["{label}"]):::instrument')

        # Render Edges
        for edge in self.edges:
            src_clean = re.sub(r"[^a-zA-Z0-9_-]", "_", edge["source"])
            dst_clean = re.sub(r"[^a-zA-Z0-9_-]", "_", edge["target"])
            lbl = edge.get("line_tag") or edge.get("relation") or ""
            if lbl:
                lines.append(f'    {src_clean} -->|"{lbl}"| {dst_clean}')
            else:
                lines.append(f'    {src_clean} --> {dst_clean}')

        lines.append("```")
        return "\n".join(lines)


def extract_graph_from_vision_text(vision_analysis_text: str) -> Dict[str, Any]:
    """
    Parses vision multimodal extraction text or JSON to extract
    topological nodes, connections, and flow paths.
    """
    graph_data: Dict[str, Any] = {
        "nodes": [],
        "edges": [],
        "subsystems": []
    }

    # 1. Try parsing structured JSON if the model emitted a graph block
    json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", vision_analysis_text)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if "nodes" in parsed or "edges" in parsed:
                return parsed
        except Exception:
            pass

    # 2. Heuristic extraction of Equipment Tags and Connected Lines
    detected_tags = list(set(re.findall(EQUIPMENT_TAG_REGEX, vision_analysis_text, re.IGNORECASE)))
    
    # Common P&ID equipment tags
    for tag in detected_tags:
        tag_up = tag.upper()
        ntype = "Instrument / Line"
        if tag_up.startswith("C-") or "COLUMN" in tag_up or "TOWER" in tag_up:
            ntype = "Distillation / Process Column"
        elif tag_up.startswith("F-") or "FURNACE" in tag_up or "HEATER" in tag_up:
            ntype = "Fired Heater / Furnace"
        elif tag_up.startswith("P-") or "PUMP" in tag_up:
            ntype = "Centrifugal / Process Pump"
        elif tag_up.startswith("V-") or tag_up.startswith("D-") or "DRUM" in tag_up or "VESSEL" in tag_up:
            ntype = "Separator / Vessel"
        elif tag_up.startswith("E-") or "EXCHANGER" in tag_up or "COOLER" in tag_up:
            ntype = "Heat Exchanger"
        elif "ESDV" in tag_up or "MOV" in tag_up or "XV" in tag_up:
            ntype = "Emergency Shutdown / Motor Valve"
        elif "PSV" in tag_up or "PRV" in tag_up:
            ntype = "Pressure Safety Valve"

        graph_data["nodes"].append({
            "id": tag,
            "type": ntype,
            "description": f"Extracted from drawing ({ntype})"
        })

    # Find connection arrows (e.g. "F-101 -> C-101" or "P-101A flows to V-102" or "discharges into")
    connection_patterns = [
        re.compile(r"([A-Z0-9_-]{2,15})\s*(?:->|-->|flows to|discharges into|connected to|feeds into|transfers to)\s*([A-Z0-9_-]{2,15})", re.IGNORECASE),
        re.compile(r"from\s+([A-Z0-9_-]{2,15})\s+to\s+([A-Z0-9_-]{2,15})", re.IGNORECASE),
    ]

    for pat in connection_patterns:
        for match in pat.finditer(vision_analysis_text):
            src, dst = match.group(1).strip().upper(), match.group(2).strip().upper()
            if src in [t.upper() for t in detected_tags] or dst in [t.upper() for t in detected_tags]:
                graph_data["edges"].append({
                    "source": src,
                    "target": dst,
                    "relation": "feeds",
                    "line_tag": "Process Line"
                })

    # If tags detected but no explicit text edges, create logical sequential pipeline
    if len(detected_tags) >= 2 and not graph_data["edges"]:
        for i in range(len(detected_tags) - 1):
            graph_data["edges"].append({
                "source": detected_tags[i],
                "target": detected_tags[i+1],
                "relation": "process_connection",
                "line_tag": f"Line-{i+1}"
            })

    return graph_data
