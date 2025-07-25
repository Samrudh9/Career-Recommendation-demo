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
    # Use structured parsing for better extraction
    from .resume_parser import parse_resume_structured
    
    parsed = parse_resume_structured(text)

    # Predict the career field
    predicted_career = classifier.predict(text)

    # Extract skills from structured data
    skills_data = parsed.get("skills", {})
    detected_skills = []
    for category, skills in skills_data.items():
        detected_skills.extend(skills)
    
    detected_skills_set = set(detected_skills)
    expected_skills = set(skills_map_list)
    skill_gaps = list(expected_skills - detected_skills_set)[:5]

    # Enhanced improvement tips based on structured data
    improvements = []
    
    # Check qualification
    qualification = parsed.get("qualification", [])
    if not qualification:
        improvements.append("Mention your degrees and institutions clearly.")
    
    # Check work experience
    work_experience = parsed.get("work_experience", [])
    if not work_experience:
        improvements.append("Add job roles, organizations, and time frames.")
    
    # Check skills
    if len(detected_skills) < 5:
        improvements.append("Add more relevant technical or soft skills.")
    
    # Check projects
    projects = parsed.get("projects", [])
    if not projects:
        improvements.append("Include projects that showcase your practical skills.")
    
    # Check contact information
    contact = parsed.get("contact", {})
    if not contact.get("email"):
        improvements.append("Include a professional email address.")
    
    if not contact.get("phone"):
        improvements.append("Add your phone number for contact.")

    # Enhanced quality scoring
    quality_score = 0
    if qualification: quality_score += 25
    if work_experience: quality_score += 25
    if len(detected_skills) >= 5: quality_score += 20
    if projects: quality_score += 20
    if contact.get("email"): quality_score += 5
    if contact.get("phone"): quality_score += 5

    # Format qualification for display
    qualification_display = []
    for qual in qualification:
        if qual.get("degree") and qual.get("major"):
            display = f"{qual['degree']} in {qual['major']}"
            if qual.get("institution") and qual["institution"] != "Not specified":
                display += f", {qual['institution']}"
            qualification_display.append(display)
    
    # Format work experience for display
    experience_display = []
    for exp in work_experience:
        if exp.get("job_title") and exp.get("company"):
            display = f"{exp['job_title']} at {exp['company']}"
            if exp.get("duration") and exp["duration"] != "Duration not specified":
                display += f" ({exp['duration']})"
            experience_display.append(display)

    # Format projects for display
    projects_display = []
    for proj in projects:
        if proj.get("title"):
            display = proj["title"]
            if proj.get("description"):
                display += f": {proj['description'][:100]}..."
            if proj.get("technologies"):
                display += f" [Technologies: {', '.join(proj['technologies'][:3])}]"
            projects_display.append(display)

    return {
        "name": parsed.get("name", "Not detected"),
        "contact": parsed.get("contact", {}),
        "education": "; ".join(qualification_display) if qualification_display else "Not detected",
        "experience": "; ".join(experience_display) if experience_display else "Not detected",
        "skills": detected_skills,
        "summary": "Professional with experience in " + predicted_career if predicted_career else "Not detected",
        "career": predicted_career,
        "skill_gaps": skill_gaps,
        "improvements": improvements,
        "quality_score": quality_score,
        "certificates": "Not yet implemented",
        "projects": "; ".join(projects_display) if projects_display else "Not detected",
        # Add structured data for advanced processing
        "structured_qualification": qualification,
        "structured_experience": work_experience,
        "structured_projects": projects,
        "structured_skills": skills_data
    }
