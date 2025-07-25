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
    
    # Format career prediction for better display
    career_data = {}
    if isinstance(predicted_career, dict):
        career_data = {
            'predicted_career': predicted_career.get('predicted_career', ''),
            'confidence': float(predicted_career.get('confidence', 0)) * 100 if hasattr(predicted_career.get('confidence', 0), 'item') else predicted_career.get('confidence', 0) * 100,
        }
        
        # Format top careers if available
        if 'top_careers' in predicted_career:
            formatted_top_careers = []
            for career, conf in predicted_career['top_careers']:
                # Convert numpy values to Python native types
                if hasattr(conf, 'item'):
                    conf = float(conf) * 100  # Convert to percentage
                else:
                    conf = float(conf) * 100
                formatted_top_careers.append((career, conf))
            career_data['top_careers'] = formatted_top_careers
    else:
        career_data = predicted_career  # Keep as string if it's already a string
    
    # Extract career name for summary
    if isinstance(predicted_career, dict):
        career_name = predicted_career.get('predicted_career', '')
    else:
        career_name = predicted_career
    
    # Extract known skills from resume
    detected_skills = set()  # Initialize as a set
    
    # Store the original structured skills data
    skills_data = parsed.get("skills", {})
    
    # Handle different formats of skills data
    if isinstance(skills_data, list):
        # Handle list of skills
        for skill in skills_data:
            detected_skills.add(skill)
    elif isinstance(skills_data, dict):
        # Handle the case where skills is a dictionary with categories
        for category, skills in skills_data.items():
            if isinstance(skills, list):
                detected_skills.update(skills)  # Now update() works because detected_skills is a set
    
    expected_skills = set(skills_map_list)
    skill_gaps = list(expected_skills - detected_skills)[:5]

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
        "skills": list(detected_skills),  # Convert set back to list
        "summary": "Professional with experience in " + career_name if career_name else "Not detected",
        "career": career_data,  # Now using our formatted career data
        "skill_gaps": skill_gaps,
        "improvements": improvements,
        "quality_score": quality_score,
        "certificates": "Not yet implemented",
        "projects": "; ".join(projects_display) if projects_display else "Not detected",
        # Add structured data for advanced processing
        "structured_qualification": qualification,
        "structured_experience": work_experience,
        "structured_projects": projects,
        "structured_skills": skills_data  # Now skills_data is properly defined
    }
