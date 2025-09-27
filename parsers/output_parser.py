import docx

def parse_output(file):
    """
    Extracts paragraphs from the output file (e.g., example output).
    Returns as a list of strings.
    """
    doc = docx.Document(file)
    return [p.text for p in doc.paragraphs if p.text.strip()]
