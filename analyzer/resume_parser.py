import pdfplumber
import docx
import re
from typing import Union, IO, List
from docx.document import Document
from docx.table import Table

def extract_text_from_pdf(pdf_file_path):
    """Extracts text from a PDF file given its path."""
    text = ""
    with pdfplumber.open(pdf_file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_all_text_blocks(doc: Document) -> List[str]:
    """
    Extract all text blocks from DOCX document including paragraphs and table cells.
    Handles complex layouts where names might be in tables or split across elements.
    """
    text_blocks = []
    
    # Extract from paragraphs
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            # Split by newlines to handle multi-line content
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text_blocks.extend(lines)
    
    # Extract from tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                cell_text = cell.text.strip()
                if cell_text:
                    # Split cell content by newlines
                    lines = [line.strip() for line in cell_text.split('\n') if line.strip()]
                    text_blocks.extend(lines)
    
    return text_blocks

def is_valid_name(text: str) -> bool:
    """
    Validate if text looks like a person's name with strict criteria.
    """
    if not text:
        return False
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Split into words
    words = text.split()
    
    # Must have 2-4 words (first, last, optional middle/initial)
    if len(words) < 2 or len(words) > 4:
        return False
    
    # Section header blacklist
    blacklist = {
        'resume', 'cv', 'curriculum vitae', 'phone', 'mobile', 'email', 'e-mail',
        'address', 'linkedin', 'github', 'objective', 'summary', 'profile', 'contact',
        'education', 'experience', 'skills', 'projects', 'certifications', 'certificates',
        'references', 'awards', 'achievements', 'publications', 'languages', 'interests',
        'hobbies', 'volunteer', 'activities', 'professional', 'personal', 'employment',
        'work', 'career', 'qualifications', 'competencies', 'expertise', 'background',
        'training', 'courses', 'coursework', 'portfolio', 'about', 'me', 'myself'
    }
    
    # Check against blacklist (case-insensitive)
    if any(word.lower() in blacklist for word in words):
        return False
    
    # Validate each word
    for word in words:
        # Remove trailing punctuation for validation
        clean_word = word.rstrip('.,;:')
        
        # Must contain only letters, hyphens, apostrophes, periods
        if not re.match(r'^[a-zA-Z\'\.-]+$', clean_word):
            return False
        
        # Must start with a letter
        if not clean_word[0].isalpha():
            return False
        
        # Avoid all-caps words (likely section headers)
        if len(clean_word) > 2 and clean_word.isupper():
            return False
        
        # Avoid single characters (unless it's an initial with period)
        if len(clean_word) == 1 and not word.endswith('.'):
            return False
    
    return True

def contains_job_title_indicator(text: str) -> bool:
    """
    Check if text contains job title indicators that often appear near names.
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Job title patterns
    job_indicators = [
        r'#\s*\w+',  # # registered nurse, # software engineer
        r'@\s*\w+',  # @ company name
        r'\b(position|role|title|job)\b',
        r'\b(engineer|developer|nurse|manager|analyst|designer|consultant)\b',
        r'\b(intern|internship|trainee|graduate|junior|senior|lead)\b',
        r'\b(specialist|coordinator|assistant|associate|director)\b',
        r'\b(student|candidate|applicant|fresher)\b'
    ]
    
    return any(re.search(pattern, text_lower) for pattern in job_indicators)

def extract_name_from_docx_robust(doc: Document) -> str:
    """
    Robust name extraction for complex DOCX layouts using multiple strategies.
    """
    # Extract all text blocks
    text_blocks = extract_all_text_blocks(doc)
    
    # Limit to first 15 blocks (first 1/4 of document typically)
    candidate_blocks = text_blocks[:15]
    
    # Name patterns (case-insensitive)
    patterns = [
        r'^\s*([a-z][a-z\s.\'-]{2,30})\s*$',  # Standalone name
        r'^(?!.*(image|media))([a-z]+\s+[a-z]+)',  # Avoid image tags, capture 2+ words
        r'name[:\s]*([a-z][a-z\s.\'-]{2,30})',  # Labeled name
    ]
    
    candidates = []
    
    # Strategy 1: Look for standalone names in early blocks
    for i, block in enumerate(candidate_blocks):
        # Skip blocks that look like image/media references
        if re.search(r'\b(image|media|photo|picture|img)\b', block, re.IGNORECASE):
            continue
        
        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern, block, re.IGNORECASE)
            if match:
                # Extract the name part
                if len(match.groups()) > 0:
                    candidate = match.group(1).strip()
                else:
                    candidate = match.group(0).strip()
                
                # Validate the candidate
                if is_valid_name(candidate):
                    # Check context (next block for job title indicator)
                    context_score = 0
                    
                    # Check next few blocks for job title context
                    for j in range(i + 1, min(i + 4, len(candidate_blocks))):
                        if contains_job_title_indicator(candidate_blocks[j]):
                            context_score += 2
                            break
                    
                    # Prefer names that appear earlier in document
                    position_score = max(0, 10 - i)
                    
                    # Calculate total score
                    total_score = context_score + position_score
                    
                    candidates.append((candidate, total_score, i))
    
    # Strategy 2: Look for names in labeled format anywhere in first 15 blocks
    for i, block in enumerate(candidate_blocks):
        labeled_match = re.search(r'(?:name|student\s*name|candidate)[:\s]*([a-z][a-z\s.\'-]{2,30})', block, re.IGNORECASE)
        if labeled_match:
            candidate = labeled_match.group(1).strip()
            if is_valid_name(candidate):
                candidates.append((candidate, 15, i))  # High score for labeled names
    
    # Sort candidates by score (highest first)
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Return the best candidate, properly formatted
    if candidates:
        best_candidate = candidates[0][0]
        # Convert to title case for proper name formatting
        return ' '.join(word.capitalize() for word in best_candidate.split())
    
    return "Not detected"

def extract_text_from_docx(docx_file_path):
    """Extracts text from a DOCX file with enhanced name extraction."""
    try:
        doc = docx.Document(docx_file_path)
        
        # Extract name using robust method
        name = extract_name_from_docx_robust(doc)
        
        # Extract all text for general parsing
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
            
        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + "\n"
        
        # Add extracted name to the beginning if detected
        if name != "Not detected":
            text = f"Name: {name}\n\n{text}"
            
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
        # Try to detect from content or default to PDF
        file_ext = 'pdf'
    
    try:
        if file_ext == 'docx':
            # For DOCX files, we need to handle file streams differently
            if hasattr(file_path_or_stream, 'read'):
                # It's a file stream - save to temporary file
                import tempfile
                import os
                
                # Create a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                    # Reset stream position if possible
                    if hasattr(file_path_or_stream, 'seek'):
                        file_path_or_stream.seek(0)
                    
                    # Copy stream content to temp file
                    temp_file.write(file_path_or_stream.read())
                    temp_file_path = temp_file.name
                
                try:
                    # Extract text from temporary file
                    result = extract_text_from_docx(temp_file_path)
                finally:
                    # Clean up temporary file
                    os.unlink(temp_file_path)
                
                return result
            else:
                # It's a file path
                return extract_text_from_docx(file_path_or_stream)
        else:  # Default to PDF
            return extract_text_from_pdf(file_path_or_stream)
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""