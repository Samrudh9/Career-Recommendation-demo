import os
import re
import pandas as pd
from .ml_resume_parser_enhanced import MLResumeParser
from .ml_resume_classifier import ResumeCareerClassifier

# Initialize the parser and classifier
parser = MLResumeParser()
classifier = ResumeCareerClassifier()

# Load skill list from CSV
SKILL_CAREER_MAP_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "skills_career_map.csv")
if os.path.exists(SKILL_CAREER_MAP_PATH):
    skill_df = pd.read_csv(SKILL_CAREER_MAP_PATH)
    skills_map_list = list(skill_df["Skill"].dropna().unique())
else:
    skills_map_list = []

def analyze_resume(text):
    parsed = parser.parse_resume(text)

    # Predict the career field
    predicted_career = classifier.predict(text)

    # Extract known skills from resume
    detected_skills = set(parsed.get("skills", []))
    expected_skills = set(skills_map_list)
    skill_gaps = list(expected_skills - detected_skills)[:5]

    # Improvement tips
    improvements = []
    if parsed.get("summary") == "Not detected":
        improvements.append("Include a short professional summary.")
    if len(detected_skills) < 5:
        improvements.append("Add more relevant technical or soft skills.")
    if parsed.get("experience") == "Not detected":
        improvements.append("Add job roles, organizations, and time frames.")
    if parsed.get("education") == "Not detected":
        improvements.append("Mention your degrees and institutions clearly.")

    # Quality scoring (basic heuristic)
    quality_score = 0
    if parsed.get("summary") != "Not detected": quality_score += 20
    if len(detected_skills) >= 5: quality_score += 20
    if parsed.get("experience") != "Not detected": quality_score += 20
    if parsed.get("education") != "Not detected": quality_score += 20
    if parsed.get("name") != "Not detected": quality_score += 20

    return {
        "name": parsed.get("name", "Not detected"),
        "contact": parsed.get("contact", {}),
        "education": parsed.get("education", "Not detected"),
        "experience": parsed.get("experience", "Not detected"),
        "skills": list(detected_skills),
        "summary": parsed.get("summary", "Not detected"),
        "career": predicted_career,
        "skill_gaps": skill_gaps,
        "improvements": improvements,
        "quality_score": quality_score,
        "certificates": "Not yet implemented",
        "projects": "Not yet implemented"
    }
