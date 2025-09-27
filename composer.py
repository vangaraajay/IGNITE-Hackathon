from typing import Dict, List, Tuple

def infer_voltage_from_name(net: str):
    n = net.upper()
    if "3V3" in n or "+3V3" in n: return 3.3
    if "5V" in n or "+5V" in n: return 5.0
    if "1V8" in n or "+1V8" in n: return 1.8
    if "2V5" in n or "+2V5" in n: return 2.5
    return None

def pick_representative_pins(net: str, nets_map: Dict[str, List[Tuple[str,str]]], limit=3):
    conns = nets_map.get(net, [])
    # prefer connectors J*/P* then ICs U*, then others
    connectors = [(r,p) for r,p in conns if r and (r.startswith("J") or r.startswith("P"))]
    ics = [(r,p) for r,p in conns if r and r.startswith("U")]
    rest = [(r,p) for r,p in conns if (r,p) not in connectors and (r,p) not in ics]
    picks = connectors + ics + rest
    # collapse same refdes into ranges if pins are sequential (simple)
    return picks[:limit]

def to_item_letter(idx: int):
    return "abcdefghijklmnopqrstuvwxyz"[idx]

def build_plan(nets_map: Dict[str, List[tuple]], rails: List[str], clocks: List[str]):
    # Rail table
    rail_rows = []
    for i, net in enumerate(rails[:6]):  # limit to first 6 rails for readability
        pins = pick_representative_pins(net, nets_map, limit=3)
        pin_text = "; ".join([f"{r} pin {p.lstrip('-')}" for r,p in pins]) if pins else "TBD"
        volts = infer_voltage_from_name(net)
        val_text = f"{volts}V ±100mV" if volts is not None else "TBD"
        rail_rows.append({
            "item": to_item_letter(i),
            "pin": pin_text,
            "net": net,
            "value": val_text
        })
    # Steps (basic)
    steps = [
        "Set power supply to the required input voltage and current limit (per board spec).",
        "Power on the unit under test (UUT).",
        "Measure the following voltage rails against GND at the listed pins; verify within tolerance."
    ]
    for row in rail_rows:
        steps.append(f"Measure {row['net']} at {row['pin']} → expect {row['value']}.")
    if clocks:
        steps.append("Set oscilloscope: 1 V/div, 5 µs/div, measure frequency on channel 1.")
        for clk in clocks[:2]:
            steps.append(f"Probe {clk} with CH1 and verify expected frequency (per design).")
    steps.append("Power off the UUT.")
    # Datasheet rows mirror steps (simplified)
    datasheet = []
    sec_base = "4.2"
    seq = 10
    for row in rail_rows:
        datasheet.append({
            "section": f"{sec_base}.11.{row['item']}",
            "description": f"{row['net']} Voltage",
            "expected": row['value']
        })
    if clocks:
        datasheet.append({
            "section": f"{sec_base}.13",
            "description": "Y1 Oscillator Frequency",
            "expected": "Per design (e.g., 16 MHz ±100 kHz)"
        })
        datasheet.append({
            "section": f"{sec_base}.14",
            "description": "Y2 Oscillator Frequency",
            "expected": "Per design (e.g., 32 MHz ±100 kHz)"
        })
    return {
        "procedure": { "rail_table": rail_rows, "steps": steps },
        "datasheet": datasheet
    }
