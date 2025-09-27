import os, json
from typing import Dict
from openai import OpenAI

SYSTEM_PROMPT = """You refine bring-up procedures from structured netlists.
- Only use nets and pins provided.
- Keep the rail table items identical; you may rewrite step text for clarity.
- Return the same JSON keys you receive, but with improved 'steps' text.
"""

def maybe_refine_with_llm(plan: Dict, enable: bool) -> Dict:
    if not enable:
        return plan
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return plan
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":json.dumps(plan)}
        ]
    )
    try:
        refined = json.loads(resp.choices[0].message.content)
        # only accept if it preserves keys
        if "procedure" in refined and "datasheet" in refined:
            return refined
        return plan
    except Exception:
        return plan
