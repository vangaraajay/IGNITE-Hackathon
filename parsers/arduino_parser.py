import pandas as pd
import streamlit as st

def parse_arduino_xlsx(file):
    """
    Reads Arduino test cases from XLSX.
    Returns a list of dicts with test name, input, expected, etc.
    """
    try:
        df = pd.read_excel(file)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        return df.to_dict(orient="records")
    except Exception as e:
        st.error(f"Failed to parse Arduino test case file {file.name}: {e}")
        return []
