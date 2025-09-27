from typing import Dict, List, Tuple
import re

def _has_any(name: str, keys) -> bool:
    u = name.upper()
    return any(k in u for k in keys)

def _prefer_pins(net: str, nets_map: Dict[str, List[Tuple[str,str]]], limit=3):
    conns = nets_map.get(net, [])
    connectors = [(r,p) for r,p in conns if r and (r.startswith("J") or r.startswith("P"))]
    ics = [(r,p) for r,p in conns if r and r.startswith("U")]
    rest = [(r,p) for r,p in conns if (r,p) not in connectors and (r,p) not in ics]
    return (connectors + ics + rest)[:limit]

def _infer_voltage(net: str):
    n = net.upper()
    if "3V3" in n or "+3V3" in n: return 3.3
    if "5V"  in n or "+5V"  in n: return 5.0
    if "1V8" in n or "+1V8" in n: return 1.8
    if "2V5" in n or "+2V5" in n: return 2.5
    return None

def detect_rails(nets_map):
    rails = []
    for n in nets_map:
        u = n.upper()
        if u.startswith(("+","VCC","VDD","VIN","VBAT")) or u in {"PWR_JACK","VCC","VIN","VBAT"}:
            rails.append(n)
    return sorted(set(rails))

def detect_grounds(nets_map):
    return sorted([n for n in nets_map if re.search(r"(^GND|GND$|_GND|GND_)", n.upper())])

def detect_clocks(nets_map):
    keys = ["OSC","XTAL","XIN","XOUT","CLK","SWCLK","JTCK","TCK"]
    return sorted([n for n in nets_map if _has_any(n, keys)])

def detect_resets(nets_map):
    keys = ["RESET","RST","NRST","NRESET","RESET#","RESET_N"]
    return sorted([n for n in nets_map if _has_any(n, keys)])

def detect_buses(nets_map):
    i2c = [n for n in nets_map if re.search(r"\bSCL\b|\bSDA\b", n.upper())]
    spi = [n for n in nets_map if re.search(r"\bMOSI\b|\bMISO\b|\bSCK\b|\bCS\b", n.upper())]
    uart = [n for n in nets_map if re.search(r"\bTX\b|\bRX\b", n.upper())]
    can = [n for n in nets_map if re.search(r"\bCANH\b|\bCANL\b", n.upper())]
    usb = [n for n in nets_map if re.search(r"\bUSB_DP\b|\bUSB_DM\b|USB\+", n.upper())]
    return {"i2c": sorted(set(i2c)), "spi": sorted(set(spi)),
            "uart": sorted(set(uart)), "can": sorted(set(can)), "usb": sorted(set(usb))}

def detect_summary(nets_map):
    return {
        "nets": nets_map,
        "rails": detect_rails(nets_map),
        "grounds": detect_grounds(nets_map),
        "clocks": detect_clocks(nets_map),
        "resets": detect_resets(nets_map),
        "buses": detect_buses(nets_map)
    }

def representative_pins_for_rail(net, nets_map, limit=3):
    pins = _prefer_pins(net, nets_map, limit=limit)
    pin_text = "; ".join([f"{r} pin {p.lstrip('-')}" for r,p in pins]) if pins else "TBD"
    volts = _infer_voltage(net)
    val_text = f"{volts}V ±100mV" if volts is not None else "TBD"
    return pin_text, val_text
