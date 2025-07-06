import os
import sys
import pickle
import random
import tempfile
import html
from collections.abc import Sequence
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from markupsafe import Markup
from analyzer.resume_analyzer import analyze_resume
from tempfile import TemporaryFile
from werkzeug.utils import secure_filename

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from analyzer.resume_parser import extract_text_from_file
from analyzer.resume_analyzer import analyze_resume
from analyzer.quality_checker import check_resume_quality
from analyzer.salary_estimator import salary_est

app = Flask(__name__)

# ===== Configuration =====
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'docx'}  # Removed PDF support for now
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

    resume_file = request.files['resume']
    tmp_file = TemporaryFile()
    tmp_file.write(resume_file.read())

    # Extract text from the uploaded resume
    extracted_text = extract_text_from_file(tmp_file, resume_file.filename)
    
    # Check if extraction failed with an error
    if isinstance(extracted_text, str) and extracted_text.startswith("ERROR:"):
        return f"❌ {extracted_text[7:]}", 400
    
    # Extract skills from resume text
    analysis = analyze_resume(extracted_text)
    
    # Get detected skills and predicted career
    skills_text = ", ".join(analysis.get('skills', []))
    career = analysis.get('career', "Software Developer")  # Default if no career detected
    
    # Fix qualification format - convert from list to string
    qualifications = analysis.get('qualifications', ['Bachelors'])
    qualification = qualifications[0] if qualifications else 'Bachelors'  # Take first or default
    
    # Predict salary - now with qualification as a string
    try:
        salary_value, _ = salary_est.estimate(
            skills=skills_text,
            career=str(career),  # Force string type
            qualification=str(qualification)  # Force string type
        )
        predicted_salary = f"₹{salary_value:,}/year"
    except Exception as e:
        print(f"Salary prediction failed: {e}")
        # Fallback to a default salary
        predicted_salary = f"₹750,000/year (estimated)"
    
    skill_gaps = analysis.get('skill_gaps', [])
    
    # Add resource recommendations
    yt_links = [
        f"https://www.youtube.com/results?search_query={skill}+tutorial" 
        for skill in skill_gaps[:3]
    ] if skill_gaps else []
    
    book_links = [
        f"Learn {skill.capitalize()}: The Complete Guide" 
        for skill in skill_gaps[:3]
    ] if skill_gaps else []

    # After processing analysis, determine predicted career
    predicted_career = analysis.get('career', 'Not detected')
    
    # Prepare data for template
    return render_template(
        'result.html',
        mode="resume",
        predicted_career=predicted_career,
        name=analysis.get('name', 'Not detected'),
        contact=analysis.get('contact', {}),
        education=analysis.get('education', 'Not detected'),
        technical_skills=', '.join(analysis.get('skills', [])),
        projects=analysis.get('projects', 'Not detected'),
        certificates=analysis.get('certificates', 'Not detected'),
        skill_gaps=analysis.get('skill_gaps', []),
        improvements=analysis.get('improvements', []),
        quality_score=analysis.get('quality_score', 0),
        predicted_salary=predicted_salary,
    )

# ===== Enhanced Resume Analysis Route =====
@app.route('/analyze_resume', methods=['POST'])
def resume_analysis():
    # Check if a file was uploaded
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    try:
        # Save the file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract structured information from the resume
        resume_data = extract_text_from_file(filepath, parse_structure=True)
        
        # If extraction failed
        if not resume_data:
            # Fallback to text extraction and traditional analysis
            text = extract_text_from_file(filepath)
            if not text:
                return jsonify({'error': 'Could not extract text from file'}), 500
            
            # Analyze using traditional method
            analysis = analyze_resume(text)
            
            # Sanitize the output to prevent XSS
            sanitize_data(analysis)
            
            return render_template('resume_result.html', result=analysis)
        
        # Perform additional analysis (career prediction, salary estimation)
        text = extract_text_from_file(filepath)  # Get plain text for ML models
        
        # Career prediction and other analyses
        analysis_result = analyze_resume(text)
        
        # Merge the structured data with analysis results
        result = {**resume_data}
        result['career'] = analysis_result.get('career', 'Not detected')
        result['skill_gaps'] = analysis_result.get('skill_gaps', [])
        result['improvements'] = analysis_result.get('improvements', [])
        result['quality_score'] = analysis_result.get('quality_score', 0)
        
        # Sanitize data to prevent XSS
        sanitize_data(result)
        
        # Clean up temporary file
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return render_template('resume_result.html', result=result)
    
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

# ===== Feature Disabled =====
@app.route('/multi-upload')
def multi_upload():
    # Redirect to single resume upload with a message
    # Use flash if available, otherwise redirect to regular upload
    try:
        flash("Multiple resume analysis is currently disabled. Please upload one resume at a time.", "info")
        return redirect(url_for('upload'))
    except:
        return redirect('/upload')

@app.route('/multi-resume', methods=['POST'])
def handle_multi_resume_upload():
    # Return clear message that feature is disabled
    return "Multi-resume analysis is currently disabled. Please use the single resume upload feature instead.", 400

# ===== Sanitize Data Function =====
def sanitize_data(data):
    """
    Recursively sanitize all string values in a data structure to prevent XSS.
    Works on nested dictionaries and lists.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = html.escape(value)
            elif isinstance(value, (dict, list)):
                sanitize_data(value)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, str):
                data[i] = html.escape(item)
            elif isinstance(item, (dict, list)):
                sanitize_data(item)
    return data

# ===== Run =====
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
