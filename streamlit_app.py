
import io, json
import pandas as pd
import streamlit as st

from core.ipc_parser import parse_ipc356_lines
from core.detect import detect_summary
from core.plan_rules import build_plan, build_coverage_report
from llm.writer import maybe_refine_with_llm
from render.markdown import plan_to_markdown
from render.docx import plan_to_docx

st.set_page_config(page_title="Ignite Bring-Up", layout="wide")
st.title("Ignite Bring-Up — Streamlit")

st.write("Upload an IPC-356 testpoint report (.ipc/.txt). "
         "We parse connectivity, detect rails/resets/clocks/buses, "
         "and generate a bring-up plan that mirrors the required style.")

colA, colB = st.columns([2,1])
with colB:
    use_llm = st.toggle("Use LLM to refine steps (optional)", value=False)
    docx_export = st.toggle("Enable DOCX export", value=True)

file = st.file_uploader("Upload IPC-356 file", type=["ipc","txt"])
if not file:
    st.info("Tip: after upload you’ll get a plan preview, coverage report, and exports (MD/DOCX/CSV).")
    st.stop()

# 1) Parse
text_lines = file.read().decode(errors="ignore").splitlines()
nets_map = parse_ipc356_lines(text_lines)

# 2) Detect features
summary = detect_summary(nets_map)

with st.expander("Detection summary", expanded=True):
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Rails", len(summary["rails"]))
    c2.metric("Resets", len(summary["resets"]))
    c3.metric("Clocks", len(summary["clocks"]))
    c4.metric("Buses (I²C/SPI/UART/CAN/USB)", sum(len(v) for v in summary["buses"].values()))
    st.write({k: (v if k!="buses" else {kk:v[:8] for kk,v in v.items()})
              for k,v in summary.items() if k!="nets"})

# 3) Compose plan (deterministic) then optional LLM polish
base_plan = build_plan(nets_map, summary)
plan = maybe_refine_with_llm(base_plan, enable=use_llm)

# 4) Coverage & validation
coverage = build_coverage_report(summary, plan)

with st.expander("Coverage & validation", expanded=True):
    st.json(coverage)

# 5) Preview plan
md = plan_to_markdown(plan)
st.subheader("Bring-Up Plan (Preview)")
st.markdown(md)

# 6) Downloads
st.subheader("Downloads")
st.download_button("Download Plan JSON", data=json.dumps(plan, indent=2),
                   file_name="plan.json", mime="application/json")
st.download_button("Download Markdown", data=md,
                   file_name="bringup.md", mime="text/markdown")

# Datasheet CSV
df = pd.DataFrame(plan.get("datasheet", []))
csv_buf = io.StringIO(); df.to_csv(csv_buf, index=False)
st.download_button("Download Datasheet CSV", data=csv_buf.getvalue(),
                   file_name="datasheet.csv", mime="text/csv")

if docx_export:
    docx_bytes = plan_to_docx(plan)
    st.download_button("Download DOCX", data=docx_bytes,
                       file_name="bringup.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
