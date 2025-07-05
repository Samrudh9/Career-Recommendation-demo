import re
import pandas as pd
from .quality_checker import check_resume_quality
from .ml_resume_parser import MLResumeParser

# Update how the CSV files are loaded
CAREER_DATA_PATH = r's:\Career-Recommendation-demo\dataset\career_data_with_qualifications.csv'
SKILLS_MAP_PATH = r's:\Career-Recommendation-demo\dataset\skills_career_map.csv'

# Load data files once - ensure Skill column is read as string
career_df = pd.read_csv(CAREER_DATA_PATH)
skills_map_df = pd.read_csv(SKILLS_MAP_PATH, dtype={'Skill': str})  # Force 'Skill' to be string

def extract_name(text):
    """Extract the name from the resume."""
    lines = text.split('\n')
    if lines and lines[0].strip():
        return lines[0].strip()
    return "Not detected"

def extract_name_and_contact(text):
    """Extract name and contact info."""
    name = extract_name(text)
    
    # Extract email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    email = email_match.group(0) if email_match else ""
    
    # Extract phone
    phone_match = re.search(r'\b(?:\+\d{1,3}[-\s])?\d{10,15}\b', text)
    phone = phone_match.group(0) if phone_match else ""
    
    contact = {"email": email, "phone": phone}
    return name, contact

def extract_section(text, section):
    # Extracts lines under a section heading until next heading or empty line
    pattern = rf"{section}[:\s]*\n(.*?)(?:\n[A-Z][^\n]*:|\n\n|$)"
    match = re.search(pattern, text, re.I | re.S)
    if match:
        return match.group(1).strip()
    return ""

def extract_skills(text):
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

def extract_qualification(text):
    # Simple extraction based on known qualifications
    qualifications = set()
    for quals in career_df['Qualification_required']:
        for q in str(quals).split(','):
            if re.search(r'\b' + re.escape(q.strip()) + r'\b', text, re.IGNORECASE):
                qualifications.add(q.strip())
    return list(qualifications)

def extract_interests(text):
    # Extract interests section or keywords
    interests_section = extract_section(text, "Interests")
    if interests_section:
        return interests_section
    
    # Look for hobby keywords
    hobby_keywords = ["hobby", "hobbies", "interests", "enjoy", "passion"]
    lines = text.split('\n')
    for line in lines:
        if any(keyword in line.lower() for keyword in hobby_keywords):
            return line.strip()
    
    return "Not detected"

def get_career_required_skills(career):
    """Get required skills for a specific career using the skills_career_map.csv file"""
    if not career:
        return []
    
    # Find the row for the specified career
    career_row = skills_map_df[skills_map_df['Career'].str.lower() == career.lower()]
    
    if career_row.empty:
        # If exact match not found, try to find partial matches
        for idx, row in skills_map_df.iterrows():
            if career.lower() in str(row['Career']).lower():
                career_row = skills_map_df.iloc[[idx]]
                break
    
    if career_row.empty:
        return []
    
    # Extract skills from the Skills column, ensuring we have a string
    skills_str = str(career_row['Skill'].iloc[0])
    # Split by comma and strip whitespace
    skills = [skill.strip() for skill in skills_str.split(',')]
    return skills

def predict_career_from_skills(skills):
    """Predict the most likely career based on skills in the resume"""
    if not skills:
        return None
    
    # Convert skills to lowercase for case-insensitive matching
    skills_lower = [s.lower() for s in skills]
    
    # Calculate match score for each career
    career_scores = {}
    
    for idx, row in skills_map_df.iterrows():
        career = row['Career']
        
        # Safely handle skill value by converting to string
        skill_value = str(row['Skill']) if not pd.isna(row['Skill']) else ""
        
        # Now we can safely split
        career_skills = [s.strip().lower() for s in skill_value.split(',')]
        
        # Count how many skills match
        matching_skills = sum(1 for skill in skills_lower if any(career_skill in skill or skill in career_skill for career_skill in career_skills))
        
        # Calculate score as percentage of career skills matched
        if matching_skills > 0 and career_skills:
            career_scores[career] = (matching_skills / len(career_skills)) * 100
    
    # Return the career with highest match score, if any
    if career_scores:
        top_career = max(career_scores.items(), key=lambda x: x[1])
        return top_career[0] if top_career[1] > 20 else None  # Return only if >20% match
    
    return None

def generate_improvement_feedback(text, skills, experience, education, projects):
    feedback = []
    text_lower = text.lower()
    
    # Check for summary/objective
    if not any(x in text_lower for x in ["objective", "summary", "profile"]):
        feedback.append("Add a professional summary at the beginning to highlight career goals")
    
    # Check for quantified achievements
    if not any(x in text_lower for x in ["increased", "improved", "reduced", "saved", "achieved", "%", "percent"]):
        feedback.append("Quantify achievements in your internship and project (e.g., \"Increased efficiency by 30%\")")
    
    # Check for internship details
    if "intern" in text_lower and not any(x in text_lower for x in ["developed", "created", "built", "implemented"]):
        feedback.append("Elaborate on your internship - what technologies did you use? What did you accomplish?")
    
    # Check for GitHub link
    if "github" not in text_lower:
        feedback.append("Add GitHub profile link to showcase your code")
    
    # Check for project metrics
    if "project" in text_lower and not any(x in text_lower for x in ["user", "performance", "improved", "efficiency"]):
        feedback.append("Include project metrics - user numbers, performance improvements, etc.")
    
    # Check for coursework
    if not any(x in text_lower for x in ["coursework", "relevant courses", "key courses"]):
        feedback.append("Add relevant coursework from your education")
    
    # Check for skill organization
    skill_categories = ["languages", "frameworks", "tools", "databases"]
    if not any(category in text_lower for category in skill_categories):
        feedback.append("Organize technical skills into clearer categories")
    
    # Check for hackathons/competitions
    if not any(x in text_lower for x in ["hackathon", "competition", "contest", "challenge"]):
        feedback.append("Add any hackathons or competitions you've participated in")
    
    # Check for extracurricular
    if not any(x in text_lower for x in ["extracurricular", "volunteer", "club", "organization"]):
        feedback.append("Add section on extracurricular activities if applicable")
    
    # Check for skill gaps
    modern_skills = ["typescript", "react", "docker", "kubernetes", "aws", "azure", "testing", "ci/cd"]
    missing_modern = [skill for skill in modern_skills if skill not in text_lower]
    if missing_modern:
        feedback.append(f"Consider learning these in-demand skills: {', '.join(missing_modern[:3])}")
    
    return feedback

def analyze_resume(text, target_career=None):
    # Initialize ML parser
    parser = MLResumeParser()
    parsed_data = parser.parse_resume(text)
    
    # Extract data using ML
    name = parsed_data.get("name", "") or extract_name(text)
    contact = parsed_data.get("contact", {})
    education = parsed_data.get("education", "")
    experience = parsed_data.get("experience", "")
    
    # Process skills
    skill_data = parsed_data.get("skills", {})
    all_skills = []
    for category, skills in skill_data.items():
        all_skills.extend(skills)
    
    if not all_skills:
        all_skills = extract_skills(text)
    
    # Auto-detect career if not provided
    if not target_career:
        target_career = predict_career_from_skills(all_skills)
        
    technical_skills = ", ".join(all_skills)
    certificates = parsed_data.get("certificates", "")
    projects = parsed_data.get("projects", "")
    references = extract_section(text, "References")
    qualifications = extract_qualification(text)
    interests = parsed_data.get("interests", "") or extract_interests(text)
    
    # Required skills for the target career
    required_skills = get_career_required_skills(target_career)
    skill_gaps = [s for s in required_skills if s.lower() not in [sk.lower() for sk in all_skills]]
    
    # Extra: Check for modern tech gaps
    cloud_skills = ["aws", "azure", "gcp", "docker", "kubernetes"]
    testing_skills = ["jest", "mocha", "pytest", "unittest", "testing"]
    uiux_skills = ["figma", "adobe xd", "sketch", "ui/ux"]
    
    missing_cloud = [s for s in cloud_skills if s.lower() not in [sk.lower() for sk in all_skills]]
    missing_testing = [s for s in testing_skills if s.lower() not in [sk.lower() for sk in all_skills]]
    missing_uiux = [s for s in uiux_skills if s.lower() not in [sk.lower() for sk in all_skills]]
    
    # Section presence checks
    text_lower = text.lower()
    has_skills_section = any(re.search(r'\bskills?\b', line) for line in text.split('\n'))
    has_projects_section = any(re.search(r'\bprojects?\b', line) for line in text.split('\n'))
    missing_sections = []
    
    # Generate missing sections list
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
    
    # Generate personalized feedback
    feedback = generate_improvement_feedback(text, all_skills, experience, education, projects)
    
    # Quality score
    quality_report = check_resume_quality(text)
    
    return {
        "name": name,
        "contact": contact,
        "education": education,
        "certificates": certificates,
        "experience": experience,
        "technical_skills": technical_skills,
        "projects": projects,
        "references": references,
        "missing_sections": missing_sections,
        "skill_gaps": skill_gaps + missing_cloud + missing_testing + missing_uiux,
        "improvements": feedback,
        "quality_score": quality_report["score"],
        "qualifications": qualifications,
        "skills": all_skills,
        "skill_data": skill_data,
        "interests": interests,
        "career": target_career,
    }