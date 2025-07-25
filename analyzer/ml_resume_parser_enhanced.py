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
        # Use the enhanced structured parsing
        from .resume_parser import parse_resume_structured
        
        structured_data = parse_resume_structured(text)
        
        # Convert to the expected format for backward compatibility
        name = structured_data.get("name", "Not provided")
        contact = structured_data.get("contact", {})
        
        # Format qualification
        qualification = structured_data.get("qualification", [])
        education = "; ".join([f"{q.get('degree', '')} in {q.get('major', '')}" for q in qualification]) if qualification else "Not detected"
        
        # Format experience
        work_experience = structured_data.get("work_experience", [])
        experience = "; ".join([f"{exp.get('job_title', '')} at {exp.get('company', '')}" for exp in work_experience]) if work_experience else "Not detected"
        
        # Extract summary from first few lines
        summary = self._extract_summary(text)
        
        # Flatten skills from structured format
        skills_data = structured_data.get("skills", {})
        all_skills = []
        for category, skills in skills_data.items():
            all_skills.extend(skills)
        
        skills = all_skills if all_skills else ["Not detected"]

        return {
            "name": name,
            "contact": contact,
            "education": education,
            "experience": experience,
            "summary": summary,
            "skills": skills,
            # Add structured data for advanced processing
            "structured_data": structured_data
        }

    def _extract_name(self, text):
        """
        Name extraction removed as requested.
        Returns a placeholder value.
        """
        return "Not provided"

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
