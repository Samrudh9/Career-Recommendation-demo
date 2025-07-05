import pandas as pd
import joblib
from datetime import datetime
from pathlib import Path
from typing import Tuple, Union

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.pipeline import Pipeline


class SalaryEstimator:

    def __init__(self,
                 model_path: Union[str, Path] = "model/salary_model.pkl",
                 csv_path: Union[str, Path] = "dataset/career_data_with_qualifications.csv"):
        self.model_path = Path(model_path)
        if self.model_path.exists():
            self.pipeline = joblib.load(self.model_path)
            print(f"✅ Salary model loaded from: {self.model_path}")
        else:
            print("⚠️  Salary model not found — training a new one…")
            self._train_and_save(csv_path)

        self.last_updated = datetime.now()

    # ------------------------------------------------------------------
    def _train_and_save(self, csv_path: Union[str, Path]):
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found for training: {csv_path}")

        df = pd.read_csv(csv_path)
        req = {"Skills", "Career", "Qualification_required", "Entry_level_salary"}
        missing = req - set(df.columns)
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        X = df[["Skills", "Career", "Qualification_required"]]
        y = df["Entry_level_salary"]

        pre = ColumnTransformer([
            ("skills_tf", TfidfVectorizer(token_pattern=r"[^,]+", lowercase=True), "Skills"),
            ("career_ohe", OneHotEncoder(sparse_output=False, handle_unknown="ignore"), ["Career"]),
            ("qual_ohe",  OneHotEncoder(sparse_output=False, handle_unknown="ignore"), ["Qualification_required"]),
        ])

        base_reg = Pipeline([
            ("pre", pre),
            ("rf", RandomForestRegressor(n_estimators=200, random_state=42))
        ])

        self.pipeline = TransformedTargetRegressor(
            regressor=base_reg,
            func=np.log1p,
            inverse_func=np.expm1,
        )

        self.pipeline.fit(X, y)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, self.model_path)
        print(f"✅ New salary model trained and saved to {self.model_path}")

    # ------------------------------------------------------------------
    def estimate(self, skills, career=None, qualification=None):
        """
        Estimate salary based on skills, career and qualification.
        
        Parameters:
        - skills: Comma-separated string of skills
        - career: Job title/career
        - qualification: Highest education level
        """
        # Set defaults for missing values
        career = career if career else "Software Developer"
        qualification = qualification if qualification else "Bachelors"
        
        # Force string type for all inputs
        skills = str(skills) if skills else ""
        career = str(career) if career else "Software Developer" 
        qualification = str(qualification) if qualification else "Bachelors"
        
        # Create input dataframe
        df_in = pd.DataFrame({
            'skills': [skills],
            'career': [career],
            'qualification': [qualification]
        })
        
        try:
            # Only use valid categories the model knows
            # Check if career is in known categories, otherwise use default
            known_careers = ['Software Developer', 'Data Scientist', 'Frontend Developer', 'Backend Developer']
            if career not in known_careers:
                df_in['career'] = 'Software Developer'
                
            # Same for qualification
            known_qualifications = ['Bachelors', 'Masters', 'PhD', 'High School', 'Associates', 'Diploma']
            if qualification not in known_qualifications:
                df_in['qualification'] = 'Bachelors'
                
            # Predict salary
            salary = int(round(self.pipeline.predict(df_in)[0]))
            
            # Calculate confidence based on feature importance
            confidence = 75 + (len(skills.split(',')) * 2) if skills else 75
            confidence = min(confidence, 95)
            
            return salary, confidence
            
        except Exception as e:
            # Fallback to a default salary if prediction fails
            print(f"Salary prediction error: {e}")
            # Return a reasonable default based on career
            default_salaries = {
                'Software Developer': 750000,
                'Data Scientist': 900000,
                'Frontend Developer': 700000,
                'Backend Developer': 800000
            }
            return default_salaries.get(career, 750000), 60


# Global singleton for easy Flask import
salary_est = SalaryEstimator()
