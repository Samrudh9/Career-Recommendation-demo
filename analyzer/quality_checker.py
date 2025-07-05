import re
import pandas as pd
from typing import Dict, List, Tuple

class ResumeQualityChecker:
    """
    Professional resume quality checker based on recruiter standards.
    100-point scoring system.
    """
    
    def __init__(self):
        self.scoring_breakdown = {
            'personal_contact': 10,
            'education': 20,
            'skills': 25,
            'projects_experience': 30,
            'extracurriculars': 10,
            'presentation': 5
        }
    
    def check_resume_quality(self, text: str, extracted_data: Dict) -> Dict:
        """
        Comprehensive quality analysis based on recruiter framework.
        Returns detailed scoring and actionable feedback.
        """
        scores = {}
        feedback = []
        
        # 1. Personal Details & Contact Info (10 points)
        personal_score, personal_feedback = self._score_personal_details(text, extracted_data)
        scores['personal_contact'] = personal_score
        feedback.extend(personal_feedback)
        
        # 2. Education (20 points)
        education_score, education_feedback = self._score_education(text, extracted_data)
        scores['education'] = education_score
        feedback.extend(education_feedback)
        
        # 3. Skills Section (25 points)
        skills_score, skills_feedback = self._score_skills(text, extracted_data)
        scores['skills'] = skills_score
        feedback.extend(skills_feedback)
        
        # 4. Projects & Practical Experience (30 points)
        projects_score, projects_feedback = self._score_projects_experience(text, extracted_data)
        scores['projects_experience'] = projects_score
        feedback.extend(projects_feedback)
        
        # 5. Extracurriculars & Achievements (10 points)
        extra_score, extra_feedback = self._score_extracurriculars(text, extracted_data)
        scores['extracurriculars'] = extra_score
        feedback.extend(extra_feedback)
        
        # 6. Presentation & Hygiene (5 points)
        presentation_score, presentation_feedback = self._score_presentation(text)
        scores['presentation'] = presentation_score
        feedback.extend(presentation_feedback)
        
        total_score = sum(scores.values())
        
        return {
            'score': total_score,
            'breakdown': scores,
            'feedback': feedback,
            'grade': self._get_grade(total_score),
            'priority_improvements': self._get_priority_improvements(scores, feedback)
        }
    
    def _score_personal_details(self, text: str, data: Dict) -> Tuple[int, List[str]]:
        """Score personal details and contact information (10 points)"""
        score = 0
        feedback = []
        
        contact = data.get('contact', {})
        
        # Complete contact details (4 pts)
        contact_score = 0
        if contact.get('email'):
            contact_score += 1.5
            # Professional email check (3 pts)
            email = contact['email'].lower()
            if not any(word in email for word in ['cool', 'sexy', 'hot', '123', 'xyz', 'abc']):
                if re.match(r'^[a-zA-Z][a-zA-Z0-9._]*@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                    score += 3
                else:
                    feedback.append("Use a more professional email format")
            else:
                feedback.append("Consider using a more professional email address")
        else:
            feedback.append("Add email address to contact information")
            
        if contact.get('phone'):
            contact_score += 1.5
        else:
            feedback.append("Add phone number to contact information")
            
        if contact.get('linkedin') or 'linkedin' in text.lower():
            contact_score += 1
        else:
            feedback.append("Add LinkedIn profile URL")
            
        score += min(4, contact_score)
        
        # LinkedIn/GitHub links (3 pts)
        links_score = 0
        if contact.get('linkedin') or 'linkedin' in text.lower():
            links_score += 1.5
        if contact.get('github') or 'github' in text.lower():
            links_score += 1.5
        else:
            feedback.append("Add GitHub profile to showcase your code")
            
        score += min(3, links_score)
        
        return score, feedback
    
    def _score_education(self, text: str, data: Dict) -> Tuple[int, List[str]]:
        """Score education section (20 points)"""
        score = 0
        feedback = []
        
        education = data.get('education', '')
        if not education or education == 'Not detected':
            feedback.append("Add clear education section with degree details")
            return 0, feedback
        
        # Degree relevance (6 pts)
        relevant_keywords = ['computer', 'software', 'engineering', 'technology', 'science', 'it', 'information']
        if any(keyword in education.lower() for keyword in relevant_keywords):
            score += 6
        else:
            score += 3  # Some credit for having education
            feedback.append("Highlight relevant coursework that relates to your target role")
        
        # GPA/Grades (5 pts)
        gpa_patterns = [r'gpa[:\s]*(\d+\.?\d*)', r'cgpa[:\s]*(\d+\.?\d*)', r'grade[:\s]*[a-a+]']
        gpa_found = any(re.search(pattern, education.lower()) for pattern in gpa_patterns)
        if gpa_found:
            score += 5
        else:
            feedback.append("Include GPA if 3.0 or above (out of 4.0)")
        
        # Academic awards/certifications (5 pts)
        award_keywords = ['honor', 'dean', 'scholarship', 'award', 'distinction', 'magna cum laude']
        if any(keyword in education.lower() for keyword in award_keywords):
            score += 5
        else:
            feedback.append("Add any academic honors or achievements")
        
        # Institution reputation (4 pts) - Give some points for having institution
        if len(education.split()) > 5:  # Detailed education section
            score += 4
        else:
            score += 2
            feedback.append("Provide more details about your educational background")
        
        return min(20, score), feedback
    
    def _score_skills(self, text: str, data: Dict) -> Tuple[int, List[str]]:
        """Score skills section (25 points)"""
        score = 0
        feedback = []
        
        skills = data.get('skills', [])
        skill_data = data.get('skill_data', {})
        
        if not skills:
            feedback.append("Add a dedicated skills section")
            return 0, feedback
        
        # Hard Skills (15 pts)
        hard_skills_score = 0
        technical_skills = skill_data.get('languages', []) + skill_data.get('frameworks', []) + skill_data.get('tools', [])
        
        if len(technical_skills) >= 5:
            hard_skills_score += 8
        elif len(technical_skills) >= 3:
            hard_skills_score += 5
        else:
            feedback.append("Add more technical skills relevant to your target role")
        
        # Check for measurable proficiency
        proficiency_keywords = ['advanced', 'intermediate', 'proficient', 'expert', 'years']
        if any(keyword in text.lower() for keyword in proficiency_keywords):
            hard_skills_score += 4
        else:
            feedback.append("Specify proficiency levels for your skills (e.g., 'Python - Advanced')")
        
        # Relevance check
        relevant_tech = ['python', 'java', 'javascript', 'react', 'node', 'sql', 'git', 'aws', 'docker']
        if any(skill.lower() in relevant_tech for skill in skills):
            hard_skills_score += 3
        
        score += min(15, hard_skills_score)
        
        # Soft Skills (10 pts)
        soft_skills = skill_data.get('soft_skills', [])
        if soft_skills and len(soft_skills) >= 3:
            score += 8
        elif soft_skills:
            score += 5
        else:
            feedback.append("Add relevant soft skills with examples")
        
        # Avoid generic overuse
        generic_skills = ['team player', 'hard working', 'passionate']
        if any(generic in ' '.join(skills).lower() for generic in generic_skills):
            feedback.append("Replace generic skills with specific, measurable abilities")
        else:
            score += 2
        
        return min(25, score), feedback
    
    def _score_projects_experience(self, text: str, data: Dict) -> Tuple[int, List[str]]:
        """Score projects and practical experience (30 points)"""
        score = 0
        feedback = []
        
        projects = data.get('projects', '')
        experience = data.get('experience', '')
        
        if not projects and not experience:
            feedback.append("Add projects section showcasing your practical work")
            return 0, feedback
        
        combined_text = f"{projects} {experience}".lower()
        
        # Project Quality (20 pts)
        # Clear problem-solution-impact structure
        impact_indicators = ['improved', 'increased', 'reduced', 'optimized', 'enhanced', 'developed', 'built', 'created']
        impact_count = sum(1 for indicator in impact_indicators if indicator in combined_text)
        
        if impact_count >= 5:
            score += 8
        elif impact_count >= 3:
            score += 6
        elif impact_count >= 1:
            score += 3
        else:
            feedback.append("Use action verbs and describe the impact of your projects")
        
        # Quantifiable results
        metrics_pattern = r'\d+%|\d+\$|\d+x|by \d+|saved \d+|improved.*\d+'
        if re.search(metrics_pattern, combined_text):
            score += 6
        else:
            feedback.append("Add quantifiable metrics to your projects (e.g., 'improved performance by 40%')")
        
        # Tech stack visibility
        tech_keywords = ['python', 'react', 'node', 'database', 'api', 'framework', 'library']
        tech_count = sum(1 for tech in tech_keywords if tech in combined_text)
        if tech_count >= 3:
            score += 6
        elif tech_count >= 1:
            score += 3
        else:
            feedback.append("Clearly mention technologies and tools used in your projects")
        
        # Relevance (10 pts)
        project_types = ['web', 'mobile', 'machine learning', 'data', 'api', 'database', 'automation']
        relevant_projects = sum(1 for ptype in project_types if ptype in combined_text)
        
        if relevant_projects >= 2:
            score += 10
        elif relevant_projects >= 1:
            score += 7
        else:
            score += 3
            feedback.append("Include projects that are relevant to your target career path")
        
        return min(30, score), feedback
    
    def _score_extracurriculars(self, text: str, data: Dict) -> Tuple[int, List[str]]:
        """Score extracurriculars and achievements (10 points)"""
        score = 0
        feedback = []
        
        text_lower = text.lower()
        
        # Leadership roles (4 pts)
        leadership_keywords = ['president', 'leader', 'head', 'captain', 'coordinator', 'organizer', 'founded']
        if any(keyword in text_lower for keyword in leadership_keywords):
            score += 4
        else:
            feedback.append("Include any leadership roles or initiatives you've taken")
        
        # Volunteering/student clubs (3 pts)
        volunteer_keywords = ['volunteer', 'club', 'society', 'organization', 'community', 'ngo']
        if any(keyword in text_lower for keyword in volunteer_keywords):
            score += 3
        else:
            feedback.append("Add extracurricular activities or volunteer work")
        
        # Awards/competitions (3 pts)
        achievement_keywords = ['award', 'winner', 'competition', 'hackathon', 'contest', 'certificate', 'achievement']
        if any(keyword in text_lower for keyword in achievement_keywords):
            score += 3
        else:
            feedback.append("Include any awards, competitions, or certifications")
        
        return min(10, score), feedback
    
    def _score_presentation(self, text: str) -> Tuple[int, List[str]]:
        """Score presentation and hygiene (5 points)"""
        score = 0
        feedback = []
        
        # Consistent formatting (2 pts)
        lines = text.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        if len(non_empty_lines) > 10:  # Reasonable content length
            score += 1
        
        # Check for section headers
        headers = ['education', 'experience', 'skills', 'projects', 'certifications']
        header_count = sum(1 for header in headers if header in text.lower())
        if header_count >= 3:
            score += 1
        else:
            feedback.append("Use clear section headers (Education, Skills, Projects, etc.)")
        
        # No spelling/grammar errors (2 pts) - Basic check
        common_errors = ['teh', 'recieve', 'seperate', 'occured', 'definately']
        if not any(error in text.lower() for error in common_errors):
            score += 2
        else:
            feedback.append("Check for spelling and grammar errors")
        
        # Length appropriateness (1 pt)
        word_count = len(text.split())
        if 200 <= word_count <= 800:  # Reasonable for a resume
            score += 1
        elif word_count < 200:
            feedback.append("Resume seems too brief - add more details about your experience")
        else:
            feedback.append("Consider making your resume more concise")
        
        return min(5, score), feedback
    
    def _get_grade(self, score: int) -> str:
        """Convert numerical score to letter grade"""
        if score >= 90:
            return "A+ (Excellent)"
        elif score >= 80:
            return "A (Very Good)"
        elif score >= 70:
            return "B+ (Good)"
        elif score >= 60:
            return "B (Satisfactory)"
        elif score >= 50:
            return "C+ (Needs Improvement)"
        else:
            return "C (Major Improvements Needed)"
    
    def _get_priority_improvements(self, scores: Dict, feedback: List[str]) -> List[str]:
        """Get the most important improvements based on scoring"""
        priorities = []
        
        # Find lowest scoring areas
        sorted_scores = sorted(scores.items(), key=lambda x: x[1])
        
        for category, score in sorted_scores[:3]:  # Top 3 lowest areas
            max_score = self.scoring_breakdown[category]
            if score < max_score * 0.7:  # Less than 70% of max score
                if category == 'personal_contact':
                    priorities.append("🔥 Priority: Complete your contact information with professional email and LinkedIn")
                elif category == 'skills':
                    priorities.append("🔥 Priority: Expand and organize your skills section with proficiency levels")
                elif category == 'projects_experience':
                    priorities.append("🔥 Priority: Add detailed projects with quantifiable results and impact")
                elif category == 'education':
                    priorities.append("🔥 Priority: Enhance education section with relevant coursework and achievements")
        
        return priorities

# Legacy function for backward compatibility
def check_resume_quality(text: str, extracted_data: Dict = None) -> Dict:
    """Backward compatible function"""
    if extracted_data is None:
        extracted_data = {}
    
    checker = ResumeQualityChecker()
    result = checker.check_resume_quality(text, extracted_data)
    
    # Return in legacy format for compatibility
    return {
        "score": result['score'],
        "feedback": result['feedback'],
        "breakdown": result['breakdown'],
        "grade": result['grade']
    }