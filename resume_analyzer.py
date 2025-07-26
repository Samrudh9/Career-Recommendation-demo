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
        
        # Add certification headers
        self.certification_headers = [
            'certifications', 'certificates', 'certification',
            'achievements', 'awards', 'accomplishments',
            'credentials', 'licenses', 'professional certifications'
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
        """Extract content under specific section headers with improved detection"""
        content = []
        text_lower = text.lower()
        
        for header in section_headers:
            # Find section start with more flexible patterns
            patterns = [
                rf'\b{re.escape(header)}\b\s*:?',
                rf'^{re.escape(header)}\s*:?',
                rf'\n\s*{re.escape(header)}\s*:?'
            ]
            
            for pattern in patterns:
                matches = list(re.finditer(pattern, text_lower, re.MULTILINE))
                
                for match in matches:
                    start_pos = match.end()
                    
                    # Find next section or end of text
                    next_section_patterns = [
                        r'\n\s*(?:[a-z\s]+:)',
                        r'\n\s*(?:skills?|education|experience|projects?|certifications?|achievements?|summary|objective|contact|personal)\b',
                        r'\n\s*[A-Z][A-Z\s]+\n'  # All caps section headers
                    ]
                    
                    end_pos = len(text)
                    for next_pattern in next_section_patterns:
                        next_match = re.search(next_pattern, text_lower[start_pos:])
                        if next_match:
                            end_pos = start_pos + next_match.start()
                            break
                    
                    section_text = text[start_pos:end_pos].strip()
                    if section_text and len(section_text) > 10:  # Ensure meaningful content
                        content.append(section_text)
        
        return '\n'.join(content)
    
    def format_education_entry(self, match_tuple):
        """Format education entry into a LinkedIn-style structured string"""
        try:
            if len(match_tuple) == 5:
                degree, branch, institution, location, year = match_tuple
                return {
                    'degree': f"{degree.upper()} in {branch.title()}",
                    'institution': institution.title(),
                    'location': location.strip(),
                    'duration': year,
                    'type': 'degree'
                }
            elif len(match_tuple) == 4:
                degree, branch, institution, year = match_tuple
                return {
                    'degree': f"{degree.upper()} in {branch.title()}",
                    'institution': institution.title(),
                    'location': '',
                    'duration': year,
                    'type': 'degree'
                }
            elif len(match_tuple) == 3:
                degree, branch, institution = match_tuple
                return {
                    'degree': f"{degree.upper()} in {branch.title()}",
                    'institution': institution.title(),
                    'location': '',
                    'duration': '',
                    'type': 'degree'
                }
            else:
                return {
                    'degree': ' '.join(match_tuple),
                    'institution': '',
                    'location': '',
                    'duration': '',
                    'type': 'other'
                }
        except:
            return {
                'degree': ' '.join(match_tuple),
                'institution': '',
                'location': '',
                'duration': '',
                'type': 'other'
            }

    def format_experience_entry(self, match_tuple):
        """Format experience entry into a LinkedIn-style structured string"""
        if not match_tuple:
            return None
            
        try:
            # Handle single string
            if isinstance(match_tuple, str):
                return {
                    'title': match_tuple.strip(),
                    'company': '',
                    'duration': '',
                    'location': 'Remote',
                    'description': '',
                    'type': 'work'
                }
            
            # Handle tuple
            if isinstance(match_tuple, tuple):
                # Filter out empty items
                match_list = [item.strip() for item in match_tuple if item and item.strip()]
                
                if not match_list:
                    return None
                
                # Initialize result structure
                result = {
                    'title': '',
                    'company': '',
                    'duration': '',
                    'location': 'Remote',
                    'description': '',
                    'type': 'work'
                }
                
                # Identify components
                for item in match_list:
                    item_lower = item.lower()
                    if any(keyword in item_lower for keyword in ['technologies', 'solutions', 'systems', 'pvt', 'ltd', 'inc', 'corp', 'company', 'organization', 'group', 'services', 'enterprises', 'institute']):
                        result['company'] = item.title()
                    elif any(keyword in item_lower for keyword in ['intern', 'developer', 'engineer', 'analyst', 'manager', 'lead', 'executive', 'specialist', 'coordinator', 'consultant', 'designer', 'administrator', 'trainee', 'associate']):
                        result['title'] = item.title()
                    elif re.match(r'\d{4}', item) or any(month in item_lower for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                        result['duration'] = item
                
                # If we couldn't identify clearly, use order
                if not result['company'] and not result['title'] and len(match_list) >= 2:
                    result['title'] = match_list[0].title()
                    result['company'] = match_list[1].title()
                elif not result['title'] and match_list:
                    result['title'] = match_list[0].title()
                
                return result if result['title'] or result['company'] else None
            
            return None
            
        except Exception as e:
            print(f"Error formatting experience: {e}")
            return None

    def extract_education(self, text):
        """Extract education information with structured formatting"""
        education_info = []
        
        # First try to extract from education section
        education_section = self.extract_section_content(text, self.education_headers)
        search_text = education_section if education_section else text
        
        # Enhanced patterns for degree with institution and dates
        education_patterns = [
            # Pattern: Degree from Institution, Location (Year - Year)
            r'(b\.?tech|m\.?tech|mba|phd|b\.?sc|m\.?sc|be|me|bca|mca|diploma)\s+(?:in\s+)?([^,\n]+)[\s\n]*([^,\n]+(?:institute|university|college|school)[^,\n]*)[,\s]*([^,\n]*)\s*(\d{4}|\d{4}\s*-\s*\d{4}|\d{4}\s*-\s*present)',
            # Pattern: Institution - Degree (Year)
            r'([^,\n]+(?:institute|university|college|school)[^,\n]*)[,\s]*([^,\n]*)\s*(b\.?tech|m\.?tech|mba|phd|b\.?sc|m\.?sc|be|me|bca|mca)\s*(?:in\s+)?([^,\n]+)\s*(\d{4}|\d{4}\s*-\s*\d{4})',
            # Pattern: Degree in Branch from Institution
            r'(b\.?tech|m\.?tech|mba|phd|b\.?sc|m\.?sc|be|me|bca|mca)\s+(?:in\s+)?(computer science|engineering|business|science|commerce|arts|[^,\n]+)\s+(?:from\s+)?([^,\n]+(?:institute|university|college|school)[^,\n]*)'
        ]
        
        for pattern in education_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 3:
                    formatted_entry = self.format_education_entry(match)
                    if formatted_entry:
                        education_info.append(formatted_entry)
        
        # If no structured data found, try simpler extraction
        if not education_info:
            simple_patterns = [
                r'(b\.?tech|m\.?tech|mba|phd|b\.?sc|m\.?sc|be|me|bca|mca)\s+([^.\n]+)',
                r'([^.\n]+(?:institute|university|college|school)[^.\n]*)',
                r'(bachelor|master|doctor)\s+of\s+([^.\n]+)'
            ]
            
            for pattern in simple_patterns:
                matches = re.findall(pattern, search_text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        education_info.append({
                            'degree': ' '.join(match).strip().title(),
                            'institution': '',
                            'location': '',
                            'duration': '',
                            'type': 'simple'
                        })
                    else:
                        education_info.append({
                            'degree': match.strip().title(),
                            'institution': '',
                            'location': '',
                            'duration': '',
                            'type': 'simple'
                        })
        
        return education_info if education_info else [{"degree": "Not detected", "institution": "", "location": "", "duration": "", "type": "none"}]

    def extract_experience(self, text):
        """Extract experience information with structured formatting"""
        experience_info = []
        
        # First try to extract from experience section
        experience_section = self.extract_section_content(text, self.experience_headers)
        search_text = experience_section if experience_section else text
        
        # More specific patterns for actual resume content
        experience_patterns = [
            # Pattern: Company followed by position
            r'(?:^|\n)\s*([A-Z][^,\n]+(?:technologies|solutions|systems|pvt|ltd|inc|corp|company|organization|group|services|enterprises|institute)[^,\n]*)\s*[,\-–]?\s*([^,\n]*(?:intern|developer|engineer|analyst|manager|lead|executive|specialist|coordinator|consultant|designer|administrator|trainee|associate)[^,\n]*)',
            
            # Pattern: Position at Company
            r'([^,\n]*(?:intern|developer|engineer|analyst|manager|lead|executive|specialist|coordinator|consultant|designer|administrator|trainee|associate)[^,\n]*)\s+(?:at|with|@|in)\s+([A-Z][^,\n]+)',
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                formatted_exp = self.format_experience_entry(match)
                if formatted_exp:
                    experience_info.append(formatted_exp)
        
        return experience_info if experience_info else [{"title": "Not detected", "company": "", "duration": "", "location": "", "description": "", "type": "none"}]

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
    
    def extract_certifications(self, text):
        """Extract certification information from resume text"""
        certifications_info = []
        
        # First try to extract from certifications section
        certifications_section = self.extract_section_content(text, self.certification_headers)
        search_text = certifications_section if certifications_section else text
        
        print(f"Certifications section found: {certifications_section[:200] if certifications_section else 'None'}")
        
        # Certification patterns
        certification_patterns = [
            # Common certification patterns
            r'([A-Z][^,\n]*(?:certified|certification|certificate)[^,\n]*)',
            r'([A-Z][^,\n]*(?:AWS|Azure|Google Cloud|Oracle|Microsoft|Cisco|CompTIA)[^,\n]*)',
            r'([A-Z][^,\n]*(?:PMP|CISSP|CEH|CCNA|CCNP|CCIE|MCSE|MCSA)[^,\n]*)',
            r'([A-Z][^,\n]*(?:Python|Java|JavaScript|React|Angular|Node\.js)[^,\n]*(?:certified|certification)[^,\n]*)',
            r'([A-Z][^,\n]*(?:Data Science|Machine Learning|AI|Cloud|Security)[^,\n]*(?:certified|certification)[^,\n]*)',
            
            # Course completion patterns
            r'([A-Z][^,\n]*(?:course|training|bootcamp|program)[^,\n]*(?:completed|finished|graduated)[^,\n]*)',
            r'([A-Z][^,\n]*(?:Coursera|Udemy|edX|Pluralsight|LinkedIn Learning)[^,\n]*)',
            
            # Achievement patterns
            r'([A-Z][^,\n]*(?:winner|awarded|achieved|received)[^,\n]*(?:prize|award|recognition)[^,\n]*)',
            
            # Professional certifications
            r'([A-Z][^,\n]*(?:Professional|Associate|Expert|Specialist)[^,\n]*(?:certified|certification)[^,\n]*)',
        ]
        
        for pattern in certification_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 5:  # Filter out very short matches
                    certifications_info.append(match.strip())
        
        # Look for bullet points in certifications section
        if certifications_section:
            bullet_patterns = [
                r'[•\-\*]\s*([^.\n]+)',
                r'\d+\.\s*([^.\n]+)'
            ]
            
            for pattern in bullet_patterns:
                matches = re.findall(pattern, certifications_section, re.IGNORECASE)
                for match in matches:
                    if len(match.strip()) > 10:  # Filter reasonable length
                        certifications_info.append(match.strip())
        
        # Look for common certification keywords throughout the text
        cert_keywords = [
            'aws certified', 'azure certified', 'google cloud certified',
            'microsoft certified', 'oracle certified', 'cisco certified',
            'comptia', 'pmp certified', 'cissp', 'ceh', 'ccna', 'ccnp',
            'python certification', 'java certification', 'data science certification',
            'machine learning certification', 'scrum master', 'agile certification'
        ]
        
        for keyword in cert_keywords:
            if keyword in text.lower():
                # Try to extract the full certification name
                pattern = rf'([^.\n]*{re.escape(keyword)}[^.\n]*)'
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match.strip()) > 10 and len(match.strip()) < 100:
                        certifications_info.append(match.strip())
        
        # Clean up and remove duplicates
        certifications_info = list(set([cert.strip() for cert in certifications_info if cert.strip() and len(cert.strip()) > 5]))
        
        print(f"Final certifications info: {certifications_info}")
        return certifications_info if certifications_info else ["Not detected"]

    def extract_skills(self, text):
        """Extract skills from resume text with improved detection"""
        skills = []
        text_lower = text.lower()
        
        # Debug: Print available skills
        print(f"Available skills in map: {len(self.skills_career_map)} skills")
        print(f"Sample skills: {list(self.skills_career_map.keys())[:10]}")
        
        # Direct skill matching
        for skill in self.skills_career_map.keys():
            if skill in text_lower:
                skills.append(skill)
                print(f"Found skill: {skill}")
        
        # Additional skill patterns for common variations
        skill_variations = {
            'python': ['python', 'py'],
            'javascript': ['javascript', 'js', 'node.js', 'nodejs'],
            'react': ['react', 'reactjs', 'react.js'],
            'angular': ['angular', 'angularjs'],
            'vue': ['vue', 'vuejs', 'vue.js'],
            'machine learning': ['machine learning', 'ml', 'ai', 'artificial intelligence'],
            'data science': ['data science', 'data analysis', 'analytics'],
            'android': ['android', 'android development'],
            'ios': ['ios', 'iphone', 'ipad'],
            'html': ['html', 'html5'],
            'css': ['css', 'css3'],
            'sql': ['sql', 'mysql', 'postgresql', 'sqlite'],
            'git': ['git', 'github', 'gitlab'],
            'docker': ['docker', 'containerization'],
            'kubernetes': ['kubernetes', 'k8s'],
            'aws': ['aws', 'amazon web services'],
            'azure': ['azure', 'microsoft azure'],
            'tensorflow': ['tensorflow', 'tf'],
            'pytorch': ['pytorch', 'torch'],
            'react native': ['react native', 'react-native'],
            'c++': ['c++', 'cpp', 'c plus plus'],
            'rest api': ['rest', 'rest api', 'restful', 'api'],
            'graphql': ['graphql', 'graph ql'],
            'mongodb': ['mongodb', 'mongo'],
            'postgresql': ['postgresql', 'postgres'],
            'photoshop': ['photoshop', 'ps', 'adobe photoshop'],
            'illustrator': ['illustrator', 'ai', 'adobe illustrator'],
            'figma': ['figma', 'design'],
            'excel': ['excel', 'microsoft excel', 'spreadsheet']
        }
        
        # Check for skill variations
        for base_skill, variations in skill_variations.items():
            if base_skill in self.skills_career_map:
                for variation in variations:
                    if variation in text_lower and base_skill not in skills:
                        skills.append(base_skill)
                        print(f"Found skill variation: {variation} -> {base_skill}")
                        break
        
        # Look for skills in specific sections
        skills_section = self.extract_section_content(text, ['skills', 'technical skills', 'technologies', 'tools'])
        if skills_section:
            print(f"Skills section found: {skills_section[:200]}")
            # Extract from bullet points or comma-separated lists
            skill_lines = re.findall(r'[•\-\*]\s*([^.\n]+)', skills_section)
            for line in skill_lines:
                for skill in self.skills_career_map.keys():
                    if skill in line.lower() and skill not in skills:
                        skills.append(skill)
                        print(f"Found skill in bullet: {skill}")
        
        # Remove duplicates and return
        skills = list(set(skills))
        print(f"Total skills detected: {len(skills)} - {skills}")
        return skills if skills else []

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
        certifications = self.extract_certifications(text)
        
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
            'certifications': certifications,
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
    return analyzer.analyze_resume(text)
    analyzer = ResumeAnalyzer()
    return analyzer.analyze_resume(text)
    return analyzer.analyze_resume(text)
