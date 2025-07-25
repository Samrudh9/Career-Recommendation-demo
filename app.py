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

# ===== Resume Upload Page =====
@app.route('/resume', methods=['POST'])
def handle_resume_upload():
    uploaded = request.files.get('resume')
    if not uploaded or uploaded.filename == '':
        return "❌ No resume uploaded", 400

    tmp = TemporaryFile()
    tmp.write(uploaded.read())
    tmp.seek(0)

    text = extract_text_from_file(tmp, uploaded.filename)
    if isinstance(text, str) and text.startswith("ERROR:"):
        return f"❌ {text[7:]}", 400

    result = analyze_resume(text)
    contact = result.get('contact', {})
    contact_display = f"{contact.get('email','')} | {contact.get('phone','')}"

    career_prediction = result['career']
    if isinstance(career_prediction, dict):
        if 'confidence' in career_prediction and hasattr(career_prediction['confidence'], 'item'):
            career_prediction['confidence'] = float(career_prediction['confidence'])

        if 'top_careers' in career_prediction:
            top_careers = []
            for career, conf in career_prediction['top_careers']:
                if hasattr(conf, 'item'):
                    conf = float(conf)
                top_careers.append((career, conf))
            career_prediction['top_careers'] = top_careers

    salary, _ = salary_est.estimate(
        skills=', '.join(result['skills']),
        career=result['career']['top_careers'][0][0] if result['career']['top_careers'] else None,
        qualification=result.get('education', 'Bachelors')
    )

    return render_template('result.html',
        mode="resume",
        name=result['name'],
        contact=contact_display,
        education=result['education'],
        experience=result['experience'],
        summary=result['summary'],
        technical_skills=', '.join(result['skills']),
        predicted_career=career_prediction,
        quality_score=result['quality_score'],
        skill_gaps=result['skill_gaps'],
        improvements=result['improvements'],
        certificates=result['certificates'],
        projects=result['projects'],
        predicted_salary=f"₹{salary:,}/year"
    )

# ===== Run =====
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
