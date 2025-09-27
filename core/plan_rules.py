from typing import Dict, List, Tuple
from core.detect import representative_pins_for_rail

def build_plan(nets_map: Dict[str, List[Tuple[str,str]]], summary: Dict) -> Dict:
    # 1) Rails table
    rail_rows = []
    rails = summary["rails"][:6]  # keep it readable; can be edited in UI later
    for i, net in enumerate(rails):
        pin_text, val_text = representative_pins_for_rail(net, nets_map, limit=3)
        rail_rows.append({
            "item": "abcdefghijklmnopqrstuvwxyz"[i],
            "pin": pin_text,
            "net": net,
            "value": val_text
        })

    # 2) Steps
    steps = [
        "Set bench supply to the board input and current limit per design.",
        "Power on the UUT and observe current draw.",
        "Measure each voltage rail vs GND at the listed pins and verify within tolerance."
    ]
    for row in rail_rows:
        steps.append(f"Measure {row['net']} at {row['pin']} → expect {row['value']}.")
    if summary["clocks"]:
        steps.append("Set oscilloscope to 1 V/div, 5 µs/div; measurement: frequency on CH1.")
        for clk in summary["clocks"][:2]:
            steps.append(f"Probe {clk} and verify expected frequency (per design).")
    if summary["resets"]:
        for rst in summary["resets"][:2]:
            steps.append(f"Assert {rst} for 10–50 ms then release; confirm devices reset to known state.")

    steps.append("Power off the UUT.")

    # 3) Datasheet rows
    datasheet = []
    base = "4.2"
    for row in rail_rows:
        datasheet.append({
            "section": f"{base}.11.{row['item']}",
            "description": f"{row['net']} Voltage",
            "expected": row["value"]
        })
    if summary["clocks"]:
        datasheet.append({"section": f"{base}.13", "description": "Oscillator Frequency (Y1)", "expected": "Per design"})
        if len(summary["clocks"]) > 1:
            datasheet.append({"section": f"{base}.14", "description": "Oscillator Frequency (Y2)", "expected": "Per design"})
    if summary["resets"]:
        datasheet.append({"section": f"{base}.20", "description": "Reset behavior", "expected": "Device resets to known state"})

    # 4) Assumptions (for transparency)
    assumptions = []
    if any(r["value"] == "TBD" for r in rail_rows):
        assumptions.append("Some rail voltages inferred from names; unspecified values marked TBD.")
    if summary["clocks"] and len(summary["clocks"]) > 2:
        assumptions.append("Only first two clock nets included for brevity.")
    if summary["resets"] and len(summary["resets"]) > 2:
        assumptions.append("Only first two reset nets included for brevity.")

    return {
        "procedure": {"rail_table": rail_rows, "steps": steps},
        "datasheet": datasheet,
        "assumptions": assumptions
    }

def build_coverage_report(summary: Dict, plan: Dict) -> Dict:
    total_rails = len(summary["rails"])
    covered_rails = len(plan["procedure"]["rail_table"])
    clocks = len(summary["clocks"])
    resets = len(summary["resets"])
    buses_present = {k: len(v) for k,v in summary["buses"].items()}
    gaps = []
    if covered_rails < total_rails:
        gaps.append(f"{total_rails - covered_rails} rails not explicitly measured.")
    if clocks == 0:
        gaps.append("No clocks detected/checked.")
    if resets == 0:
        gaps.append("No reset nets detected/checked.")
    if all(v==0 for v in buses_present.values()):
        gaps.append("No interface smoke tests generated (no buses detected).")
    return {
        "coverage": {
            "rails": f"{covered_rails}/{total_rails}",
            "clocks_detected": clocks,
            "resets_detected": resets,
            "buses_detected": buses_present
        },
        "gaps": gaps
    }
