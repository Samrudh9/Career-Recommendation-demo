import spacy
from spacy.matcher import Matcher
import re

class MLResumeParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.matcher = Matcher(self.nlp.vocab)
        
        # Add patterns for different sections
        self.matcher.add("EDUCATION", [[{"LOWER": "education"}]])
        self.matcher.add("EXPERIENCE", [[{"LOWER": "experience"}]])
        self.matcher.add("SKILLS", [[{"LOWER": "skills"}]])
        self.matcher.add("CERTIFICATES", [[{"LOWER": "certificates"}]])
        
    def parse_resume(self, text):
        doc = self.nlp(text)
        sections = {}
        
        # Find all section matches
        matches = self.matcher(doc)
        
        # Extract sections
        for match_id, start, end in matches:
            section_name = doc[start:end].text
            section_content = self._extract_section_content(doc[end:])
            sections[section_name.lower()] = section_content
            
        return {
            "contact": self._extract_contact_info(text),
            "education": sections.get("education", ""),
            "experience": sections.get("experience", ""),
            "skills": self._extract_skills(text),
            "certificates": sections.get("certificates", ""),
            "projects": self._extract_projects(text)
        }
        
    def _extract_contact_info(self, text):
        contact = {}
        email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
        phone_pattern = r"\+?\d{10,15}"
        linkedin_pattern = r"linkedin\.com/in/[\w-]+"
        github_pattern = r"github\.com/[\w-]+"
        
        contact["email"] = re.findall(email_pattern, text)
        contact["phone"] = re.findall(phone_pattern, text)
        contact["linkedin"] = re.findall(linkedin_pattern, text)
        contact["github"] = re.findall(github_pattern, text)
        
        return {k: v[0] if v else "" for k, v in contact.items()}