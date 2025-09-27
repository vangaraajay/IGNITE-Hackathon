import streamlit as st
import io, json

from ipc_parser import parse_ipc356_lines, summarize
from composer import build_plan
from llm_drafter import maybe_refine_with_llm

st.set_page_config(page_title="Bring-Up AI (Streamlit)", layout="centered")
st.title("Bring-Up AI — Streamlit MVP")

st.write("Upload an IPC-356 testpoint report (.ipc/.txt). The app parses nets, "
         "extracts likely rails/grounds/clocks, and drafts a bring-up procedure.")

use_llm = st.toggle("Use LLM to refine step wording (optional)", value=False)

file = st.file_uploader("Upload IPC-356 file", type=["ipc","txt"])

if file is not None:
    text = file.read().decode(errors="ignore").splitlines()
    nets_map = parse_ipc356_lines(text)
    summary = summarize(nets_map)

    st.subheader("Detected Nets (summary)")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Rails", len(summary["rails"]))
    with c2: st.metric("Grounds", len(summary["grounds"]))
    with c3: st.metric("Clocks", len(summary["clocks"]))

    with st.expander("Show sample rails/grounds/clocks"):
        st.write({
            "rails": summary["rails"][:10],
            "grounds": summary["grounds"][:10],
            "clocks": summary["clocks"][:10]
        })

    # Build deterministic plan, then optionally refine with LLM
    base_plan = build_plan(nets_map, summary["rails"], summary["clocks"])
    plan = maybe_refine_with_llm(base_plan, enable=use_llm)

    st.subheader("Draft Bring-Up Procedure")
    # Render rail table
    st.markdown("**Voltage Rails to Check**")
    rail_rows = plan["procedure"]["rail_table"]
    st.table([{k:v for k,v in r.items()} for r in rail_rows])

    # Steps
    st.markdown("**Steps**")
    for i, step in enumerate(plan["procedure"]["steps"], start=1):
        st.markdown(f"{i}. {step}")

    # Datasheet
    st.markdown("---")
    st.markdown("**Appendix: Test Datasheet**")
    st.table(plan["datasheet"] or [])

    # Downloads: JSON / CSV / Markdown
    # JSON
    st.download_button("Download Plan JSON", data=json.dumps(plan, indent=2), file_name="plan.json", mime="application/json")

    # CSV for datasheet
    import csv
    import pandas as pd
    df = pd.DataFrame(plan["datasheet"] or [])
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button("Download Datasheet CSV", data=csv_buf.getvalue(), file_name="datasheet.csv", mime="text/csv")

    # Markdown
    def plan_to_md(p):
        lines = ["# Bring-Up Procedure", "", "## Voltage Rails to Check"]
        lines.append("| Item | Pin | Net | Value |")
        lines.append("|---|---|---|---|")
        for r in p["procedure"]["rail_table"]:
            lines.append(f"| {r['item']} | {r['pin']} | {r['net']} | {r['value']} |")
        lines.append("")
        lines.append("## Steps")
        for i, s in enumerate(p["procedure"]["steps"], 1):
            lines.append(f"{i}. {s}")
        lines.append("")
        lines.append("## Appendix: Test Datasheet")
        lines.append("| Section | Description | Expected |")
        lines.append("|---|---|---|")
        for row in p["datasheet"]:
            lines.append(f"| {row.get('section','')} | {row.get('description','')} | {row.get('expected','')} |")
        return "\n".join(lines)

    md = plan_to_md(plan)
    st.download_button("Download Markdown", data=md, file_name="bringup.md", mime="text/markdown")
else:
    st.info("Upload an IPC-356 file to begin.")
