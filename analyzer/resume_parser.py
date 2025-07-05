import pdfplumber
import docx
import re
from typing import Union, IO

def extract_text_from_pdf(pdf_file_path):
    """Extracts text from a PDF file given its path."""
    text = ""
    with pdfplumber.open(pdf_file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_docx(docx_file_path):
    """Extracts text from a DOCX file given its path."""
    try:
        doc = docx.Document(docx_file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""

def extract_text_from_file(file_path_or_stream, filename=None):
    """
    Extracts text from either PDF or DOCX file.
    Can handle file paths or file streams.
    """
    # Determine file type
    if filename:
        file_ext = filename.lower().split('.')[-1]
    elif hasattr(file_path_or_stream, 'name'):
        file_ext = file_path_or_stream.name.lower().split('.')[-1]
    else:
        # Try to detect from content
        file_ext = 'pdf'  # Default to PDF
    
    try:
        if file_ext == 'docx':
            return extract_text_from_docx(file_path_or_stream)
        else:  # Default to PDF
            return extract_text_from_pdf(file_path_or_stream)
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""