import os
import sys
import pickle
import random
import tempfile
import uuid
import re
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from analyzer.resume_parser import extract_text_from_pdf
# Remove the problematic import and handle it conditionally
try:
    from analyzer.resume_analyzer import analyze_resume_for_app
    ENHANCED_ANALYZER_SUPPORT = True
except ImportError as e:
    print(f"Warning: Enhanced resume analyzer not available: {e}")
    ENHANCED_ANALYZER_SUPPORT = False

# Try to import the enhanced analyzer
try:
    from resume_analyzer import ResumeAnalyzer
    RESUME_ANALYZER_SUPPORT = True
except ImportError as e:
    print(f"Warning: ResumeAnalyzer not available: {e}")
    RESUME_ANALYZER_SUPPORT = False

from analyzer.quality_checker import check_resume_quality
from analyzer.salary_estimator import salary_est

# Import the career roadmap functionality
try:
    from analyzer.career_roadmap import skill_gap_analyzer, roadmap_generator
    ROADMAP_SUPPORT = True
except ImportError:
    ROADMAP_SUPPORT = False
    print("Warning: Career roadmap functionality not available.")

# Try to import docx support
try:
    from docx import Document
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False
    print("Warning: python-docx not installed, DOCX extraction will not work.")

app = Flask(__name__)

# ===== Configuration =====
UPLOAD_FOLDER = 'uploads'
# Only include DOCX if supported
ALLOWED_EXTENSIONS = {'pdf', 'docx'} if DOCX_SUPPORT else {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize the enhanced resume analyzer if available
if RESUME_ANALYZER_SUPPORT:
    try:
        resume_analyzer = ResumeAnalyzer()
    except Exception as e:
        print(f"Warning: Failed to initialize ResumeAnalyzer: {e}")
        resume_analyzer = None
        RESUME_ANALYZER_SUPPORT = False
else:
    resume_analyzer = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_docx(filepath):
    """Extract text from DOCX file"""
    if not DOCX_SUPPORT:
        return "ERROR: DOCX support not available. Please install python-docx."
    
    try:
        doc = Document(filepath)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return '\n'.join(text)
    except Exception as e:
        return f"ERROR: Failed to extract text from DOCX: {str(e)}"

def extract_text_from_file(filepath, filename):
    """Extract text from uploaded file based on extension"""
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if file_ext == 'pdf':
        return extract_text_from_pdf(filepath)
    elif file_ext == 'docx':
        return extract_text_from_docx(filepath)
    else:
        return f"ERROR: Unsupported file format: {file_ext}"

# ===== Load Trained Model =====
def load_model():
    try:
        with open('model/career_model.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        print("❌ Model not found.")
        return None

model_package = load_model()

# ===== Utility Functions =====
def normalize(text):
    return text.lower().replace('-', ' ').strip()

def fetch_job_count(career):
    simulated_counts = {
        "data scientist": 1300,
        "project manager": 900,
        "mobile app developer": 1100,
        "frontend developer": 1000,
        "backend developer": 980,
    }
    return simulated_counts.get(career.lower(), random.randint(200, 1000))

def normalize_demand(count, min_jobs=50, max_jobs=2000):
    return min(1.0, max(0.0, (count - min_jobs) / (max_jobs - min_jobs)))

def predict_career(interests, skills):
    if model_package is None:
        return [("Model not loaded", 0.0)]

    combined = []
    if isinstance(interests, str):
        combined += [normalize(x) for x in interests.split(',') if x.strip()]
    if isinstance(skills, str):
        combined += [normalize(x) for x in skills.split(',') if x.strip()]

    known_features = set(normalize(f) for f in model_package['feature_names'])
    filtered = [f for f in combined if f in known_features]

    mlb = model_package['feature_encoder']
    X = mlb.transform([filtered])

    model = model_package['classifier']
    try:
        proba = model.predict_proba(X)[0]
        careers = model.classes_

        top_indices = proba.argsort()[-5:][::-1]
        top_preds = [(careers[i], round(proba[i] * 100, 2)) for i in top_indices]

        hybrid_scores = []
        for career, conf in top_preds:
            job_count = fetch_job_count(career)
            demand_score = normalize_demand(job_count)
            final_score = round(0.7 * (conf / 100) + 0.3 * demand_score, 4)
            hybrid_scores.append((career, round(final_score * 100, 2)))

        return sorted(hybrid_scores, key=lambda x: x[1], reverse=True)[:3]
    except Exception as e:
        print(f"Model prediction error: {e}")
        # Fallback: return generic careers
        return [
            ("Software Developer", 70.0),
            ("Data Analyst", 60.0),
            ("Web Developer", 55.0)
        ]

def recommend_resources(career):
    """Simple resource recommender function"""
    resources = {
        "data scientist": [
            "Coursera: Data Science Specialization",
            "Kaggle Learn: Python and Machine Learning",
            "edX: MIT Introduction to Computer Science"
        ],
        "mobile app developer": [
            "Flutter Documentation",
            "React Native Tutorial",
            "Android Developer Guides"
        ],
        "frontend developer": [
            "MDN Web Docs",
            "freeCodeCamp: Responsive Web Design",
            "JavaScript.info"
        ],
        "backend developer": [
            "Node.js Documentation",
            "Django Tutorial",
            "REST API Best Practices"
        ]
    }
    return resources.get(career.lower(), [
        "General Programming Resources",
        "LinkedIn Learning",
        "Udemy Courses"
    ])

# ===== Routes =====
@app.route('/')
def home():
    return render_template('intro.html')

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    interests = request.form['interest']
    skills = request.form['skills']
    qualification = request.form['qualification']
    career_pref = request.form.get('career_pref', '').strip()

    predictions = predict_career(interests, skills)
    description_dict = model_package.get('descriptions', {})

    top_3_careers = []
    for career, confidence in predictions:
        description = description_dict.get(career) or \
                      description_dict.get(career.lower()) or \
                      "Description not available for this career."
        top_3_careers.append({
            'career': career,
            'confidence': confidence,
            'description': description
        })

    interests_list = [x.strip() for x in interests.split(',') if x.strip()]
    skills_list = [x.strip() for x in skills.split(',') if x.strip()]

    return render_template('result.html',
                           mode="manual",
                           name=name,
                           interests=', '.join(interests_list),
                           skills=', '.join(skills_list),
                           qualification=qualification,
                           career_pref=career_pref,
                           top_3_careers=top_3_careers)

# ===== Resume Upload Page =====
@app.route('/upload')
def upload():
    return render_template('upload_form.html')

@app.route('/resume', methods=['POST'])
def handle_resume_upload():
    resume = request.files['resume']

    if not resume or resume.filename == '':
        return "❌ No resume uploaded", 400
    
    if not allowed_file(resume.filename):
        supported_formats = ', '.join(ALLOWED_EXTENSIONS).upper()
        return f"❌ Unsupported file format. Please upload {supported_formats} files only.", 400
     
    # Generate unique filename with correct extension
    file_ext = resume.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    resume.save(filepath)

    # Extract text from resume based on file type
    extracted_text = extract_text_from_file(filepath, resume.filename)
    
    # Clean up uploaded file
    try:
        os.remove(filepath)
    except:
        pass  # Ignore cleanup errors
    
    # Check for extraction errors
    if isinstance(extracted_text, str) and extracted_text.startswith("ERROR:"):
        return f"❌ {extracted_text[7:]}", 400
    
    # Extract name from resume text
    name = extract_name_from_text(extracted_text)
    
    # Extract contact information
    contact_info = extract_contact_info(extracted_text)
    
    # Use enhanced resume analyzer if available, otherwise use basic analysis
    if RESUME_ANALYZER_SUPPORT and resume_analyzer:
        try:
            analysis_result = resume_analyzer.analyze_resume(extracted_text)
        except Exception as e:
            print(f"Enhanced analyzer failed, using basic analysis: {e}")
            analysis_result = basic_resume_analysis(extracted_text)
    else:
        analysis_result = basic_resume_analysis(extracted_text)
    
    # Get skills from analyzer
    skills_found = analysis_result.get("skills", [])
    print(f"Skills from analyzer: {skills_found}")  # Debug
    
    # If no skills detected, try basic keyword search
    if not skills_found:
        skills_found = basic_skill_detection(extracted_text)
        print(f"Skills from basic detection: {skills_found}")  # Debug
    
    # Get other extracted information with better formatting
    education = analysis_result.get("education", ["Not detected"])
    experience = analysis_result.get("experience", ["Not detected"])
    projects = analysis_result.get("projects", ["Not detected"])
    certifications = analysis_result.get("certifications", ["Not detected"])
    
    # Format education for display
    education_display = format_list_for_display(education)
    experience_display = format_list_for_display(experience)
    projects_display = format_list_for_display(projects)
    certifications_display = format_list_for_display(certifications)
    
    # Quality checking with proper error handling
    try:
        quality_report = check_resume_quality(extracted_text)
        if isinstance(quality_report, dict):
            resume_score = quality_report.get("score", 70)
            quality_tips = quality_report.get("tips", ["Resume analysis completed"])
        else:
            # If quality_report is not a dict, use fallback values
            resume_score = 70
            quality_tips = ["Resume analysis completed"]
    except Exception as e:
        print(f"Quality check error: {e}")
        resume_score = 70
        quality_tips = ["Resume analysis completed"]

    # Career prediction - handle empty skills
    skills_text = ', '.join(skills_found) if skills_found else 'programming, software development'
    predictions = predict_career("", skills_text)

    top_3_careers = []
    description_dict = model_package.get('descriptions', {}) if model_package else {}
    for career, confidence in predictions:
        description = description_dict.get(career) or \
                      description_dict.get(career.lower()) or \
                      "Description not available for this career."
        top_3_careers.append({
            'career': career,
            'confidence': confidence,
            'description': description
        })

    # Generate skill gap analysis if roadmap support is available
    skill_gap_data = None
    if ROADMAP_SUPPORT and predictions:
        primary_career = predictions[0][0]
        try:
            skill_gap_data = skill_gap_analyzer.analyze_skill_gap(skills_found, primary_career)
        except Exception as e:
            print(f"Skill gap analysis error: {e}")

    # Salary estimation with error handling
    try:
        salary_value, _ = salary_est.estimate(
            skills=skills_text,
            career=predictions[0][0] if predictions else "Software Developer",
            qualification=education[0] if education != ["Not detected"] else "Unknown"
        )
    except Exception as e:
        print(f"Salary estimation error: {e}")
        salary_value = 500000  # Default salary
    
    predicted_salary = f"₹{salary_value:,}/year"

    # Resource recommendations
    primary_career = predictions[0][0] if predictions else "software developer"
    resources = recommend_resources(primary_career)

    return render_template('result.html',
                          mode="resume",
                          name=name,
                          contact=contact_info,
                          education=education_display,
                          experience=experience_display,
                          projects=projects_display,
                          summary="Resume analysis completed",
                          technical_skills=skills_text,
                          certificates=certifications_display,
                          predicted_career=create_career_dict(predictions),
                          quality_score=analysis_result.get("quality_score", resume_score),
                          skill_gaps=skill_gap_data.get("skills_analysis", {}).get("missing_required", []) if skill_gap_data else [],
                          improvements=quality_tips,
                          predicted_salary=predicted_salary,
                          roadmap_available=ROADMAP_SUPPORT)

@app.route('/roadmap', methods=['GET', 'POST'])
def generate_roadmap():
    """Generate personalized career roadmap"""
    if not ROADMAP_SUPPORT:
        return "Career roadmap feature is not available. Please check your installation.", 500
    
    if request.method == 'POST':
        # Get form data
        career = request.form.get('career', '').strip()
        skills_input = request.form.get('skills', '').strip()
        time_months = int(request.form.get('time_months', 6))
        learning_style = request.form.get('learning_style', 'mixed')
        qualification = request.form.get('qualification', 'bachelors')
        
        # Parse skills
        user_skills = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
        
        # Generate roadmap
        roadmap_data = roadmap_generator.generate_personalized_roadmap(
            user_skills=user_skills,
            target_career=career,
            available_time_months=time_months,
            learning_style=learning_style,
            qualification=qualification
        )
        
        return render_template('roadmap_result.html', roadmap=roadmap_data)
    
    # Available careers for dropdown
    available_careers = list(skill_gap_analyzer.career_skills_db.keys())
    return render_template('roadmap_form.html', careers=available_careers)

@app.route('/skill-gap-analysis', methods=['POST'])
def analyze_skill_gap():
    """API endpoint for skill gap analysis"""
    if not ROADMAP_SUPPORT:
        return jsonify({"error": "Career roadmap feature not available"}), 500
        
    data = request.get_json()
    
    user_skills = data.get('skills', [])
    target_career = data.get('career', '')
    
    analysis = skill_gap_analyzer.analyze_skill_gap(user_skills, target_career)
    
    return jsonify(analysis)

def format_list_for_display(data_list):
    """Format list data for better display in template - handle structured data"""
    if not data_list:
        return "Not detected"
    
    # Check if it's a list of dictionaries (structured format)
    if isinstance(data_list, list) and len(data_list) > 0:
        if isinstance(data_list[0], dict):
            return data_list  # Return as-is for template to handle
        elif data_list == ["Not detected"]:
            return "Not detected"
        elif len(data_list) == 1:
            return data_list[0]
        else:
            return "\n".join([f"• {item}" for item in data_list])
    
    return str(data_list)

def create_career_dict(predictions):
    """Create a properly formatted career dictionary for the template"""
    if not predictions:
        return {
            'predicted_career': 'Software Developer',
            'confidence': 70.0,
            'top_careers': [('Software Developer', 70.0)]
        }
    
    return {
        'predicted_career': predictions[0][0],
        'confidence': predictions[0][1],
        'top_careers': predictions
    }

def extract_name_from_text(text):
    """Extract name from resume text"""
    lines = text.split('\n')
    
    # Look for name in first few lines
    for line in lines[:5]:
        line = line.strip()
        if line and len(line.split()) <= 4:
            # Skip lines with common resume keywords
            skip_keywords = ['resume', 'cv', 'curriculum', 'email', 'phone', 'mobile', '@', 'address', 'objective', 'summary']
            if not any(keyword in line.lower() for keyword in skip_keywords):
                # Check if it looks like a name (contains letters, reasonable length)
                if re.match(r'^[A-Za-z\s.]+$', line) and 2 <= len(line.split()) <= 4:
                    return line.title()
    
    return "Resume Candidate"

def extract_contact_info(text):
    """Extract contact information from resume text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'[\+]?[\d\-\(\)\s]{10,15}'
    
    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)
    
    contact_parts = []
    if emails:
        contact_parts.append(emails[0])
    if phones:
        # Clean up phone number
        phone = re.sub(r'[^\d\+]', '', phones[0])
        if len(phone) >= 10:
            contact_parts.append(phones[0])
    
    return ' | '.join(contact_parts) if contact_parts else "Contact information not detected"

def basic_skill_detection(text):
    """Fallback skill detection using common programming keywords"""
    text_lower = text.lower()
    common_skills = [
        'python', 'java', 'javascript', 'react', 'angular', 'vue', 'nodejs', 'html', 'css',
        'sql', 'mongodb', 'postgresql', 'git', 'docker', 'kubernetes', 'aws', 'azure',
        'machine learning', 'data science', 'android', 'ios', 'flutter', 'swift', 'kotlin',
        'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'typescript', 'bootstrap', 'tailwind',
        'express', 'django', 'flask', 'spring', 'laravel', 'rails', 'tensorflow', 'pytorch'
    ]
    
    detected_skills = []
    for skill in common_skills:
        if skill in text_lower:
            detected_skills.append(skill)
    
    return detected_skills

def basic_resume_analysis(text):
    """Fallback resume analysis when enhanced analyzer is not available"""
    analysis = {
        "skills": basic_skill_detection(text),
        "education": extract_education_basic(text),
        "experience": extract_experience_basic(text),
        "projects": extract_projects_basic(text),
        "certifications": extract_certifications_basic(text),
        "quality_score": 70  # Default score
    }
    return analysis

def extract_education_basic(text):
    """Basic education extraction"""
    education_keywords = ['bachelor', 'master', 'phd', 'degree', 'university', 'college', 'graduate']
    lines = text.lower().split('\n')
    education = []
    
    for line in lines:
        if any(keyword in line for keyword in education_keywords):
            education.append(line.strip())
    
    return education if education else ["Not detected"]

def extract_experience_basic(text):
    """Basic experience extraction"""
    experience_keywords = ['experience', 'worked', 'employed', 'position', 'role', 'company']
    lines = text.lower().split('\n')
    experience = []
    
    for line in lines:
        if any(keyword in line for keyword in experience_keywords):
            experience.append(line.strip())
    
    return experience if experience else ["Not detected"]

def extract_projects_basic(text):
    """Basic project extraction"""
    project_keywords = ['project', 'developed', 'built', 'created', 'implemented']
    lines = text.lower().split('\n')
    projects = []
    
    for line in lines:
        if any(keyword in line for keyword in project_keywords):
            projects.append(line.strip())
    
    return projects if projects else ["Not detected"]

def extract_certifications_basic(text):
    """Basic certification extraction"""
    cert_keywords = ['certified', 'certification', 'certificate', 'credential']
    lines = text.lower().split('\n')
    certifications = []
    
    for line in lines:
        if any(keyword in line for keyword in cert_keywords):
            certifications.append(line.strip())
    
    return certifications if certifications else ["Not detected"]

# ===== Run =====
if __name__ == '__main__':
    app.run(debug=True)