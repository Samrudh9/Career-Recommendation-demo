import spacy
from spacy.matcher import Matcher
import re

class MLResumeParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.matcher = Matcher(self.nlp.vocab)
        
        # Add patterns for different sections
        self.matcher.add("EDUCATION", [[{"LOWER": {"IN": ["education", "academic", "qualification"]}}]])
        self.matcher.add("EXPERIENCE", [[{"LOWER": {"IN": ["experience", "employment", "work history"]}}]])
        self.matcher.add("SKILLS", [[{"LOWER": {"IN": ["skills", "technical skills", "competencies"]}}]])
        self.matcher.add("CERTIFICATES", [[{"LOWER": {"IN": ["certificates", "certifications", "credentials"]}}]])
        self.matcher.add("PROJECTS", [[{"LOWER": {"IN": ["projects", "personal projects", "academic projects"]}}]])
        self.matcher.add("INTERESTS", [[{"LOWER": {"IN": ["interests", "hobbies"]}}]])
        
    def parse_resume(self, text):
        doc = self.nlp(text)
        sections = {}
        
        # Find name with NER
        name = self._extract_name(doc)
        
        # Find all section matches
        matches = self.matcher(doc)
        section_spans = []
        
        for match_id, start, end in matches:
            section_name = doc[start:end].text
            section_spans.append((start, end, section_name))
        
        # Sort by position in text
        section_spans.sort()
        
        # Extract content between sections
        for i, (start, end, section_name) in enumerate(section_spans):
            if i < len(section_spans) - 1:
                next_start = section_spans[i + 1][0]
                section_content = doc[end:next_start].text.strip()
            else:
                section_content = doc[end:].text.strip()
                
            sections[section_name.lower()] = section_content
            
        # Extract skill categories
        skills_data = self._categorize_skills(text)
            
        return {
            "name": name,
            "contact": self._extract_contact_info(text),
            "education": sections.get("education", "") or self._extract_education(text),
            "experience": sections.get("experience", "") or self._extract_experience(text),
            "skills": skills_data,
            "certificates": sections.get("certificates", "") or self._extract_certificates(text),
            "projects": sections.get("projects", "") or self._extract_projects(text),
            "interests": sections.get("interests", "") or self._extract_interests(text)
        }
    
    def _extract_name(self, doc):
        """Extract name using NER"""
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                return ent.text
        
        # Fallback - look at the beginning of the document
        first_line = doc[:20].text.strip().split("\n")[0]
        return first_line
        
    def _extract_contact_info(self, text):
        """Extract contact details with regex patterns"""
        contact = {}
        email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
        phone_pattern = r"(?:\+\d{1,3}[-\s])?\d{10,15}"
        linkedin_pattern = r"(?:linkedin\.com/in/|Linkedin:?)[\w-]+"
        github_pattern = r"(?:github\.com/|Github:?)[\w-]+"
        skype_pattern = r"(?:skype:?|Skype ID:?)[\w-]+"
        
        emails = re.findall(email_pattern, text)
        contact["email"] = emails[0] if emails else ""
        
        phones = re.findall(phone_pattern, text)
        contact["phone"] = phones[0] if phones else ""
        
        linkedins = re.findall(linkedin_pattern, text, re.IGNORECASE)
        if linkedins:
            contact["linkedin"] = linkedins[0].replace("Linkedin:", "").replace("LinkedIn:", "").strip()
        else:
            contact["linkedin"] = ""
            
        githubs = re.findall(github_pattern, text, re.IGNORECASE)
        if githubs:
            contact["github"] = githubs[0].replace("Github:", "").replace("GitHub:", "").strip()
        else:
            contact["github"] = ""
            
        skypes = re.findall(skype_pattern, text, re.IGNORECASE)
        if skypes:
            contact["skype"] = skypes[0].replace("Skype:", "").replace("Skype ID:", "").strip()
        else:
            contact["skype"] = ""
        
        return contact
    
    def _extract_education(self, text):
        """Extract education information"""
        education_section = ""
        education_keywords = ["degree", "bachelor", "master", "phd", "diploma", "btech", "mtech", "b.tech", "m.tech"]
        school_keywords = ["university", "college", "institute", "school", "polytechnic"]
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in education_keywords) or any(keyword in line_lower for keyword in school_keywords):
                # Get the next few lines
                education_section += line + "\n"
                for j in range(1, 5):  # Look at next 5 lines
                    if i + j < len(lines) and lines[i + j].strip():
                        education_section += lines[i + j] + "\n"
        
        return education_section.strip()
    
    def _extract_experience(self, text):
        """Extract work experience"""
        experience_section = ""
        experience_keywords = ["experience", "work history", "employment", "intern"]
        
        lines = text.split('\n')
        in_experience = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            if any(keyword in line_lower for keyword in experience_keywords):
                in_experience = True
                experience_section += line + "\n"
            elif in_experience and i + 1 < len(lines) and any(s.lower() in lines[i + 1].lower() for s in ["education", "skills", "projects"]):
                in_experience = False
            elif in_experience:
                experience_section += line + "\n"
        
        return experience_section.strip()
    
    def _categorize_skills(self, text):
        """Extract and categorize skills"""
        # Define skill categories
        languages = ["python", "java", "javascript", "html", "css", "c++", "c#", "go", "ruby", "php", "swift"]
        tools = ["git", "github", "jira", "docker", "kubernetes", "jenkins", "aws", "azure", "gcp", "figma", "photoshop"]
        frameworks = ["react", "angular", "vue", "django", "flask", "spring", "express", "node.js", "tensorflow", "pytorch"]
        databases = ["sql", "mysql", "postgresql", "mongodb", "oracle", "sqlite", "redis", "cassandra", "dynamodb"]
        soft_skills = ["communication", "teamwork", "leadership", "time management", "problem-solving", "critical thinking",
                      "adaptability", "patience", "self-awareness"]
        
        # Find all skills in text
        skills = {
            "languages": [],
            "tools": [],
            "frameworks": [],
            "databases": [],
            "soft_skills": []
        }
        
        text_lower = text.lower()
        
        # Extract languages
        for skill in languages:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                skills["languages"].append(skill)
                
        # Extract tools
        for skill in tools:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                skills["tools"].append(skill)
                
        # Extract frameworks
        for skill in frameworks:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                skills["frameworks"].append(skill)
                
        # Extract databases
        for skill in databases:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                skills["databases"].append(skill)
                
        # Extract soft skills
        for skill in soft_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                skills["soft_skills"].append(skill)
                
        return skills
    
    def _extract_certificates(self, text):
        """Extract certificates"""
        certificates_section = ""
        certificate_keywords = ["certificate", "certification", "credential", "course"]
        
        lines = text.split('\n')
        in_certificates = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            if any(keyword in line_lower for keyword in certificate_keywords):
                in_certificates = True
                certificates_section += line + "\n"
            elif in_certificates and i + 1 < len(lines) and any(s.lower() in lines[i + 1].lower() for s in ["education", "skills", "projects", "experience"]):
                in_certificates = False
            elif in_certificates:
                certificates_section += line + "\n"
        
        return certificates_section.strip()
    
    def _extract_projects(self, text):
        """Extract projects"""
        projects_section = ""
        project_keywords = ["project", "portfolio", "application", "developed", "created"]
        
        lines = text.split('\n')
        in_projects = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            if any(keyword in line_lower for keyword in project_keywords):
                in_projects = True
                projects_section += line + "\n"
            elif in_projects and i + 1 < len(lines) and any(s.lower() in lines[i + 1].lower() for s in ["education", "skills", "certificates", "experience"]):
                in_projects = False
            elif in_projects:
                projects_section += line + "\n"
        
        return projects_section.strip()
    
    def _extract_interests(self, text):
        """Extract interests/hobbies"""
        interests_pattern = r"(?:interests|hobbies):\s*(.*?)(?:\n\n|\n[A-Z]|\Z)"
        match = re.search(interests_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(1).strip()
        return ""