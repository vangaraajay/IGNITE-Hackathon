# streamlit_app.py
import os
import io
import streamlit as st
import pandas as pd
from docx import Document
from docx.shared import Pt
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI

# --- Load .env ---
# Looks for a .env file in the current working directory
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# --- Streamlit page config ---
st.set_page_config(page_title="LoRa PCB Test Procedure Generator", layout="wide")
st.title("Import input files to generate a test procedure")

# --- Sidebar: model settings (no API key input here) ---
st.sidebar.header("Model Settings")
model = st.sidebar.text_input("Model", value="gpt-4.1-mini")
if API_KEY:
    st.sidebar.success("API key loaded from .env", icon="✅")
else:
    st.sidebar.error("OPENAI_API_KEY not found in .env", icon="⚠️")

# --- File uploader ---
uploaded_files = st.file_uploader(
    "Upload multiple files. Include Assembly Testpoint Report (txt), PCB Hardware Specifications (docx), "
    "PCB Software Specifications (docx), BOM Documents (xml/xlsx), Arduino Files (xml), and Schematics (png).",
    accept_multiple_files=True
)

# --- Helpers ---
def text_to_docx(text: str) -> bytes:
    """Convert plain text to a DOCX and return bytes."""
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    for block in text.split("\n\n"):
        p = doc.add_paragraph()
        p.add_run(block)

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.read()

def file_to_text(file) -> str | None:
    """Extract text/summary from supported files for the LLM."""
    name = file.name
    lower = name.lower()

    try:
        if file.type == "text/plain" or lower.endswith(".txt"):
            return file.read().decode("utf-8", errors="ignore")

        if lower.endswith(".xlsx"):
            df = pd.read_excel(file)
            return df.to_csv(index=False)

        if lower.endswith(".csv"):
            df = pd.read_csv(file)
            return df.to_csv(index=False)

        if lower.endswith(".docx"):
            d = Document(file)
            return "\n".join([p.text for p in d.paragraphs])

        if lower.endswith(".xml"):
            return file.read().decode("utf-8", errors="ignore")

        if lower.endswith((".png", ".jpg", ".jpeg")):
            image = Image.open(file)
            return f"Image file: {name}, size: {image.size}, mode: {image.mode}"

        return None
    except Exception as e:
        return f"[Error reading {name}: {e}]"

# Collect texts from uploads
texts = []
if uploaded_files:
    for f in uploaded_files:
        st.write("Processing:", f.name)
        content = file_to_text(f)
        if content:
            texts.append(f"--- File: {f.name} ---\n{content}")
            st.write(f"Processed {f.name}")
        else:
            st.warning(f"Skipping {f.name} (unsupported or empty)")

# Prompt template
BASE_PROMPT = """
You are an experienced electrical engineer tasked with creating a test procedure for a LoRa radio PCB. You will be provided with:

- Type of PCB: LoRa Radio
- BOM Documents
- Assembly Testpoint Report / Netlist
- PCB Hardware Specifications
- PCB Software Specifications
- Schematic Files
- Example output file
These files are here: {FILES_BLOCK}

Your task is to generate a new test case file that in the form of a DOCX document, following these requirements:

1. Strictly follows the format, numbering, headings, and table styles of the example output file.
2. Includes a step-by-step test procedure that an electrical engineer can follow. In the test procedure:
 - Make sure every step in the TEST PROCEDURE is numbered and has a heading (for example, "4.1 - Visual Inspection, and then 4.1.2- Inspect the PCB...)
 - Before powering on UT, verify each power rail is not connected to ground or shorted. Verify each power rail is not connected to another power rail.
 - identify local passive components (resistors, capacitors, inductors) near components that start with "U" (integrated circuits) and "X" (crystals) and include them in the test procedure. Look for easier points to probe, such as test points or vias, and include them in the test procedure.

3. Places special emphasis on voltage guardrail tests:
   - Check power rails at all test points.
   - Specify expected voltages and acceptable tolerances.
   - Include warnings if voltages exceed limits.

4. Covers power-on checks, connectivity tests, functional tests using test cases, and signal verification.
5. Be concise but detailed enough to perform tests without additional guidance.
6. Presents a test data sheet at the end of the document similar to the one in the example output file.
7. Make sure all tables are formatted correctly and the columns are aligned and neat.
8. Put a generous tolerance on the Oscilloscope checks like 10 or 20% tolerance.

Output the result **strictly in the format of the example output file**, including all tables, headings, and numbering.
"""


# Generate button
generated_text = None
docx_bytes = None
generate_disabled = not API_KEY or not texts

if st.button("Generate Test Procedure", type="primary", disabled=generate_disabled):
    if not texts:
        st.error("Please upload the required input files first.")
    elif not API_KEY:
        st.error("Missing OPENAI_API_KEY in .env. Add it and restart the app.")
    else:
        with st.spinner("Calling LLM to generate the test procedure..."):
            try:
                client = OpenAI(api_key=API_KEY)  # or simply OpenAI() to read from env
                lock = "\n\n".join(texts)
                prompt = BASE_PROMPT.format(FILES_BLOCK=files_block)

                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an expert test engineer."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                generated_text = resp.choices[0].message.content or ""
            except Exception as e:
                st.error(f"LLM call failed: {e}")

        if generated_text:
            st.subheader("Generated Procedure (Preview)")
            st.write(generated_text)

            with st.spinner("Building DOCX..."):
                try:
                    docx_bytes = text_to_docx(generated_text)
                    st.download_button(
                        label="⬇️ Download Test Procedure (DOCX)",
                        data=docx_bytes,
                        file_name="LoRa_Test_Procedure.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                except Exception as e:
                    st.error(f"Failed to create DOCX: {e}")

# Help
with st.expander("Troubleshooting / Tips"):
    st.markdown(
        """
- Ensure a `.env` file is present with `OPENAI_API_KEY=sk-...`.
- After creating/updating `.env`, **restart** the Streamlit app so the env var loads.
- If you encounter `proxies`-related errors, pin dependencies (see below).
- Large files: consider trimming to the most relevant sections (BOM, testpoints, specs).
"""
    )
