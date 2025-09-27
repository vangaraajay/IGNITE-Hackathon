import re
from typing import Dict, List, Tuple, Iterable

TOKEN_RE = re.compile(r"\s+")

def _strip_prefix_digits(net: str) -> str:
    return re.sub(r"^\d+", "", net)

def parse_ipc356_lines(lines: Iterable[str]) -> Dict[str, List[Tuple[str,str]]]:
    nets: Dict[str, List[Tuple[str,str]]] = {}
    for raw in lines:
        line = raw.rstrip("\n")
        if not line or line.startswith(("C ","P ")):  # comment/header
            continue
        parts = TOKEN_RE.split(line.strip())
        if len(parts) < 3:
            continue
        raw_net, refdes, pin = parts[0], parts[1], parts[2]
        net = _strip_prefix_digits(raw_net)
        if net.upper() in ("N/C","NC"):
            continue
        nets.setdefault(net, []).append((refdes, pin))
    return nets

def summarize(nets: Dict[str, List[Tuple[str,str]]]):
    def has_any(name: str, keys): 
        u=name.upper()
        return any(k in u for k in keys)
    rails = [n for n in nets if n.upper().startswith(("+","VCC","VDD","VIN","VBAT")) or n.upper() in {"PWR_JACK","VCC","VIN","VBAT"}]
    grounds = [n for n in nets if "GND" in n.upper()]
    clocks = [n for n in nets if has_any(n, ["OSC","XTAL","CLK"])]
    return {"rails": rails, "grounds": grounds, "clocks": clocks}
