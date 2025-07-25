import re
from difflib import get_close_matches

class MLResumeParser:
    def __init__(self):
        self.known_skills = [
            "python", "java", "c++", "c", "sql", "javascript", "react", "angular", "nodejs",
            "excel", "communication", "leadership", "teamwork", "project management", "data analysis",
            "html", "css", "machine learning", "deep learning", "pytorch", "tensorflow", "flask", "django",
            "mongodb", "git", "github", "mysql", "rest api"
        ]

    def parse_resume(self, text):
        name = "Not provided"  # Name extraction disabled
        contact = self._extract_contact_info(text)
        education = self._extract_education(text)
        experience = self._extract_experience(text)
        summary = self._extract_summary(text)
        skills = self._extract_skills(text)
        projects = self._extract_projects(text) if hasattr(self, "_extract_projects") else "Not detected"

        return {
            "name": name,
            "contact": contact,
            "education": education,
            "experience": experience,
            "summary": summary,
            "skills": skills,
            "projects": projects
        }

    def _extract_contact_info(self, text):
        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4})', text)
        email_match = re.search(r'\b[\w.-]+?@[\w.-]+?\.[a-zA-Z]{2,6}\b', text)
        return {
            "phone": phone_match.group() if phone_match else "Not detected",
            "email": email_match.group() if email_match else "Not detected"
        }

    def _extract_education(self, text):
        edu_keywords = ['b.tech', 'bachelor', 'm.tech', 'mba', 'university', 'institute', 'college', 'school']
        matches = [line for line in text.lower().split('\n') if any(kw in line for kw in edu_keywords)]
        return ' '.join(matches[:3]) if matches else "Not detected"

    def _extract_experience(self, text):
        exp_keywords = ['intern', 'developer', 'engineer', 'manager', 'analyst']
        exp_lines = []
        for line in text.lower().split('\n'):
            if any(kw in line for kw in exp_keywords) and re.search(r'(19|20)\d{2}', line):
                exp_lines.append(line)
        return ' '.join(exp_lines[:3]) if exp_lines else "Not detected"

    def _extract_summary(self, text):
        lines = text.strip().split('\n')
        return ' '.join(lines[1:6]).strip() if len(lines) > 1 else "Not detected"

    def _extract_skills(self, text):
        lower_text = text.lower()
        found = set()
        for skill in self.known_skills:
            if skill in lower_text:
                found.add(skill)
            else:
                match = get_close_matches(skill.lower(), lower_text.split(), n=1, cutoff=0.85)
                if match:
                    found.add(skill)
        return list(found) or ["Not detected"]
    
    def _extract_projects(self, text):
        """Extract projects from resume text"""
        proj_keywords = ['project', 'developed', 'created', 'built', 'implemented', 'designed']
        proj_lines = []
        
        # Look for project section
        sections = text.lower().split('\n\n')
        for section in sections:
            if any(section.strip().startswith(kw) for kw in ['project', 'projects', 'personal project']):
                return section.strip()
        
        # Fallback: look for lines with project keywords
        for line in text.lower().split('\n'):
            if any(kw in line for kw in proj_keywords):
                proj_lines.append(line)
                
        return ' '.join(proj_lines[:5]) if proj_lines else "Not detected"
