import re
import csv
import os
from collections import Counter
import pickle

class ResumeAnalyzer:
    def __init__(self, skills_career_map_path='skills_career_map.csv'):
        self.skills_career_map = self.load_skills_career_map(skills_career_map_path)
        
        # Education patterns
        self.education_patterns = [
            r'\b(?:b\.?tech|bachelor of technology|btech)\b',
            r'\b(?:m\.?tech|master of technology|mtech)\b',
            r'\b(?:mba|master of business administration)\b',
            r'\b(?:phd|ph\.d|doctor of philosophy)\b',
            r'\b(?:b\.?sc|bachelor of science|bsc)\b',
            r'\b(?:m\.?sc|master of science|msc)\b',
            r'\b(?:b\.?com|bachelor of commerce|bcom)\b',
            r'\b(?:m\.?com|master of commerce|mcom)\b',
            r'\b(?:be|bachelor of engineering)\b',
            r'\b(?:me|master of engineering)\b',
            r'\b(?:bca|bachelor of computer applications)\b',
            r'\b(?:mca|master of computer applications)\b',
            r'\b(?:diploma|certificate)\b',
            r'\b(?:12th|10th|high school|secondary)\b'
        ]
        
        # Experience patterns
        self.experience_patterns = [
            r'(?:worked|work|working)\s+(?:as|at|with|in)\s+([^.\n]+)',
            r'(?:experience|exp)\s+(?:as|at|with|in)\s+([^.\n]+)',
            r'(?:intern|internship)\s+(?:at|with|in)\s+([^.\n]+)',
            r'(?:employed|employment)\s+(?:as|at|with|in)\s+([^.\n]+)',
            r'(?:position|role)\s+(?:as|at|with|in)\s+([^.\n]+)',
            r'(\d+)\s+(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)',
            r'(?:from|since)\s+(\d{4})\s+to\s+(\d{4})',
            r'(\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{4})',
            r'(?:software\s+)?(?:developer|engineer|programmer|analyst)',
            r'(?:project\s+)?(?:manager|lead|coordinator)'
        ]
        
        # Project patterns
        self.project_patterns = [
            r'projects?\s*:?\s*\n((?:[^\n]+\n?)+)',
            r'project\s+(?:title|name)\s*:?\s*([^.\n]+)',
            r'developed\s+([^.\n]+)',
            r'built\s+([^.\n]+)',
            r'created\s+([^.\n]+)',
            r'implemented\s+([^.\n]+)',
            r'designed\s+([^.\n]+)'
        ]
        
        # Section headers
        self.education_headers = [
            'education', 'educational background', 'academic background',
            'qualifications', 'academic qualifications', 'degrees'
        ]
        
        self.experience_headers = [
            'experience', 'work experience', 'professional experience',
            'employment', 'career', 'work history', 'professional background'
        ]
        
        self.project_headers = [
            'projects', 'project work', 'project experience',
            'academic projects', 'personal projects', 'key projects'
        ]
    
    def load_skills_career_map(self, file_path):
        """Load skills to career mapping from CSV file"""
        skills_map = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        skill = row.get('Skill', '').lower().strip()
                        career = row.get('Career', '').strip()
                        if skill and career:
                            skills_map[skill] = career
            except Exception as e:
                print(f"Error loading skills career map: {e}")
        return skills_map
    
    def extract_section_content(self, text, section_headers):
        """Extract content under specific section headers"""
        content = []
        text_lower = text.lower()
        
        for header in section_headers:
            # Find section start
            pattern = rf'\b{re.escape(header)}\b\s*:?'
            matches = list(re.finditer(pattern, text_lower))
            
            for match in matches:
                start_pos = match.end()
                
                # Find next section or end of text
                next_section_pattern = r'\n\s*(?:[a-z\s]+:|\b(?:skills?|experience|education|projects?|certifications?|achievements?|summary|objective)\b)'
                next_match = re.search(next_section_pattern, text_lower[start_pos:])
                
                if next_match:
                    end_pos = start_pos + next_match.start()
                else:
                    end_pos = len(text)
                
                section_text = text[start_pos:end_pos].strip()
                if section_text:
                    content.append(section_text)
        
        return '\n'.join(content)
    
    def extract_education(self, text):
        """Extract education information from resume text"""
        education_info = []
        
        # First try to extract from education section
        education_section = self.extract_section_content(text, self.education_headers)
        search_text = education_section if education_section else text
        
        # Apply education patterns
        for pattern in self.education_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            education_info.extend(matches)
        
        # Look for degree with institution patterns
        degree_institution_patterns = [
            r'(b\.?tech|m\.?tech|mba|phd|b\.?sc|m\.?sc|be|me|bca|mca)\s+(?:in|from)\s+([^,.\n]+)',
            r'(bachelor|master|doctor)\s+of\s+([^,.\n]+)',
            r'(diploma|certificate)\s+in\s+([^,.\n]+)'
        ]
        
        for pattern in degree_institution_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    education_info.append(' '.join(match))
                else:
                    education_info.append(match)
        
        # Remove duplicates and clean up
        education_info = list(set([edu.strip() for edu in education_info if edu.strip()]))
        
        return education_info if education_info else ["Not detected"]
    
    def extract_experience(self, text):
        """Extract work experience information from resume text"""
        experience_info = []
        
        # First try to extract from experience section
        experience_section = self.extract_section_content(text, self.experience_headers)
        search_text = experience_section if experience_section else text
        
        # Apply experience patterns
        for pattern in self.experience_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        experience_info.extend([m for m in match if m])
                    else:
                        experience_info.append(match)
        
        # Look for job titles and companies
        job_company_patterns = [
            r'(?:software\s+)?(?:developer|engineer|programmer|analyst|manager|lead|intern)\s+at\s+([^,.\n]+)',
            r'(?:working|worked)\s+as\s+([^,.\n]+)\s+at\s+([^,.\n]+)',
            r'(\d+)\+?\s+(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)(?:\s+in\s+([^,.\n]+))?'
        ]
        
        for pattern in job_company_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    experience_info.extend([m.strip() for m in match if m.strip()])
                else:
                    experience_info.append(match.strip())
        
        # Clean up and remove duplicates
        experience_info = list(set([exp.strip() for exp in experience_info if exp.strip()]))
        
        return experience_info if experience_info else ["Not detected"]
    
    def extract_projects(self, text):
        """Extract project information from resume text"""
        projects_info = []
        
        # First try to extract from projects section
        projects_section = self.extract_section_content(text, self.project_headers)
        search_text = projects_section if projects_section else text
        
        # Apply project patterns
        for pattern in self.project_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    projects_info.extend([m.strip() for m in match if m.strip()])
                else:
                    projects_info.append(match.strip())
        
        # Look for project descriptions with technologies
        tech_project_patterns = [
            r'(?:project|developed|built|created)\s+(?:using|with|in)\s+([^,.\n]+)',
            r'(?:web|mobile|desktop)\s+(?:application|app|system)\s+([^,.\n]+)',
            r'(?:machine\s+learning|ai|data\s+science)\s+project\s+([^,.\n]+)'
        ]
        
        for pattern in tech_project_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            projects_info.extend([match.strip() for match in matches if match.strip()])
        
        # Extract bullet points from projects section
        if projects_section:
            bullet_patterns = [
                r'[•\-\*]\s*([^.\n]+)',
                r'\d+\.\s*([^.\n]+)'
            ]
            
            for pattern in bullet_patterns:
                matches = re.findall(pattern, projects_section, re.IGNORECASE)
                projects_info.extend([match.strip() for match in matches if match.strip()])
        
        # Clean up and remove duplicates
        projects_info = list(set([proj.strip() for proj in projects_info if proj.strip() and len(proj.strip()) > 10]))
        
        return projects_info if projects_info else ["Not detected"]
    
    def extract_skills(self, text):
        """Extract skills from resume text"""
        skills = []
        text_lower = text.lower()
        
        for skill in self.skills_career_map.keys():
            if skill in text_lower:
                skills.append(skill)
        
        return skills
    
    def calculate_resume_quality_score(self, text, skills, education, experience, projects):
        """Calculate resume quality score based on various factors"""
        score = 0
        max_score = 100
        
        # Length check (20 points)
        if len(text) > 500:
            score += 20
        elif len(text) > 200:
            score += 10
        
        # Skills section (25 points)
        if skills and skills != ["Not detected"]:
            score += min(25, len(skills) * 3)
        
        # Education section (20 points)
        if education and education != ["Not detected"]:
            score += 20
        
        # Experience section (20 points)
        if experience and experience != ["Not detected"]:
            score += 20
        
        # Projects section (15 points)
        if projects and projects != ["Not detected"]:
            score += 15
        
        return min(score, max_score)
    
    def predict_career_paths(self, skills):
        """Predict career paths based on skills"""
        if not skills:
            return []
        
        career_votes = Counter()
        for skill in skills:
            if skill in self.skills_career_map:
                career_votes[self.skills_career_map[skill]] += 1
        
        # Get top 3 career predictions
        top_careers = career_votes.most_common(3)
        return [career[0] for career in top_careers]
    
    def analyze_resume(self, text):
        """Main function to analyze resume and return comprehensive results"""
        # Extract information
        education = self.extract_education(text)
        experience = self.extract_experience(text)
        projects = self.extract_projects(text)
        skills = self.extract_skills(text)
        
        # Calculate quality score
        quality_score = self.calculate_resume_quality_score(text, skills, education, experience, projects)
        
        # Predict career paths
        career_predictions = self.predict_career_paths(skills)
        
        # Determine primary career with confidence
        primary_career = "Mobile App Developer"  # Default
        confidence = 70.0  # Default confidence
        
        if career_predictions:
            primary_career = career_predictions[0]
            # Calculate confidence based on skill matches
            skill_matches = sum(1 for skill in skills if skill in self.skills_career_map)
            confidence = min(95.0, max(50.0, (skill_matches / max(len(skills), 1)) * 100))
        
        # Alternative career paths
        alternative_careers = []
        if len(career_predictions) > 1:
            for i, career in enumerate(career_predictions[1:], 1):
                alt_confidence = max(30.0, confidence - (i * 15))
                alternative_careers.append(f"{career} ({alt_confidence:.0f}%)")
        
        # Skill gaps (simplified - could be enhanced with more sophisticated logic)
        skill_gaps = []
        if primary_career.lower() == "mobile app developer":
            required_skills = ["react native", "flutter", "swift", "kotlin", "android", "ios"]
            skill_gaps = [skill for skill in required_skills if skill not in [s.lower() for s in skills]]
        
        return {
            'education': education,
            'experience': experience,
            'projects': projects,
            'skills': skills,
            'quality_score': quality_score,
            'primary_career': primary_career,
            'confidence': confidence,
            'alternative_careers': alternative_careers,
            'skill_gaps': skill_gaps
        }

# Convenience function for external use
def analyze_resume_text(text):
    """Analyze resume text and return results"""
    analyzer = ResumeAnalyzer()
    return analyzer.analyze_resume(text)
