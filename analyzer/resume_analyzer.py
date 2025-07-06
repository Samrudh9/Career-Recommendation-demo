import re
import csv
import os
from .quality_checker import check_resume_quality
from .ml_resume_parser import MLResumeParser
from .ml_resume_classifier import resume_classifier

# Replace absolute Windows paths with relative paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAREER_DATA_PATH = os.path.join(base_dir, 'dataset', 'career_data_with_qualifications.csv')
SKILLS_MAP_PATH = os.path.join(base_dir, 'dataset', 'skills_career_map.csv')

# Load data files once via csv
career_list = []
with open(CAREER_DATA_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        career_list.append(row)
# Skills map
skills_map_list = []
with open(SKILLS_MAP_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        skills_map_list.append(row)

def extract_name(text):
    """Extract the name from the resume."""
    lines = text.split('\n')
    if lines and lines[0].strip():
        return lines[0].strip()
    return "Not detected"

def extract_name_and_contact(text):
    """Extract name and contact info."""
    # Better name extraction - look for name patterns
    lines = text.split('\n')
    name = "Not detected"
    
    # Try to find name in first few lines
    for i, line in enumerate(lines[:5]):
        line = line.strip()
        if line and not any(keyword in line.lower() for keyword in ['email', 'phone', 'address', 'linkedin', 'github', 'objective', 'summary']):
            # Check if it looks like a name (2-4 words, mostly alphabetic)
            words = line.split()
            if 2 <= len(words) <= 4 and all(word.replace('.', '').isalpha() for word in words):
                name = line
                break
    
    # Extract email with better patterns
    email_patterns = [
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        r'Email[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'E-mail[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    ]
    
    email = ""
    for pattern in email_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            email = match.group(1) if match.groups() else match.group(0)
            break
    
    # Extract phone with better patterns
    phone_patterns = [
        r'Phone[:\s]*(\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
        r'Mobile[:\s]*(\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',
        r'(\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
    ]
    
    phone = ""
    for pattern in phone_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            phone = match.group(1) if match.groups() else match.group(0)
            break
    
    # Extract LinkedIn
    linkedin_patterns = [
        r'linkedin\.com/in/[\w-]+',
        r'LinkedIn[:\s]*(linkedin\.com/in/[\w-]+)',
        r'(https?://)?(?:www\.)?linkedin\.com/in/([\w-]+)'
    ]
    
    linkedin = ""
    for pattern in linkedin_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if 'linkedin.com' in match.group(0):
                linkedin = match.group(0) if not match.group(0).startswith('http') else match.group(0)
                if not linkedin.startswith('http'):
                    linkedin = 'https://' + linkedin
            break
    
    # Extract GitHub
    github_patterns = [
        r'github\.com/[\w-]+',
        r'GitHub[:\s]*(github\.com/[\w-]+)',
        r'(https?://)?(?:www\.)?github\.com/([\w-]+)'
    ]
    
    github = ""
    for pattern in github_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if 'github.com' in match.group(0):
                github = match.group(0) if not match.group(0).startswith('http') else match.group(0)
                if not github.startswith('http'):
                    github = 'https://' + github
            break
    
    contact = {
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github
    }
    return name, contact

def extract_section(text, section):
    """Extracts content under a section heading with improved patterns"""
    # Multiple patterns to catch different section formats
    patterns = [
        rf"{section}[:\s]*\n(.*?)(?:\n[A-Z][A-Z\s]+[:\n]|\n\n|$)",  # All caps headings
        rf"{section}[:\s]*\n(.*?)(?:\n[A-Za-z]+[:\n]|\n\n|$)",     # Title case headings
        rf"^{section}[:\s]*\n(.*?)(?:\n\w+[:\n]|\n\n|$)",          # Start of line
        rf"\n{section}[:\s]*\n(.*?)(?:\n\w+[:\n]|\n\n|$)"          # After newline
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.I | re.S | re.M)
        if match and match.group(1).strip():
            return match.group(1).strip()
    
    # Fallback: look for keywords in lines
    lines = text.split('\n')
    section_found = False
    content_lines = []
    
    for line in lines:
        if section.lower() in line.lower() and ':' in line:
            section_found = True
            # If content is on same line after colon
            if ':' in line:
                after_colon = line.split(':', 1)[1].strip()
                if after_colon:
                    content_lines.append(after_colon)
            continue
        
        if section_found:
            # Stop if we hit another section heading
            if re.match(r'^[A-Z][A-Z\s]*:?$', line.strip()) or \
               re.match(r'^[A-Za-z\s]+:$', line.strip()):
                break
            if line.strip():
                content_lines.append(line.strip())
    
    return '\n'.join(content_lines) if content_lines else ""

def extract_education(text):
    """Extract education section with better parsing"""
    education_keywords = ["education", "academic", "qualification", "degree", "university", "college", "school"]
    
    for keyword in education_keywords:
        education = extract_section(text, keyword)
        if education:
            return education
    
    # Look for degree indicators
    degree_patterns = [
        r'(Bachelor|Master|PhD|B\.?Tech|M\.?Tech|B\.?E|M\.?E|B\.?Sc|M\.?Sc|MBA|BCA|MCA).*?(?:\n|$)',
        r'(University|College).*?(?:\n|$)'
    ]
    
    education_lines = []
    for pattern in degree_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        education_lines.extend(matches)
    
    return '\n'.join(education_lines) if education_lines else "Not detected"

def extract_projects(text):
    """Extract projects section with better parsing"""
    project_keywords = ["project", "work", "development", "built", "created", "implemented"]
    
    # First try to find explicit projects section
    for keyword in project_keywords:
        projects = extract_section(text, keyword)
        if projects and len(projects) > 50:  # Ensure meaningful content
            return projects
    
    # Look for project indicators in text
    project_patterns = [
        r'(Project[:\s]+.*?)(?=\n[A-Z]|\n\n|$)',
        r'(Built.*?)(?=\n[A-Z]|\n\n|$)',
        r'(Developed.*?)(?=\n[A-Z]|\n\n|$)',
        r'(Created.*?)(?=\n[A-Z]|\n\n|$)'
    ]
    
    project_lines = []
    for pattern in project_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        project_lines.extend([match.strip() for match in matches])
    
    return '\n'.join(project_lines[:3]) if project_lines else "Not detected"  # Limit to top 3

def extract_certifications(text):
    """Extract certifications with better parsing"""
    cert_keywords = ["certification", "certificate", "certified", "license"]
    
    # Try explicit sections first
    for keyword in cert_keywords:
        certs = extract_section(text, keyword)
        if certs:
            return certs
    
    # Look for certification patterns
    cert_patterns = [
        r'(AWS.*?(?:Certified|Certificate).*?)(?=\n|$)',
        r'(Microsoft.*?(?:Certified|Certificate).*?)(?=\n|$)',
        r'(Google.*?(?:Certified|Certificate).*?)(?=\n|$)',
        r'(Oracle.*?(?:Certified|Certificate).*?)(?=\n|$)',
        r'(Cisco.*?(?:Certified|Certificate).*?)(?=\n|$)',
        r'(PMP|CISSP|CISA|CompTIA).*?(?=\n|$)'
    ]
    
    cert_lines = []
    for pattern in cert_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        cert_lines.extend(matches)
    
    return '\n'.join(cert_lines) if cert_lines else "Not detected"

def extract_skills(text):
    """Extract skills from resume text using comprehensive skill database"""
    # Build set of all possible skills from skills_map_list
    all_possible_skills = set()
    for row in skills_map_list:
        skill_value = str(row.get('Skill',''))
        for s in skill_value.split(','):
            s = s.strip().lower()
            if s:
                all_possible_skills.add(s)
    
    # Additional comprehensive skill list
    additional_skills = [
        # Programming Languages
        "python", "java", "javascript", "typescript", "c++", "c#", "c", "go", "rust", 
        "php", "ruby", "swift", "kotlin", "scala", "r", "matlab", "perl", "vb.net",
        
        # Web Technologies
        "html", "css", "react", "angular", "vue", "node.js", "express", "django", 
        "flask", "laravel", "spring", "asp.net", "jquery", "bootstrap", "tailwind",
        
        # Databases
        "mysql", "postgresql", "mongodb", "sqlite", "redis", "elasticsearch", 
        "oracle", "sql server", "cassandra", "dynamodb", "neo4j",
        
        # Cloud & DevOps
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "git", "github",
        "gitlab", "ci/cd", "terraform", "ansible", "vagrant", "chef", "puppet",
        
        # Data Science & ML
        "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras", 
        "tableau", "power bi", "jupyter", "spark", "hadoop", "airflow",
        
        # Mobile Development
        "android", "ios", "flutter", "react native", "xamarin", "ionic",
        
        # Tools & Technologies
        "linux", "windows", "macos", "bash", "powershell", "vim", "vscode", 
        "intellij", "eclipse", "xcode", "photoshop", "illustrator", "figma",
        
        # Frameworks & Libraries
        "spring boot", "hibernate", "redux", "graphql", "rest api", "soap",
        "microservices", "oauth", "jwt", "websockets"
    ]
    
    all_possible_skills.update(additional_skills)
    
    # Find skills in text (case-insensitive match)
    text_lower = text.lower()
    found_skills = [skill for skill in all_possible_skills if skill and skill in text_lower]
    return found_skills

def extract_skills_comprehensive(text):
    """Extract skills using comprehensive pattern matching based on skills_career_map.csv"""
    text_lower = text.lower()
    found_skills = []
    
    # Get all skills from the career map dataset
    all_skills_from_dataset = set()
    for idx, row in skills_map_df.iterrows():
        skill_value = str(row['Skill']) if not pd.isna(row['Skill']) else ""
        skills_list = [s.strip() for s in skill_value.split(',')]
        all_skills_from_dataset.update(skills_list)
    
    # Check for each skill in the text
    for skill in all_skills_from_dataset:
        if not skill.strip():
            continue
            
        skill_clean = skill.strip()
        skill_lower = skill_clean.lower()
        
        # Handle special cases and variations
        skill_variations = [skill_lower]
        
        # Add common variations
        if skill_lower == 'javascript':
            skill_variations.extend(['js', 'javascript'])
        elif skill_lower == 'typescript':
            skill_variations.extend(['ts', 'typescript'])
        elif skill_lower == 'react':
            skill_variations.extend(['react.js', 'reactjs'])
        elif skill_lower == 'node.js':
            skill_variations.extend(['nodejs', 'node'])
        elif skill_lower == 'express.js':
            skill_variations.extend(['express', 'expressjs'])
        elif skill_lower == 'next.js':
            skill_variations.extend(['nextjs', 'next'])
        elif skill_lower == 'python':
            skill_variations.extend(['python3', 'py'])
        elif skill_lower == 'c++':
            skill_variations.extend(['cpp', 'c plus plus'])
        elif skill_lower == 'c#':
            skill_variations.extend(['csharp', 'c sharp'])
        
        # Check if any variation is found in the text
        for variation in skill_variations:
            # Use word boundaries for better matching
            pattern = r'\b' + re.escape(variation) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.append(skill_clean)
                break
    
    # Additional manual skill detection for common skills not in dataset
    additional_skills = {
        'html': 'HTML',
        'css': 'CSS', 
        'git': 'Git',
        'github': 'GitHub',
        'linux': 'Linux',
        'windows': 'Windows',
        'mysql': 'MySQL',
        'postgresql': 'PostgreSQL',
        'mongodb': 'MongoDB',
        'redis': 'Redis',
        'docker': 'Docker',
        'kubernetes': 'Kubernetes',
        'aws': 'AWS',
        'azure': 'Azure',
        'gcp': 'Google Cloud Platform'
    }
    
    for skill_key, skill_name in additional_skills.items():
        if re.search(r'\b' + re.escape(skill_key) + r'\b', text_lower):
            if skill_name not in found_skills:
                found_skills.append(skill_name)
    
    return list(set(found_skills))

def categorize_skills_better(skills):
    """Categorize skills into different categories"""
    categories = {
        "languages": [],
        "frameworks": [],
        "databases": [],
        "tools": [],
        "soft_skills": []
    }
    
    language_keywords = ["python", "java", "javascript", "typescript", "c++", "c#", "php", "ruby"]
    framework_keywords = ["react", "angular", "vue", "django", "flask", "spring", "express"]
    database_keywords = ["mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle"]
    tool_keywords = ["git", "docker", "kubernetes", "aws", "azure", "jenkins", "linux"]
    
    for skill in skills:
        skill_lower = skill.lower()
        if any(lang in skill_lower for lang in language_keywords):
            categories["languages"].append(skill)
        elif any(fw in skill_lower for fw in framework_keywords):
            categories["frameworks"].append(skill)
        elif any(db in skill_lower for db in database_keywords):
            categories["databases"].append(skill)
        elif any(tool in skill_lower for tool in tool_keywords):
            categories["tools"].append(skill)
        else:
            categories["tools"].append(skill)  # Default to tools
    
    return categories

def extract_qualification(text):
    # Simple extraction based on known qualifications
    qualifications = set()
    for row in career_list:
        for q in str(row.get('Qualification_required','')).split(','):
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
    if not career or not isinstance(career, str):
        return []
    
    # Find the row for the specified career
    career_row = [row for row in skills_map_list if str(row.get('Career','')).lower()==career.lower()]
    
    if not career_row:
        # If exact match not found, try partial
        for row in skills_map_list:
            if career.lower() in str(row.get('Career','')).lower():
                career_row = [row]
                break
    
    if not career_row:
        return []
    
    skills_str = str(career_row[0].get('Skill',''))
    skills = [skill.strip() for skill in skills_str.split(',')]
    return skills

def calculate_skill_gaps(user_skills, target_career):
    """Calculate skill gaps based on career requirements from skills_career_map.csv"""
    required_skills = get_career_required_skills(target_career)
    
    if not required_skills:
        return []
    
    # Normalize user skills for comparison (remove case sensitivity and extra spaces)
    user_skills_normalized = []
    for skill in user_skills:
        if isinstance(skill, str):
            # Clean and normalize skill names
            normalized = skill.lower().strip()
            # Handle common variations
            if normalized in ['js', 'javascript']:
                user_skills_normalized.append('javascript')
            elif normalized in ['ts', 'typescript']:
                user_skills_normalized.append('typescript')
            elif normalized in ['react.js', 'reactjs']:
                user_skills_normalized.append('react')
            elif normalized in ['node.js', 'nodejs']:
                user_skills_normalized.append('nodejs')
            else:
                user_skills_normalized.append(normalized)
    
    # Find missing skills with better matching
    skill_gaps = []
    for required_skill in required_skills:
        if not isinstance(required_skill, str):
            continue
            
        required_skill_normalized = required_skill.lower().strip()
        
        # Handle common variations for required skills too
        if required_skill_normalized in ['js', 'javascript']:
            required_skill_normalized = 'javascript'
        elif required_skill_normalized in ['ts', 'typescript']:
            required_skill_normalized = 'typescript'
        elif required_skill_normalized in ['react.js', 'reactjs']:
            required_skill_normalized = 'react'
        elif required_skill_normalized in ['node.js', 'nodejs']:
            required_skill_normalized = 'nodejs'
        
        # Check if skill is missing with flexible matching
        found = False
        for user_skill in user_skills_normalized:
            if (required_skill_normalized == user_skill or 
                required_skill_normalized in user_skill or 
                user_skill in required_skill_normalized):
                found = True
                break
        
        if not found:
            skill_gaps.append(required_skill)
    
    # Limit to most important gaps (top 10)
    return skill_gaps[:10]

def predict_career_from_skills(skills):
    """Predict the most likely career based on skills in the resume"""
    if not skills:
        return None
    
    # Convert skills to lowercase for case-insensitive matching
    skills_lower = [s.lower() for s in skills]
    
    # Calculate match score for each career
    career_scores = {}
    
    for row in skills_map_list:
        career = row.get('Career','')
        skill_value = row.get('Skill','')
        
        # Safely handle skill value by converting to string
        skill_value = str(skill_value) if not pd.isna(skill_value) else ""
        
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
    
def predict_career_from_resume(text):
    """Predict the career using the ML model"""
    try:
        career, top_careers = resume_classifier.predict_career(text, return_probabilities=True)
        return career, top_careers
    except Exception as e:
        print(f"Error predicting career from resume: {e}")
        return None, []

def generate_improvement_feedback(text, skills, experience, education, projects):
    feedback = []
    text_lower = text.lower()
    
    # Check for professional summary/objective
    if not any(x in text_lower for x in ["objective", "summary", "profile", "about"]):
        feedback.append("Add a professional summary to highlight your career goals and key strengths")
    
    # Check for quantified achievements
    if not any(x in text for x in ["increased", "improved", "reduced", "saved", "achieved", "%", "percent", "$", "million", "thousand"]):
        feedback.append("Quantify your achievements with numbers, percentages, or dollar amounts")
    
    # Check for action verbs
    action_verbs = ["developed", "created", "built", "implemented", "designed", "led", "managed", "optimized", "analyzed"]
    if not any(verb in text_lower for verb in action_verbs):
        feedback.append("Use strong action verbs to describe your accomplishments")
    
    # Check for project details
    if "project" in text_lower:
        if not any(tech in text_lower for tech in ["github", "git", "repository", "demo", "deployed"]):
            feedback.append("Include links to your project repositories and live demos")
    else:
        feedback.append("Add a projects section to showcase your practical experience")
    
    # Check for contact information completeness
    contact_keywords = ["email", "@", "phone", "linkedin", "github"]
    missing_contact = []
    if "@" not in text:
        missing_contact.append("email")
    if "linkedin" not in text_lower:
        missing_contact.append("LinkedIn profile")
    if "github" not in text_lower and any(skill in ["python", "javascript", "java", "react"] for skill in skills):
        missing_contact.append("GitHub profile")
    
    if missing_contact:
        feedback.append(f"Add missing contact information: {', '.join(missing_contact)}")
    
    # Check for keywords relevant to target jobs
    if not any(modern_tech in text_lower for modern_tech in ["cloud", "api", "agile", "ci/cd", "docker"]):
        feedback.append("Include modern technology keywords relevant to current job market")
    
    # Check education details
    if "education" in text_lower or "degree" in text_lower:
        if not any(detail in text_lower for detail in ["gpa", "cgpa", "honors", "dean's list", "cum laude"]):
            feedback.append("Consider adding academic achievements or relevant coursework")
    
    # Check for soft skills
    soft_skills = ["leadership", "communication", "teamwork", "problem solving", "collaboration"]
    if not any(skill in text_lower for skill in soft_skills):
        feedback.append("Include soft skills and leadership experiences")
    
    # Check for certifications
    if not any(cert in text_lower for cert in ["certification", "certificate", "certified", "aws", "google", "microsoft"]):
        feedback.append("Add relevant certifications to strengthen your technical credibility")
    
    # Skill-specific feedback
    if len(skills) < 5:
        feedback.append("Expand your technical skills section to include more relevant technologies")
    
    # Format and length feedback
    if len(text.split()) < 200:
        feedback.append("Expand your resume content - aim for 400-600 words for better impact")
    elif len(text.split()) > 800:
        feedback.append("Consider condensing your resume - focus on most relevant experiences")
    
    return feedback[:8]  # Limit to most important feedback

def analyze_resume(text, target_career=None):
    # Initialize ML parser
    parser = MLResumeParser()
    parsed_data = parser.parse_resume(text)
    
    # Extract data using ML parser (primary method)
    name = parsed_data.get("name", "Not detected")
    contact = parsed_data.get("contact", {})
    education = parsed_data.get("education", "Not detected")
    experience = parsed_data.get("experience", "Not detected")
    projects = parsed_data.get("projects", "Not detected")
    certificates = parsed_data.get("certificates", "Not detected")
    interests = parsed_data.get("interests", "Not detected")
    
    # Process skills from ML parser
    skill_data = parsed_data.get("skills", {})
    all_skills = []
    for category, skills in skill_data.items():
        all_skills.extend(skills)
    
    # If ML parser didn't find skills, fall back to basic extraction
    if not all_skills:
        all_skills = extract_skills(text)
    
    # Auto-detect career using both approaches
    if not target_career:
        # Use ML classifier first
        career_ml, top_careers = predict_career_from_resume(text)
        # Fallback to skill-based prediction if ML fails
        if not career_ml:
            target_career = predict_career_from_skills(all_skills)
            top_careers = []
        else:
            target_career = career_ml
    else:
        # If target career provided, still get top matches
        _, top_careers = predict_career_from_resume(text)
    
    # Set a default career if prediction returns None or a non-string
    if not target_career or not isinstance(target_career, str):
        target_career = "Software Engineer"  # Default
        
    technical_skills = ", ".join(all_skills)
    qualifications = extract_qualification(text)
    interests = parsed_data.get("interests", "") or extract_interests(text)
    
    # Use improved skill gap calculation
    skill_gaps = calculate_skill_gaps(all_skills, target_career)
    
    # Section presence checks
    text_lower = text.lower()
    has_skills_section = any(re.search(r'\bskills?\b', line) for line in text.split('\n'))
    has_projects_section = "project" in text_lower
    missing_sections = []
    
    # Generate missing sections list
    if not has_skills_section:
        missing_sections.append("Skills")
    if not has_projects_section:
        missing_sections.append("Projects")
    if "certification" not in text_lower and "certificate" not in text_lower:
        missing_sections.append("Certifications")
    if not any(x in text_lower for x in ["objective", "summary"]):
        missing_sections.append("Objective/Summary")
    if "extracurricular" not in text_lower and "activity" not in text_lower:
        missing_sections.append("Extracurricular Activities")
    
    # Generate personalized feedback
    feedback = generate_improvement_feedback(text, all_skills, experience, education, projects)
    
    # Quality score
    quality_report = check_resume_quality(text, {
        'name': name,
        'contact': contact,
        'education': education,
        'experience': experience,
        'skills': all_skills,
        'skill_data': skill_data,
        'projects': projects,
        'certificates': certificates
    })
    
    return {
        "name": name,
        "contact": contact,
        "education": education,
        "certificates": certificates,
        "experience": experience,
        "technical_skills": technical_skills,
        "projects": projects,
        "missing_sections": missing_sections,
        "skill_gaps": skill_gaps,
        "improvements": feedback,
        "quality_score": quality_report["score"],
        "qualifications": qualifications,
        "skills": all_skills,
        "skill_data": skill_data,
        "interests": interests,
        "career": target_career,
    }