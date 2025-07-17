# Build a fully upgraded MLResumeParser that handles unstructured resumes better
import re
import spacy
from difflib import get_close_matches

nlp = spacy.load("en_core_web_sm")

class MLResumeParser:
    def __init__(self):
        self.known_skills = [
            "python", "java", "c++", "c", "sql", "javascript", "react", "angular", "nodejs",
            "excel", "communication", "leadership", "teamwork", "project management", "data analysis",
            "html", "css", "machine learning", "deep learning", "pytorch", "tensorflow", "flask", "django"
        ]
        self.degree_keywords = ["bachelor", "b.tech", "m.tech", "master", "mba", "msc", "b.sc", "phd", "diploma"]
        self.edu_keywords = self.degree_keywords + ["university", "college", "institute", "school"]

    def parse_resume(self, text):
        text = self._clean_text(text)
        name = self._extract_name(text)
        contact = self._extract_contact_info(text)
        education = self._extract_education(text)
        experience = self._extract_experience(text)
        skills = self._extract_skills(text)
        summary = self._extract_summary(text)
        return {
            "name": name,
            "contact": contact,
            "education": education,
            "experience": experience,
            "skills": skills,
            "summary": summary
        }

    def _clean_text(self, text):
        return text.replace("\\r", "\\n").replace("\\t", " ").strip()

    def _extract_name(self, text):
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON" and len(ent.text.split()) <= 3:
                return ent.text.strip()
        lines = text.split("\\n")
        for line in lines[:5]:
            if line.strip() and not any(k in line.lower() for k in ["email", "phone", "@", "linkedin", "github", "resume"]):
                return line.strip()
        return "Not detected"

    def _extract_contact_info(self, text):
        phone_match = re.search(r'(\\+?\\d{1,3}[-.\\s]?)?(\\(?\\d{3,4}\\)?[-.\\s]?\\d{3,4}[-.\\s]?\\d{3,4})', text)
        email_match = re.search(r'\\b[\\w.-]+?@[\\w.-]+?\\.[a-zA-Z]{2,6}\\b', text)
        return {
            "phone": phone_match.group() if phone_match else "Not detected",
            "email": email_match.group() if email_match else "Not detected"
        }

    def _extract_education(self, text):
        lines = text.lower().split("\\n")
        edu_lines = [line.strip() for line in lines if any(kw in line for kw in self.edu_keywords)]
        return " ".join(edu_lines).strip() or "Not detected"

    def _extract_experience(self, text):
        exp_lines = []
        lines = text.split("\\n")
        for line in lines:
            if re.search(r"(\\b20\\d{2}\\b|\\b19\\d{2}\\b)", line) and any(role in line.lower() for role in ["intern", "developer", "manager", "engineer", "associate"]):
                exp_lines.append(line.strip())
        return " ".join(exp_lines).strip() or "Not detected"

    def _extract_skills(self, text):
        lower_text = text.lower()
        found = set()
        for skill in self.known_skills:
            if skill in lower_text:
                found.add(skill)
            else:
                # Try fuzzy matching
                words = lower_text.split()
                match = get_close_matches(skill.lower(), words, n=1, cutoff=0.85)
                if match:
                    found.add(skill)
        return list(found) or ["Not detected"]

    def _extract_summary(self, text):
        lines = text.strip().split("\\n")[:6]
        blob = " ".join(lines)
        if 20 < len(blob) < 500:
            return blob
        return "Not detected"
# Save the enhanced parser to a new file
enhanced_parser_path = os.path.join(analyzer_dir, "ml_resume_parser_enhanced.py")
with open(enhanced_parser_path, "w", encoding="utf-8") as f:
    f.write(enhanced_parser_code)

enhanced_parser_path
