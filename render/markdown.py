def plan_to_markdown(plan: dict) -> str:
    lines = ["# Bring-Up Procedure", ""]
    lines += ["## Voltage Rails to Check",
              "| Item | Pin | Net | Value |",
              "|---|---|---|---|"]
    for r in plan["procedure"]["rail_table"]:
        lines.append(f"| {r['item']} | {r['pin']} | {r['net']} | {r['value']} |")
    lines.append("")
    lines.append("## Steps")
    for i, s in enumerate(plan["procedure"]["steps"], 1):
        lines.append(f"{i}. {s}")
    lines.append("")
    lines.append("## Appendix: Test Datasheet")
    lines += ["| Section | Description | Expected |",
              "|---|---|---|"]
    for row in plan["datasheet"]:
        lines.append(f"| {row.get('section','')} | {row.get('description','')} | {row.get('expected','')} |")
    if plan.get("assumptions"):
        lines.append("")
        lines.append("## Assumptions")
        for a in plan["assumptions"]:
            lines.append(f"- {a}")
    return "\n".join(lines)
