import streamlit as st
import pandas as pd
from docx import Document
from PIL import Image


st.title("Import the input files to generate a test procedure.")

uploaded_files = st.file_uploader("Upload multiple files. Include Assembly Testpoint Report(txt), PCB Hardware Specifications(docx), PCB Software Specifications(docx), BOM Documents(xml), Arduino Files(xml), and the Schematics (png)", accept_multiple_files=True)

if uploaded_files:
    texts = []

    for file in uploaded_files:
        filename = file.name.lower()

        st.write("Processing:", file.name)
        if file.type == "text/plain":
            content = file.read().decode("utf-8")
        elif filename.endswith(".txt"):
            content = file.read().decode("utf-8")
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(file)
            content = df.decode("utf-8")
        elif filename.endswith(".docx"):
            doc = Document(file)
            content = "\n".join([para.text for para in doc.paragraphs])
        elif filename.endswith(".png"):
            image = Image.open(file)
            content = f"Image file: {file.name}, size: {image.size}, mode: {image.mode}"
        else:
            content = None
            st.warning(f"Skipping {file.name}, unsupported type")
        

        if content:
            texts.append(f"--- File: {file.name} ---\n{content}")
        st.write(f"Processed {file.name}")

    # Reset pointer if needed
