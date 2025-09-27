import streamlit as st
import io, json, pandas as pd
import sys
from pathlib import Path
from composer import build_plan
from parsers.ipc_parser import parse_ipc356_lines, summarize
from parsers.bom_parser import parse_bom, preview_bom
from parsers.hardware_parser import parse_hardware
from parsers.software_parser import parse_software
from parsers.schematic_parser import parse_schematic
from parsers.output_parser import parse_output
from parsers.arduino_parser import parse_arduino_xlsx
from llm_drafter import maybe_refine_with_llm

# Ensure the repository root is on sys.path when Streamlit runs this file
REPO_ROOT = str(Path(__file__).resolve().parent)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

st.set_page_config(page_title="Bring-Up AI", layout="centered")
st.title("Bring-Up AI — Streamlit MVP")
st.write("Upload PCB files, Example Output DOCX, and Arduino XLSX to generate a test procedure.")

# --- Upload Files ---
ipc_file = st.file_uploader("Upload IPC file", type=["ipc","txt"])
bom_files = st.file_uploader("Upload BOMs", type=["bomdoc"], accept_multiple_files=True)
hardware_file = st.file_uploader("Upload PCB Hardware Specs", type=["docx","txt"])
software_file = st.file_uploader("Upload PCB Software Specs", type=["docx","txt"])
schematic_file = st.file_uploader("Upload Schematic Files", type=["kicad_sch","sch","pdf"])
example_output_file = st.file_uploader("Upload Example Output File (.docx)", type=["docx"])
arduino_file = st.file_uploader("Upload Arduino Test Cases (.xlsx)", type=["xlsx"])

use_llm = st.checkbox("Enable LLM refinement", value=True)

# --- Parse Files ---
nets_map, summary = {}, {"rails": [], "grounds": [], "clocks": []}
if ipc_file:
    ipc_text = ipc_file.read().decode(errors="ignore").splitlines()
    nets_map = parse_ipc356_lines(ipc_text)
    summary = summarize(nets_map)

bom_data = []
if bom_files:
    for f in bom_files:
        bom_data.extend(parse_bom(f))
    preview_bom(bom_data)

hardware_text = parse_hardware(hardware_file) if hardware_file else ""
software_text = parse_software(software_file) if software_file else ""
schematic_text = parse_schematic(schematic_file) if schematic_file else ""
example_output_text = parse_output(example_output_file) if example_output_file else []
arduino_test_cases = parse_arduino_xlsx(arduino_file) if arduino_file else []

# --- Build Plan ---
if ipc_file or bom_files:
    base_plan = build_plan(
        nets_map,
        summary.get("rails", []),
        summary.get("clocks", []),
        bom=bom_data,
        hardware=hardware_text,
        software=software_text,
        schematic=schematic_text,
        example_output=example_output_text,
        arduino_cases=arduino_test_cases
    )
    plan = maybe_refine_with_llm(base_plan, enable=use_llm)

    # --- Display Plan ---
    st.subheader("Draft Bring-Up Procedure")
    st.markdown("**Voltage Rails to Check**")
    st.table([{k:v for k,v in r.items()} for r in plan["procedure"]["rail_table"]])

    st.markdown("**Steps**")
    for step_idx, step in enumerate(plan["procedure"]["steps"], 1):
        st.markdown(f"{step_idx}. {step}")

    st.markdown("---")
    st.markdown("**Appendix: Test Datasheet**")
    st.table(plan.get("datasheet", []))

    # --- Downloads ---
    st.download_button("Download Plan JSON", data=json.dumps(plan, indent=2), file_name="plan.json", mime="application/json")
    df = pd.DataFrame(plan.get("datasheet", []))
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button("Download Datasheet CSV", data=csv_buf.getvalue(), file_name="datasheet.csv", mime="text/csv")

    # Markdown download
    def plan_to_md(p):
        lines = ["# Bring-Up Procedure", "", "## Voltage Rails to Check"]
        lines.append("| Item | Pin | Net | Value |")
        lines.append("|---|---|---|---|")
        for r in p["procedure"]["rail_table"]:
            lines.append(f"| {r['item']} | {r['pin']} | {r['net']} | {r['value']} |")
        lines.append("\n## Steps")
        for md_idx, s in enumerate(p["procedure"]["steps"], 1):
            lines.append(f"{md_idx}. {s}")
        lines.append("\n## Appendix: Test Datasheet")
        lines.append("| Section | Description | Expected |")
        lines.append("|---|---|---|---|")
        for row in p.get("datasheet", []):
            lines.append(f"| {row.get('section','')} | {row.get('description','')} | {row.get('expected','')} |")
        return "\n".join(lines)

    md = plan_to_md(plan)
    st.download_button("Download Markdown", data=md, file_name="bringup.md", mime="text/markdown")

else:
    st.info("Upload at least an IPC file or BOM to begin.")

