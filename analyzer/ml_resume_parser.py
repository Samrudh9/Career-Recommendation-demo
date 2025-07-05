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
        
    def _extract_section_content(self, section_doc):
        """Extract content from a section until the next section header"""
        text = section_doc.text
        
        # Look for next section header pattern
        next_section_match = re.search(r'\n[A-Z][A-Za-z\s]+:', text)
        if next_section_match:
            # Return text until the next section header
            return text[:next_section_match.start()].strip()
        
        # If no next section, return all text
        return text.strip()
    
    def _extract_skills(self, text):
        """Extract skills from the resume text"""
        # Define common skills to look for
        common_skills = [
            "python", "java", "javascript", "html", "css", "react", "angular", "node.js",
            "sql", "mongodb", "mysql", "postgresql", "git", "docker", "kubernetes",
            "aws", "azure", "gcp", "machine learning", "deep learning", "tensorflow",
            "pytorch", "nlp", "data analysis", "data science", "c++", "c#", "go",
            "rust", "php", "ruby", "swift", "kotlin", "flutter", "react native"
        ]
        
        # Find skills in text
        found_skills = []
        text_lower = text.lower()
        
        for skill in common_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                found_skills.append(skill)
                
        return found_skills
    
    def _extract_projects(self, text):
        """Extract project information from resume"""
        # Look for project section
        project_section = ""
        
        # Pattern to find project section
        project_patterns = [
            r'(?:PROJECTS|PROJECT|PERSONAL PROJECTS).*?(?=\n[A-Z][A-Za-z\s]+:|$)',
            r'(?:PROJECTS|PROJECT|PERSONAL PROJECTS).*?(?=\n\n|$)'
        ]
        
        for pattern in project_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                project_section = match.group(0)
                break
        
        return project_section.strip()