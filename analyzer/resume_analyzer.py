import os
import pandas as pd
from .ml_resume_parser_enhanced import MLResumeParser
from .ml_resume_classifier import ResumeCareerClassifier
from .resume_parser import parse_resume_structured  # Used in function-based approach

# Paths
SKILL_CAREER_MAP_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "skills_career_map.csv")


class ResumeSkillGapAnalyzer:
    """Analyzes resume skill gaps based on predicted career path."""

    def __init__(self, skills_career_map_path: str):
        self.skills_career_map_path = skills_career_map_path
        self.skills_df = self._load_skills_career_map()

    def _load_skills_career_map(self):
        if not os.path.exists(self.skills_career_map_path):
            raise FileNotFoundError(f"Skill map not found: {self.skills_career_map_path}")
        df = pd.read_csv(self.skills_career_map_path)
        if 'Skill' not in df.columns or 'Career' not in df.columns:
            raise ValueError("CSV must contain 'Skill' and 'Career' columns")
        df['Skill'] = df['Skill'].str.strip().str.lower()
        df['Career'] = df['Career'].str.strip().str.lower()
        return df

    def _normalize_skills(self, skills):
        normalized = []
        if isinstance(skills, list):
            normalized = [str(skill).strip().lower() for skill in skills]
        elif isinstance(skills, dict):
            for _, skill_list in skills.items():
                if isinstance(skill_list, list):
                    normalized.extend([str(s).strip().lower() for s in skill_list])
        elif isinstance(skills, str):
            normalized = [s.strip().lower() for s in skills.split(",")]
        return list(dict.fromkeys(normalized))  # remove duplicates

    def _get_expected_skills(self, career: str):
        return self.skills_df[self.skills_df["Career"] == career.lower()]["Skill"].tolist()

    def _generate_improvements(self, parsed):
        improvements = []
        if not parsed.get("qualification"): improvements.append("Mention your degrees and institutions clearly.")
        if not parsed.get("work_experience"): improvements.append("Add job roles, organizations, and time frames.")
        skills = parsed.get("skills", [])
        if isinstance(skills, dict):  # handle category-based
            skill_count = sum(len(v) for v in skills.values() if isinstance(v, list))
        else:
            skill_count = len(skills)
        if skill_count < 5: improvements.append("Add more relevant technical or soft skills.")
        if not parsed.get("projects"): improvements.append("Include projects that showcase your practical skills.")
        contact = parsed.get("contact", {})
        if not contact.get("email"): improvements.append("Include a professional email address.")
        if not contact.get("phone"): improvements.append("Add your phone number for contact.")
        return improvements

    def analyze_skill_gaps(self, resume_text: str, parser_func, classifier_class) -> dict:
        parsed = parser_func(resume_text)
        resume_skills = self._normalize_skills(parsed.get("skills", []))

        classifier = classifier_class()
        prediction = classifier.predict(resume_text)

        if isinstance(prediction, dict):
            predicted_career = prediction.get("predicted_career", "").lower()
        else:
            predicted_career = prediction.lower()

        expected_skills = list(dict.fromkeys(self._get_expected_skills(predicted_career)))
        matched = sorted(set(resume_skills) & set(expected_skills))
        gaps = sorted(set(expected_skills) - set(resume_skills))
        coverage = round((len(matched) / len(expected_skills)) * 100, 2) if expected_skills else 0

        improvements = self._generate_improvements(parsed)

        return {
            "predicted_career": predicted_career,
            "matched_skills": matched,
            "skill_gaps": gaps,
            "skill_coverage_percent": coverage,
            "suggestions": improvements,
            "total_resume_skills": len(resume_skills),
            "total_expected_skills": len(expected_skills),
        }


# ✅ Quick wrapper for Flask/backend
def analyze_resume_for_app(resume_text: str):
    try:
        analyzer = ResumeSkillGapAnalyzer(SKILL_CAREER_MAP_PATH)
        result = analyzer.analyze_skill_gaps(
            resume_text,
            parser_func=parse_resume_structured,
            classifier_class=ResumeCareerClassifier
        )

        # You can also extend this to include parsed resume details
        parsed = parse_resume_structured(resume_text)

        return {
            "name": parsed.get("name", "Not detected"),
            "contact": parsed.get("contact", {}),
            "education": parsed.get("qualification", []),
            "experience": parsed.get("work_experience", []),
            "projects": parsed.get("projects", []),
            "skills": parsed.get("skills", []),
            "career_analysis": result
        }
    except Exception as e:
        return {"error": str(e)}
