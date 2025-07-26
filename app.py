import os
import sys
import pickle
import random
import tempfile
import uuid
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from analyzer.resume_parser import extract_text_from_pdf
from resume_analyzer import ResumeAnalyzer  # Use the enhanced analyzer
from analyzer.quality_checker import check_resume_quality
from analyzer.salary_estimator import salary_est

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

# Initialize the enhanced resume analyzer
resume_analyzer = ResumeAnalyzer()

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
    
    # Use enhanced resume analyzer
    analysis_result = resume_analyzer.analyze_resume(extracted_text)
    
    # Get skills from enhanced analyzer
    skills_found = analysis_result.get("skills", [])
    if skills_found == ["Not detected"]:
        skills_found = []
    
    # Get other extracted information
    education = analysis_result.get("education", ["Not detected"])
    experience = analysis_result.get("experience", ["Not detected"])
    projects = analysis_result.get("projects", ["Not detected"])
    
    # Quality checking
    quality_report = check_resume_quality(extracted_text)    
    resume_score = quality_report["score"]
    quality_tips = quality_report["tips"]

    # Career prediction
    skills_text = ', '.join(skills_found)
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

    # Salary estimation
    salary_value, _ = salary_est.estimate(
        skills=skills_text,
        career=predictions[0][0] if predictions else "Software Developer",
        qualification=education[0] if education != ["Not detected"] else "Unknown"
    )
    predicted_salary = f"₹{salary_value:,}/year"

    # Resource recommendations
    primary_career = predictions[0][0] if predictions else "software developer"
    resources = recommend_resources(primary_career)

    return render_template('result.html',
                          mode="resume",
                          skills=skills_text,
                          education=education,
                          experience=experience,
                          projects=projects,
                          resume_score=resume_score,
                          quality_feedback=quality_tips,
                          predicted_salary=predicted_salary,
                          resources=resources,
                          top_3_careers=top_3_careers,
                          quality_score=analysis_result.get("quality_score", resume_score),
                          skill_gaps=analysis_result.get("skill_gaps", []))

# ===== Run =====
if __name__ == '__main__':
    app.run(debug=True)