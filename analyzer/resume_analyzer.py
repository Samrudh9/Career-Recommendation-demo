import re
import pandas as pd
from .quality_checker import check_resume_quality

# Load career data once
CAREER_DATA_PATH = r's:\Career-Recommendation-demo\dataset\career_data_with_qualifications.csv'
career_df = pd.read_csv(CAREER_DATA_PATH)

CAREER_SKILL_MAP_PATH = r's:\Career-Recommendation-demo\dataset\skills_career_map.csv'
career_skill_df = pd.read_csv(CAREER_SKILL_MAP_PATH)

def extract_name(text):
    # Simple heuristic: first line with two or more words, title case
    for line in text.split('\n'):
        if len(line.split()) >= 2 and line == line.title():
            return line.strip()
    return ""

def extract_interests(text):
    # Look for a section labeled 'Interests' or 'Technical Skills and Interests'
    match = re.search(r'(Interests|Technical Skills and Interests)[:\n](.*)', text, re.IGNORECASE)
    if match:
        return match.group(2).strip()
    return ""

def extract_skills(text):
    # Use a comprehensive skill list from the dataset
    all_skills = set()
    for skills in career_df['Skills']:
        all_skills.update([s.strip().lower() for s in skills.split(',')])
    found = set()
    for skill in all_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            found.add(skill)
    return list(found)

def extract_qualification(text):
    # Simple extraction based on known qualifications
    qualifications = set()
    for quals in career_df['Qualification_required']:
        for q in str(quals).split(','):
            if re.search(r'\b' + re.escape(q.strip()) + r'\b', text, re.IGNORECASE):
                qualifications.add(q.strip())
    return list(qualifications)

def get_career_required_skills(career):
    if not career:
        return []
    row = career_skill_df[career_skill_df['Career'].str.lower() == career.lower()]
    if not row.empty:
        skills = row.iloc[0]['Skill']
        if isinstance(skills, str):
            return [s.strip().lower() for s in skills.split(',')]
    return []

def analyze_resume(text, target_career=None):
    name = extract_name(text)
    interests = extract_interests(text)
    skills = extract_skills(text)
    qualifications = extract_qualification(text)

    # Predict or select career
    if not target_career:
        best_match = None
        max_overlap = 0
        for _, row in career_skill_df.iterrows():
            skill_cell = row['Skill']
            if not isinstance(skill_cell, str):
                continue
            required = [s.strip().lower() for s in skill_cell.split(',')]
            overlap = len(set(skills) & set(required))
            if overlap > max_overlap:
                max_overlap = overlap
                best_match = row
        target_career = best_match['Career'] if best_match is not None else None

    if not target_career:
        # fallback or warning
        required_skills = []
    else:
        required_skills = get_career_required_skills(target_career)

    # Required skills for the target career
    required_skills = get_career_required_skills(target_career)  # from your CSV
    resume_skills = extract_skills(text)  # from the resume

    skill_gaps = [s for s in required_skills if s not in resume_skills]
    skill_matches = list(set(skills) & set(required_skills))

    # Extra: Check for modern tech gaps
    cloud_skills = {"aws", "azure", "gcp", "docker", "kubernetes"}
    testing_skills = {"jest", "mocha", "pytest", "unittest"}
    uiux_skills = {"figma", "adobe xd", "sketch"}
    missing_cloud = [s for s in cloud_skills if s not in skills]
    missing_testing = [s for s in testing_skills if s not in skills]
    missing_uiux = [s for s in uiux_skills if s not in skills]

    # Section presence checks
    text_lower = text.lower()
    has_skills_section = any(re.search(r'\bskills?\b', line) for line in text.split('\n'))
    has_projects_section = any(re.search(r'\bprojects?\b', line) for line in text.split('\n'))
    missing_sections = []
    if not has_skills_section:
        missing_sections.append("Skills")
    if not has_projects_section:
        missing_sections.append("Projects")
    if not any(x in text_lower for x in ["certification", "certificate"]):
        missing_sections.append("Certifications")
    if not any(x in text_lower for x in ["objective", "summary"]):
        missing_sections.append("Objective/Summary")
    if "extracurricular" not in text_lower and "activity" not in text_lower:
        missing_sections.append("Extracurricular Activities")
    if missing_cloud:
        missing_sections.append("Cloud/DevOps")
    if missing_testing:
        missing_sections.append("Testing")
    if missing_uiux:
        missing_sections.append("UI/UX Tools")

    # Human-like feedback
    feedback = []
    if not any(x in text_lower for x in ["objective", "summary"]):
        feedback.append("Add a brief Objective or Summary at the top to quickly communicate your career goals.")
    if "javascript" not in skills:
        feedback.append("List JavaScript explicitly in your technical skills if you have experience.")
    if "typescript" not in skills:
        feedback.append("Add TypeScript if you have experience or plan to work with modern JS frameworks.")
    if missing_cloud:
        feedback.append("Consider learning or mentioning Cloud/DevOps tools (e.g., AWS, Docker, Kubernetes).")
    if missing_testing:
        feedback.append("Mention any experience with testing frameworks (e.g., Jest, Mocha, Pytest).")
    if missing_uiux:
        feedback.append("Add UI/UX tools (e.g., Figma, Adobe XD) if you have experience.")
    if not any(x in text_lower for x in ["extracurricular", "activity"]):
        feedback.append("Include extracurricular activities or volunteer work if relevant.")
    feedback.append("Quantify your achievements (e.g., 'Developed a web app used by 500+ users').")
    feedback.append("Use consistent formatting and section headings for a professional look.")

    # Quality score
    quality_report = check_resume_quality(text)

    print("missing_sections type:", type(missing_sections), missing_sections)
    print("skill_gaps type:", type(skill_gaps), skill_gaps)

    return {
        "name": name,
        "interests": interests or "Not detected",
        "missing_sections": missing_sections,  # must be a list, not a string!
        "skill_gaps": skill_gaps + missing_cloud + missing_testing + missing_uiux,  # must be a list!
        "feedback": feedback,
        "quality_score": quality_report["score"],
        "qualifications": qualifications,
        "skills": skills,
        "career": target_career,
    }