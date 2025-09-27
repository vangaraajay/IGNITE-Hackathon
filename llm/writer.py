import json, os
from typing import Dict

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

# Simple system prompt that preserves structure but improves wording
SYSTEM_PROMPT = """You refine bring-up procedures from structured netlists.
- Only use nets and pins provided in the input JSON.
- Keep rail_table entries identical.
- Improve step wording for clarity; do not add or remove steps dramatically.
- Return JSON with the same keys: procedure{rail_table,steps}, datasheet, assumptions.
"""

def maybe_refine_with_llm(plan: Dict, enable: bool) -> Dict:
    if not enable or OpenAI is None:
        return plan
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return plan
    client = OpenAI(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(plan)}
            ]
        )
        content = resp.choices[0].message.content
        refined = json.loads(content)
        # basic guard: must preserve keys
        if "procedure" in refined and "datasheet" in refined:
            return refined
    except Exception:
        pass
    return plan
