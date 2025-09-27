import re
from typing import Dict, List, Tuple, Iterable

TOKEN_RE = re.compile(r"\s+")

def _strip_prefix_digits(net: str) -> str:
    return re.sub(r"^\d+", "", net)

def parse_ipc356_lines(lines: Iterable[str]) -> Dict[str, List[Tuple[str,str]]]:
    nets: Dict[str, List[Tuple[str,str]]] = {}
    for raw in lines:
        line = raw.rstrip("\n")
        if not line or line.startswith(("C ","P ")):
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
