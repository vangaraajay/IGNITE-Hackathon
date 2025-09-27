def parse_schematic(file):
    """
    Returns raw text from schematic file.
    For KiCad, SCH, or PDF (text extract only).
    """
    try:
        return file.read().decode(errors="ignore")
    except:
        return ""
