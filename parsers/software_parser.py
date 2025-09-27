import docx

def parse_software(file):
    """
    Extracts text from PCB software spec DOCX or TXT.
    """
    ext = file.name.split(".")[-1].lower()
    if ext == "docx":
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    else:
        return file.read().decode(errors="ignore")
