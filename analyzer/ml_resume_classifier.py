try:
    import pandas as pd
except ImportError:
    pd = None
import numpy as np
import re
import pickle
import os
import spacy
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
from typing import List, Dict, Tuple, Union, Optional


class ResumeCareerClassifier:
    def __init__(self, model_path: Union[str, Path] = "model/resume_classifier.pkl"):
        """Initialize the resume career classifier model"""
        self.model_path = Path(model_path)
        self.pipeline = None
        self.label_encoder = None
        self.nlp = spacy.load("en_core_web_sm")
        self.load_or_train_model()
    
    def load_or_train_model(self) -> None:
        """Load existing model or train a new one"""
        if self.model_path.exists():
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.pipeline = data['pipeline']
                self.label_encoder = data['label_encoder']
                self.feature_importance = data.get('feature_importance', {})
            print(f"✅ Resume classifier loaded from: {self.model_path}")
        else:
            print("⚠️ Resume classifier not found - training a new one...")
            self._train_and_save()
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize resume text"""
        # Convert to lowercase
        text = text.lower()
        # Remove special characters and extra spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        # Extract key information using spaCy
        doc = self.nlp(text[:10000])  # Limit to first 10K chars for performance
        # Keep entities like skills, organizations, etc.
        entities = ' '.join([ent.text for ent in doc.ents if ent.label_ in ['ORG', 'PRODUCT', 'GPE', 'SKILL']])
        # Combine with original text
        return f"{text.strip()} {entities}".strip()
    
    def _extract_features(self, text: str) -> Dict[str, List[str]]:
        """Extract structured features from resume text"""
        features = {
            'skills': [],
            'education': [],
            'experience': []
        }
        
        # Extract skills
        skill_patterns = [
            r'skills?:?\s*(.*?)(?:\n\n|\n[A-Z]|$)',
            r'technical skills?:?\s*(.*?)(?:\n\n|\n[A-Z]|$)',
            r'technologies:?\s*(.*?)(?:\n\n|\n[A-Z]|$)'
        ]
        
        for pattern in skill_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                skills_text = match.group(1)
                # Extract skills from list or comma-separated
                skills = re.findall(r'[A-Za-z][A-Za-z0-9+#\.\-]+(?:\s*[A-Za-z0-9+#\.\-]+)*', skills_text)
                features['skills'].extend([s.lower() for s in skills if len(s) > 2])
        
        # Extract education
        edu_patterns = [
            r'education:?\s*(.*?)(?:\n\n|\n[A-Z]|$)',
            r'academic:?\s*(.*?)(?:\n\n|\n[A-Z]|$)',
            r'degree:?\s*(.*?)(?:\n\n|\n[A-Z]|$)'
        ]
        
        for pattern in edu_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                edu_text = match.group(1).lower()
                features['education'] = edu_text
                # Look for degrees
                degrees = re.findall(r'(bachelor|master|phd|diploma|associate|b\.?tech|m\.?tech|b\.?e|m\.?e)', edu_text)
                features['education'] = ' '.join(degrees) if degrees else edu_text
                
        # Extract experience
        exp_patterns = [
            r'experience:?\s*(.*?)(?:\n\n|\n[A-Z]|$)',
            r'employment:?\s*(.*?)(?:\n\n|\n[A-Z]|$)',
            r'work history:?\s*(.*?)(?:\n\n|\n[A-Z]|$)'
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                features['experience'] = match.group(1).lower()
                
        return features
    
    def _create_sample_dataset(self, dataset_path: Union[str, Path]) -> None:
        """Create a sample dataset if none exists"""
        print("⚠️ Creating sample dataset for initial training...")
        
        # Career categories
        careers = [
            'Backend Developer',
            'Frontend Developer',
            'Data Scientist',
            'Project Manager', 
            'Mobile App Developer',
            'DevOps Engineer',
            'UI/UX Designer',
            'Software Engineer',
            'Database Administrator',
            'Network Engineer'
        ]
        
        # Skills associated with each career
        career_skills = {
            'Backend Developer': [
                'python django flask api rest microservices java spring boot node.js express postgresql mysql mongodb docker aws',
                'java spring hibernate microservices restful apis jpa mysql oracle docker kubernetes jenkins',
                'node.js express typescript mongodb rest graphql docker aws serverless microservices',
                'python fastapi django postgresql redis celery docker aws lambda microservices',
                'c# .net core entity framework sql server rest apis azure devops microservices'
            ],
            'Frontend Developer': [
                'react redux javascript typescript html css webpack jest tailwind responsive',
                'angular typescript rxjs ngrx material design sass bootstrap responsive testing',
                'vue.js vuex javascript sass webpack responsive design cross-browser accessibility',
                'react next.js typescript styled-components redux material-ui responsive design accessibility',
                'javascript html css sass responsive design bootstrap jquery cross-browser testing'
            ],
            'Data Scientist': [
                'python r pandas numpy scikit-learn tensorflow keras statistics machine learning',
                'python jupyter pytorch pandas numpy matplotlib data visualization nlp computer vision',
                'r statistics regression clustering hypothesis testing data visualization tableau',
                'python sql data analysis machine learning big data spark hadoop tableau',
                'python tensorflow deep learning neural networks nlp statistics research'
            ],
            'Project Manager': [
                'agile scrum jira project management pmp stakeholder communication budget planning',
                'kanban project planning resource allocation risk management client communication',
                'waterfall sdlc project coordination timeline management stakeholder reporting',
                'prince2 project management resource planning team leadership reporting',
                'agile project management team leadership jira confluence requirements gathering'
            ],
            'Mobile App Developer': [
                'android kotlin java xml firebase gradle retrofit room architecture components',
                'ios swift swiftui xcode core data firebase cocoapods uikit arkit',
                'react native javascript redux expo firebase cross-platform mobile development',
                'flutter dart firebase state management cross-platform ui material design',
                'swift objective-c ios uikit core data push notifications in-app purchases'
            ],
            'DevOps Engineer': [
                'kubernetes docker aws terraform jenkins ci/cd github actions monitoring',
                'ansible jenkins docker kubernetes aws infrastructure as code monitoring',
                'ci/cd pipelines aws cloud formation kubernetes docker prometheus grafana',
                'azure devops terraform docker kubernetes monitoring automation scripting',
                'gcp kubernetes terraform helm docker ci/cd observability logging'
            ],
            'UI/UX Designer': [
                'figma sketch user research wireframing prototyping usability testing',
                'adobe xd photoshop illustrator user flows ui design system accessibility',
                'user research personas information architecture wireframing interaction design',
                'figma design systems prototyping user testing accessibility responsive design',
                'sketch invision prototyping interaction design usability testing research'
            ],
            'Software Engineer': [
                'java spring boot microservices object-oriented design patterns testing',
                'python django rest apis object-oriented testing docker aws',
                'c++ algorithms data structures performance optimization multithreading',
                'javascript typescript node.js express react full-stack development',
                'c# .net core asp.net entity framework sql server azure'
            ],
            'Database Administrator': [
                'sql server database administration backup recovery performance tuning security',
                'oracle database administration performance tuning pl/sql backup recovery',
                'mysql database administration replication backup performance optimization',
                'postgresql database administration backup recovery performance tuning',
                'mongodb database administration sharding replication security performance'
            ],
            'Network Engineer': [
                'cisco networking routing switching firewalls vpn security protocols',
                'network security firewalls vpn intrusion detection system penetration testing',
                'network design implementation troubleshooting cisco juniper routing switching',
                'sdwan network virtualization routing protocols monitoring troubleshooting',
                'network infrastructure design implementation maintenance security'
            ]
        }
        
        # Education levels
        education_levels = [
            'bachelors in computer science',
            'masters in computer science',
            'bachelors in information technology',
            'masters in information technology',
            'bachelors in engineering',
            'diploma in computer science',
            'phd in computer science',
            'self-taught programmer'
        ]
        
        # Experience levels
        experience_levels = [
            'internship at tech company developing software',
            '2 years experience in development',
            '5 years experience in technology industry',
            'senior level position with team management',
            '3 years experience building applications',
            'worked on multiple projects for enterprise clients',
            'freelance developer for 4 years',
            'recent graduate with internship experience'
        ]
        
        # Generate sample data
        data = []
        
        for career in careers:
            for skill_text in career_skills[career]:
                # Randomly select education and experience
                education = np.random.choice(education_levels)
                experience = np.random.choice(experience_levels)
                
                # Create a sample resume text
                resume_text = f"""
                Skills: {skill_text}
                
                Education: {education}
                
                Experience: {experience}
                """
                
                data.append({
                    'resume_text': resume_text,
                    'career_label': career
                })
        
        # Create a DataFrame
        df = pd.DataFrame(data)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
        
        # Save to CSV
        df.to_csv(dataset_path, index=False)
        print(f"✅ Sample dataset created at {dataset_path}")
    
    def _train_and_save(self) -> None:
        """Train a new model and save it to disk"""
        try:
            # Load labeled resume dataset
            base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            dataset_path = base_dir / "data" / "labeled_resumes.csv"
            
            if not dataset_path.exists():
                self._create_sample_dataset(dataset_path)
            
            df = pd.read_csv(dataset_path)
            
            # Preprocess text data
            df['processed_text'] = df['resume_text'].apply(self._preprocess_text)
            
            # Extract features and labels
            X = df['processed_text']
            y = df['career_label']
            
            # Encode labels
            self.label_encoder = LabelEncoder()
            y_encoded = self.label_encoder.fit_transform(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
            
            # Create pipeline
            self.pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=1000)),
                ('clf', RandomForestClassifier(n_estimators=100, random_state=42))
            ])
            
            # Train model
            self.pipeline.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.pipeline.predict(X_test)
            print(classification_report(y_test, y_pred, target_names=self.label_encoder.classes_))
            
            # Save model
            model_data = {
                'pipeline': self.pipeline,
                'label_encoder': self.label_encoder,
                'class_names': list(self.label_encoder.classes_),
                'descriptions': self._get_career_descriptions()
            }
            
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            print(f"✅ Model trained and saved to: {self.model_path}")
        except Exception as e:
            print(f"❌ Error training model: {e}")
            self._create_dummy_model()
    
    def _create_dummy_model(self) -> None:
        """Create a dummy model for fallback when training fails"""
        print("⚠️ Creating a dummy classifier model with default careers")
        
        # Default career classes
        default_careers = [
            "Software Developer", 
            "Data Scientist", 
            "Frontend Developer", 
            "Backend Developer",
            "Project Manager",
            "UI/UX Designer",
            "DevOps Engineer"
        ]
        
        # Create dummy label encoder
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(default_careers)
        
        # Create simple pipeline with default classifier
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000)),
            ('clf', RandomForestClassifier(n_estimators=10, random_state=42))
        ])
        
        # Create some dummy data to fit the model
        dummy_texts = [
            "python java developer software code programming",
            "data science machine learning analysis statistics",
            "html css javascript react frontend ui",
            "server api database backend cloud",
            "project management team coordination leadership",
            "design ui ux wireframe prototype",
            "devops kubernetes docker ci cd deployment"
        ]
        
        dummy_labels = np.arange(len(default_careers))
        
        # Fit the dummy model
        self.pipeline.fit(dummy_texts, dummy_labels)
        
        # Save the dummy model
        model_data = {
            'pipeline': self.pipeline,
            'label_encoder': self.label_encoder,
            'class_names': list(self.label_encoder.classes_),
            'descriptions': self._get_career_descriptions()
        }
        
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
            
        print("⚠️ Dummy model created and saved as fallback")
    
    def _get_career_descriptions(self) -> Dict[str, str]:
        """Get detailed descriptions for each career"""
        return {
            "Software Developer": "Software Developers create, design, and implement computer programs. They work across industries to build software solutions that are efficient, scalable, and secure. Strong problem-solving skills and proficiency in programming languages like Python, Java, or C++ are essential.",
            
            "Data Scientist": "Data Scientists analyze complex datasets to extract actionable insights. They use statistical methods, machine learning, and programming to solve business problems. Skills in Python, R, SQL, and visualization tools are highly valued, as is domain expertise.",
            
            "Frontend Developer": "Frontend Developers create the user interface and user experience of websites and applications. They work with HTML, CSS, and JavaScript frameworks like React, Angular, or Vue.js to build responsive, accessible, and visually appealing interfaces.",
            
            "Backend Developer": "Backend Developers build and maintain the server-side of applications, databases, and APIs. They ensure applications run efficiently, securely, and at scale. Skills include server-side languages (Python, Java, Node.js), database management, and API design.",
            
            "Project Manager": "Project Managers coordinate teams and resources to ensure successful project delivery. They create schedules, allocate resources, manage risks, and communicate with stakeholders. Strong leadership, organizational, and communication skills are essential.",
            
            "UI/UX Designer": "UI/UX Designers create intuitive, accessible, and aesthetically pleasing user experiences. They conduct user research, create wireframes and prototypes, and collaborate with developers. Skills include design thinking, proficiency with design tools, and understanding of user psychology.",
            
            "DevOps Engineer": "DevOps Engineers bridge development and operations, automating processes and managing infrastructure. They implement continuous integration/delivery pipelines and ensure system reliability. Skills include cloud platforms, containerization, automation tools, and scripting.",
            
            "Mobile App Developer": "Mobile App Developers create applications for iOS, Android, or cross-platform environments. They focus on performance, user experience, and platform-specific guidelines. Skills include Swift/Kotlin or frameworks like React Native and Flutter.",
            
            "Machine Learning Engineer": "Machine Learning Engineers design and implement AI systems. They develop models, optimize algorithms, and deploy solutions at scale. They combine strong software engineering skills with deep knowledge of machine learning techniques.",
            
            "Full Stack Developer": "Full Stack Developers work across both frontend and backend technologies. They can develop complete web applications from database to user interface. They have broad technical knowledge and can coordinate various parts of application development."
        }
    
    def get_career_description(self, career: str) -> str:
        """Get the description of a specific career"""
        descriptions = self._get_career_descriptions()
        
        # Try exact match first
        if career in descriptions:
            return descriptions[career]
        
        # Try case-insensitive match
        for c, desc in descriptions.items():
            if c.lower() == career.lower():
                return desc
        
        # Return a generic description if no match
        return f"A professional in {career} typically works on specialized projects requiring technical expertise and problem-solving skills."
    
    def predict(self, resume_text: str) -> str:
        """Predict the career path for a given resume text"""
        if not self.pipeline or not self.label_encoder:
            raise RuntimeError("Model not initialized. Please call 'load_or_train_model' first.")
        
        # Preprocess and extract features
        processed_text = self._preprocess_text(resume_text)
        
        # Predict
        pred = self.pipeline.predict([processed_text])
        prob = self.pipeline.predict_proba([processed_text])
        
        # Decode label
        career = self.label_encoder.inverse_transform(pred)[0]
        
        # Get top 3 probabilities
        top_indices = np.argsort(prob[0])[-3:][::-1]
        top_careers = self.label_encoder.inverse_transform(top_indices)
        top_probs = prob[0][top_indices]
        
        return {
            'predicted_career': career,
            'confidence': prob[0][pred][0],
            'top_careers': list(zip(top_careers, top_probs))
        }
    
    def predict_career(self, resume_text: str, return_probabilities: bool = False) -> Union[str, Tuple[str, List[Tuple[str, float]]]]:
        """
        Predict the most likely career path based on the resume text
        
        Args:
            resume_text (str): The full text of the resume
            return_probabilities (bool): If True, return top career probabilities
            
        Returns:
            If return_probabilities is False:
                str: The predicted career
            If return_probabilities is True:
                tuple: (predicted_career, [(career1, prob1), (career2, prob2), ...])
        """
        # Preprocess text
        processed_text = self._preprocess_text(resume_text)
        
        if not self.pipeline or not self.label_encoder:
            print("⚠️ Model not loaded. Using default prediction.")
            default_career = "Software Developer"
            if return_probabilities:
                return default_career, [
                    ("Software Developer", 60.0),
                    ("Data Scientist", 20.0),
                    ("Frontend Developer", 10.0)
                ]
            return default_career
        
        try:
            # Predict using pipeline
            y_proba = self.pipeline.predict_proba([processed_text])[0]
            
            # Get top 3 careers with probabilities
            top_indices = y_proba.argsort()[-3:][::-1]
            top_careers = [self.label_encoder.inverse_transform([i])[0] for i in top_indices]
            top_probs = [round(y_proba[i] * 100, 2) for i in top_indices]
            
            # Return based on flag
            if return_probabilities:
                return top_careers[0], list(zip(top_careers, top_probs))
            else:
                return top_careers[0]
                
        except Exception as e:
            print(f"⚠️ Error in career prediction: {e}")
            default_career = "Software Developer"
            if return_probabilities:
                return default_career, [
                    ("Software Developer", 60.0),
                    ("Data Scientist", 20.0),
                    ("Frontend Developer", 10.0)
                ]
            return default_career

# Create a global instance of the resume classifier for easy import
resume_classifier = ResumeCareerClassifier()
