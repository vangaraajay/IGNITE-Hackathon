from typing import Dict, List, Any, Tuple
from parsers import ipc_parser, bom_parser, schematic_parser, arduino_parser

# --------------------
# Helper functions
# --------------------

def summarize_nets(nets_map: Dict[str, List[Tuple[str,str]]]):
    """Summarize nets into rails, grounds, and clocks."""
    rails = [n for n in nets_map if n.upper().startswith(("+","VCC","VDD","VIN","VBAT"))]
    grounds = [n for n in nets_map if "GND" in n.upper()]
    clocks = [n for n in nets_map if any(k in n.upper() for k in ["OSC","XTAL","CLK"])]
    return {"rails": rails, "grounds": grounds, "clocks": clocks}

def extract_voltages_from_bom(bom_data: List[Dict[str, Any]]):
    """Infer net voltages from power-related components in the BOM."""
    voltages = {}
    import re
    for part in bom_data:
        net = part.get("net")
        val = part.get("value", "")
        ptype = part.get("type", "").lower()
        if net and ptype == "regulator":
            m = re.search(r"(\d+(\.\d+)?)V", val)
            if m:
                volts = float(m.group(1))
                voltages[net] = f"{volts}V ±5%"
    return voltages

def compose_arduino_text(arduino_cases: List[Dict[str, Any]]) -> str:
    """Convert Arduino test cases to human-readable steps."""
    lines = []
    for i, case in enumerate(arduino_cases, start=1):
        name = case.get("test_name", f"Test {i}")
        inp = case.get("input", "N/A")
        expected = case.get("expected", "N/A")
        lines.append(f"{i}. {name}: Apply {inp}, expect {expected}.")
    return "\n".join(lines)

def compose_schematic_summary(schematic_texts: List[str]) -> str:
    """Combine multiple schematic file outputs into a single summary."""
    lines = []
    for i, text in enumerate(schematic_texts, start=1):
        lines.append(f"--- Schematic File {i} ---")
        lines.append(text[:1000])  # first 1000 chars or summary
    return "\n".join(lines)

# --------------------
# Main composer
# --------------------

def compose_all(
    ipc_file,
    bom_file,
    schematic_files: List[Any],
    arduino_xlsx_file
) -> Dict[str, Any]:
    """
    Parse IPC, BOM, schematics, and Arduino XLSX, pre-compose
    nets/rails/voltages, and Arduino test steps for LLM input.
    """

    # --- IPC ---
    ipc_text = ipc_file.read().decode(errors="ignore").splitlines()

    nets_map = ipc_parser.parse_ipc356_lines(ipc_text)
    nets_summary = summarize_nets(nets_map)

    # --- BOM ---
    bom_data = bom_parser.parse_bom(bom_file)
    voltages_from_bom = extract_voltages_from_bom(bom_data)

    # --- Schematics ---
    schematic_texts = [schematic_parser.parse_schematic(f) for f in schematic_files]
    schematic_summary = compose_schematic_summary(schematic_texts)

    # --- Arduino XLSX ---
    arduino_cases = arduino_parser.parse_arduino_xlsx(arduino_xlsx_file)
    arduino_text = compose_arduino_text(arduino_cases)

    # --- Compose final dictionary for LLM ---
    llm_payload = {
        "nets_map": nets_map,
        "nets_summary": nets_summary,
        "voltages_from_bom": voltages_from_bom,
        "bom": bom_data,
        "schematic_summary": schematic_summary,
        "arduino_cases": arduino_cases,
        "arduino_text": arduino_text
    }

    return llm_payload


def build_plan(nets_map, rails, clocks, bom=None, hardware="", software="", schematic="", example_output=None, arduino_cases=None):
    """Create a minimal bring-up plan dictionary suitable for the Streamlit UI.

    This is intentionally simple: it infers rail voltages from the BOM when
    available and composes a small set of sanity-check steps plus any Arduino
    test case descriptions.
    """
    bom = bom or []
    arduino_cases = arduino_cases or []

    voltages = extract_voltages_from_bom(bom)

    # Use nets_map to add known pins/counts if available
    net_counts = {k: len(v) for k, v in (nets_map or {}).items()} if nets_map else {}

    # Build a small rail table
    rail_table = []
    for idx, net in enumerate(rails, start=1):
        rail_table.append({
            "item": f"Rail {idx}",
            "pin": "",
            "net": net,
            "value": voltages.get(net, "")
        })

    # Basic steps
    steps = []
    if rail_table:
        steps.append("Verify all voltage rails are present and within tolerance.")
        for r in rail_table:
            steps.append(f"Measure {r['net']} on {r['item']} and confirm {r['value'] or 'expected voltage' }.")

    if clocks:
        steps.append("Verify clock sources are oscillating and within spec.")

    if hardware:
        steps.append("Perform basic smoke and connectivity checks per hardware spec.")

    if software:
        steps.append("Load firmware/bootloader and verify boot messages where applicable.")

    # If schematic text provided, add a short note referencing it
    if schematic:
        steps.append("Refer to schematic summary for net-to-pin mapping and component references.")

    # Arduino cases appended as steps
    for j, case in enumerate(arduino_cases, start=1):
        name = case.get("test_name", f"Arduino Test {j}")
        steps.append(f"Run {name} and verify expected behaviour.")

    # Simple datasheet composed from BOM voltages
    datasheet = []
    for r in rail_table:
        desc = f"Check net {r['net']}"
        if r['net'] in net_counts:
            desc += f" (mapped pins: {net_counts[r['net']]})"
        datasheet.append({
            "section": r["item"],
            "description": desc,
            "expected": r.get("value", "")
        })

    # Include example_output in datasheet if present (simple merge)
    if example_output:
        datasheet.append({
            "section": "ExampleOutput",
            "description": "Reference example DOCX provided",
            "expected": "See example"
        })

    return {
        "procedure": {
            "rail_table": rail_table,
            "steps": steps
        },
        "datasheet": datasheet
    }
