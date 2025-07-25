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
        
        # Check for structured qualification data
        structured_qualification = data.get('structured_qualification', [])
        if structured_qualification:
            # Score based on structured data
            for qual in structured_qualification:
                # Degree relevance (8 pts)
                degree = qual.get('degree', '').lower()
                major = qual.get('major', '').lower()
                relevant_keywords = ['computer', 'software', 'engineering', 'technology', 'science', 'it', 'information']
                
                if any(keyword in f"{degree} {major}" for keyword in relevant_keywords):
                    score += 8
                else:
                    score += 4
                    feedback.append("Highlight relevant coursework that relates to your target role")
                
                # Institution provided (6 pts)
                if qual.get('institution') and qual['institution'] != "Not specified":
                    score += 6
                else:
                    feedback.append("Include institution name for better credibility")
                
                # Break after first qualification to avoid over-scoring
                break
            
            # Bonus for multiple qualifications
            if len(structured_qualification) > 1:
                score += 6
        else:
            # Fallback to text-based scoring
            education = data.get('education', '')
            if not education or education == 'Not detected':
                feedback.append("Add clear education section with degree details")
                return 0, feedback
            
            # Apply existing logic for text-based scoring
            relevant_keywords = ['computer', 'software', 'engineering', 'technology', 'science', 'it', 'information']
            if any(keyword in education.lower() for keyword in relevant_keywords):
                score += 6
            else:
                score += 3
                feedback.append("Highlight relevant coursework that relates to your target role")
        
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
        
        # Check structured data first
        structured_projects = data.get('structured_projects', [])
        structured_experience = data.get('structured_experience', [])
        
        if not structured_projects and not structured_experience:
            feedback.append("Add projects section showcasing your practical work")
            return 0, feedback
        
        # Score structured projects (20 pts)
        if structured_projects:
            project_score = 0
            for project in structured_projects[:3]:  # Limit to first 3 projects
                title = project.get('title', '')
                description = project.get('description', '')
                technologies = project.get('technologies', [])
                
                # Project has clear title (3 pts)
                if title and title != "Untitled Project":
                    project_score += 3
                
                # Project has detailed description (4 pts)
                if description and len(description) > 50:
                    project_score += 4
                elif description:
                    project_score += 2
                
                # Project mentions technologies (3 pts)
                if technologies:
                    project_score += 3
                else:
                    feedback.append("Specify technologies used in your projects")
            
            score += min(15, project_score)
        
        # Score structured experience (10 pts)
        if structured_experience:
            exp_score = 0
            for exp in structured_experience[:2]:  # Limit to first 2 experiences
                job_title = exp.get('job_title', '')
                company = exp.get('company', '')
                duration = exp.get('duration', '')
                
                # Has job title (3 pts)
                if job_title:
                    exp_score += 3
                
                # Has company (3 pts)
                if company:
                    exp_score += 3
                
                # Has duration (4 pts)
                if duration and duration != "Duration not specified":
                    exp_score += 4
                else:
                    feedback.append("Include duration for work experiences")
            
            score += min(10, exp_score)
        
        # Bonus for having both projects and experience
        if structured_projects and structured_experience:
            score += 5
        
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