import pandas as pd
import streamlit as st

def parse_bom(file):
    """
    Parses a BOM file (.BomDoc, CSV, XLSX) into structured dicts.
    """
    name = file.name.lower()
    try:
        if name.endswith(".bomdoc") or name.endswith(".csv"):
            df = pd.read_csv(file)
        elif name.endswith((".xls",".xlsx")):
            df = pd.read_excel(file)
        else:
            st.warning(f"Unsupported BOM format: {file.name}")
            return []
        # Normalize column names
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        return df.to_dict(orient="records")
    except Exception as e:
        st.error(f"Error parsing BOM file {file.name}: {e}")
        return []

def preview_bom(bom_list, max_rows=10):
    """
    Displays a preview table in Streamlit.
    """
    if not bom_list:
        st.info("No BOM data available.")
        return
    st.subheader("BOM Preview")
    df_preview = pd.DataFrame(bom_list[:max_rows])
    st.table(df_preview)
