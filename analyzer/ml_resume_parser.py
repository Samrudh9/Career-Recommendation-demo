import pandas as pd
import numpy as np
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Optional NLP support
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    NLP_AVAILABLE = True
except (ImportError, OSError):
    NLP_AVAILABLE = False
    print("⚠️ spaCy not available. Using rule-based name extraction only.")

class MLResumeParser:
    def __init__(self):
        # Define comprehensive skills database
        self.programming_languages = [
            "python", "java", "javascript", "typescript", "c++", "c#", "c", "php", "ruby", "go", 
            "rust", "kotlin", "swift", "scala", "r", "matlab", "sql", "html", "css", "dart"
        ]
        
        self.frameworks = [
            "react", "angular", "vue", "django", "flask", "spring", "express", "laravel", 
            "rails", "asp.net", "nodejs", "nextjs", "nuxt", "svelte", "jquery", "bootstrap"
        ]
        
        self.databases = [
            "mysql", "postgresql", "mongodb", "redis", "sqlite", "oracle", "cassandra", 
            "dynamodb", "elasticsearch", "neo4j", "firebase"
        ]
        
        self.tools = [
            "git", "docker", "kubernetes", "jenkins", "aws", "azure", "gcp", "terraform", 
            "ansible", "nginx", "apache", "linux", "windows", "macos", "jira", "confluence"
        ]
        
        self.soft_skills = [
            "leadership", "communication", "teamwork", "problem solving", "project management",
            "time management", "analytical thinking", "creative", "adaptable", "organized"
        ]
        
    def parse_resume(self, text):
        """Main parsing function that extracts all information from resume text"""
        text = self._clean_text(text)
        name = "Not provided"  # Name extraction disabled
        contact = self._extract_contact_info(text)
        sections = self._split_into_sections(text)
        education = self._extract_education_detailed(sections.get('education', ''), text)
        experience = self._extract_experience_detailed(sections.get('experience', ''), text)
        projects = self._extract_projects_detailed(sections.get('projects', ''), text)
        certificates = self._extract_certificates_detailed(sections.get('certificates', ''), text)
        skills_data = self._categorize_skills(text)
        interests = self._extract_interests(text)
        return {
            "name": name,
            "contact": contact,
            "education": education,
            "experience": experience,
            "skills": skills_data,
            "certificates": certificates,
            "projects": projects,
            "interests": interests
        }

    def _clean_text(self, text):
        """Clean and normalize the text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep essential punctuation
        text = re.sub(r'[^\w\s@.,:()\-+/]', ' ', text)
        return text.strip()
    
    def _extract_name(self, text):
        # Name extraction disabled
        return "Not provided"

    def _extract_name_improved(self, resume_text):
        # Name extraction disabled
        return "Not provided"

    def _is_valid_name(self, text, blacklist):
        # Name validation disabled
        return False
    
    def _extract_contact_info(self, text):
        """Extract contact details with regex patterns"""
        contact = {}
        
        # Improved email pattern
        email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
        # Improved phone pattern to handle various formats
        phone_pattern = r"(?:\+\d{1,3}[-\s]?)?\d{10,15}"
        # More flexible LinkedIn pattern
        linkedin_pattern = r"(?:linkedin\.com/in/|linkedin:|linkedin\s*:?\s*|LinkedIn:?\s*)([a-zA-Z0-9-]+)"
        # More flexible GitHub pattern  
        github_pattern = r"(?:github\.com/|github:|github\s*:?\s*|GitHub:?\s*)([a-zA-Z0-9-]+)"
        # Skype pattern
        skype_pattern = r"(?:skype:?|Skype\s*ID:?\s*)([a-zA-Z0-9._-]+)"
        
        emails = re.findall(email_pattern, text, re.IGNORECASE)
        contact["email"] = emails[0] if emails else ""
        
        phones = re.findall(phone_pattern, text)
        # Clean phone number (remove spaces and dashes for consistency)
        if phones:
            phone = phones[0].replace('-', '').replace(' ', '')
            contact["phone"] = phone
        else:
            contact["phone"] = ""
        
        linkedin_matches = re.findall(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_matches:
            contact["linkedin"] = f"linkedin.com/in/{linkedin_matches[0]}"
        else:
            contact["linkedin"] = ""
            
        github_matches = re.findall(github_pattern, text, re.IGNORECASE)
        if github_matches:
            contact["github"] = f"github.com/{github_matches[0]}"
        else:
            contact["github"] = ""
            
        skype_matches = re.findall(skype_pattern, text, re.IGNORECASE)
        if skype_matches:
            contact["skype"] = skype_matches[0]
        else:
            contact["skype"] = ""
        
        return contact
    
    def _extract_education(self, text):
        """Extract education information"""
        education_section = ""
        education_keywords = ["degree", "bachelor", "master", "phd", "diploma", "btech", "mtech", "b.tech", "m.tech"]
        school_keywords = ["university", "college", "institute", "school", "polytechnic"]
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in education_keywords) or any(keyword in line_lower for keyword in school_keywords):
                # Get the next few lines
                education_section += line + "\n"
                for j in range(1, 5):  # Look at next 5 lines
                    if i + j < len(lines) and lines[i + j].strip():
                        education_section += lines[i + j] + "\n"
        
        return education_section.strip()
    
    def _extract_experience(self, text):
        """Extract work experience"""
        experience_section = ""
        experience_keywords = ["experience", "work history", "employment", "intern"]
        
        lines = text.split('\n')
        in_experience = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            if any(keyword in line_lower for keyword in experience_keywords):
                in_experience = True
                experience_section += line + "\n"
            elif in_experience and i + 1 < len(lines) and any(s.lower() in lines[i + 1].lower() for s in ["education", "skills", "projects"]):
                in_experience = False
            elif in_experience:
                experience_section += line + "\n"
        
        return experience_section.strip()
    
    def _extract_education_detailed(self, education_section, full_text):
        """Extract detailed education information"""
        if not education_section.strip():
            # Fall back to searching in full text
            education_keywords = ["bachelor", "master", "phd", "degree", "university", "college"]
            lines = full_text.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in education_keywords):
                    education_section += line + '\n'
        
        return education_section.strip() if education_section.strip() else "Not detected"
    
    def _extract_experience_detailed(self, experience_section, full_text):
        """Extract detailed work experience"""
        if not experience_section.strip():
            # Fall back to searching in full text
            experience_keywords = ["intern", "developer", "engineer", "analyst", "manager", "experience"]
            lines = full_text.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in experience_keywords):
                    experience_section += line + '\n'
        
        return experience_section.strip() if experience_section.strip() else "Not detected"
    
    def _extract_projects_detailed(self, projects_section, full_text):
        """Extract detailed project information"""
        if not projects_section.strip():
            # Fall back to searching in full text with better patterns
            project_keywords = [
                "project", "built", "developed", "created", "implemented", 
                "designed", "application", "website", "system", "platform",
                "github", "repository", "repo", "technologies used"
            ]
            
            lines = full_text.split('\n')
            found_projects = []
            in_project_section = False
            
            for i, line in enumerate(lines):
                line_clean = line.strip()
                if not line_clean:
                    continue
                    
                line_lower = line_clean.lower()
                
                # Check if we're entering a projects section
                if any(keyword in line_lower for keyword in ["projects", "personal projects", "academic projects"]):
                    in_project_section = True
                    found_projects.append(line_clean)
                    continue
                
                # Check if we're leaving projects section
                if in_project_section and any(section in line_lower for section in ["education", "experience", "skills", "certifications"]):
                    in_project_section = False
                
                # If we're in projects section or find project-related content
                if in_project_section or any(keyword in line_lower for keyword in project_keywords):
                    # Skip lines that are just section headers for other sections
                    if not any(section in line_lower for section in ["education", "experience", "skills", "contact"]):
                        found_projects.append(line_clean)
            
            if found_projects:
                projects_section = '\n'.join(found_projects)
        
        return projects_section.strip() if projects_section.strip() else "Not detected"
    
    def _extract_certificates_detailed(self, certificates_section, full_text):
        """Extract detailed certification information"""
        if not certificates_section.strip():
            # Fall back to searching in full text with better patterns
            cert_keywords = [
                "certified", "certification", "certificate", "aws", "microsoft", "google",
                "oracle", "cisco", "comptia", "pmp", "itil", "scrum", "agile",
                "coursera", "udemy", "edx", "linkedin learning", "pluralsight"
            ]
            
            # Also look for patterns like "Certificate in", "Certified in", etc.
            cert_patterns = [
                r"certified?\s+in\s+\w+",
                r"certificate?\s+of\s+\w+",
                r"certification\s+in\s+\w+",
                r"\w+\s+certified",
                r"\w+\s+certificate"
            ]
            
            lines = full_text.split('\n')
            found_certs = []
            
            for line in lines:
                line_clean = line.strip()
                if not line_clean:
                    continue
                    
                line_lower = line_clean.lower()
                
                # Check for certification keywords
                if any(keyword in line_lower for keyword in cert_keywords):
                    found_certs.append(line_clean)
                    continue
                
                # Check for certification patterns
                for pattern in cert_patterns:
                    if re.search(pattern, line_lower, re.IGNORECASE):
                        found_certs.append(line_clean)
                        break
            
            if found_certs:
                certificates_section = '\n'.join(found_certs)
        
        return certificates_section.strip() if certificates_section.strip() else "Not detected"
    
    def _categorize_skills(self, text):
        """Categorize skills found in the text"""
        text_lower = text.lower()
        
        skills_data = {
            "languages": [],
            "frameworks": [],
            "databases": [],
            "tools": [],
            "soft_skills": []
        }
        
        # Find programming languages
        for lang in self.programming_languages:
            if re.search(r'\b' + re.escape(lang) + r'\b', text_lower):
                skills_data["languages"].append(lang.title())
        
        # Find frameworks
        for framework in self.frameworks:
            if re.search(r'\b' + re.escape(framework) + r'\b', text_lower):
                skills_data["frameworks"].append(framework.title())
        
        # Find databases
        for db in self.databases:
            if re.search(r'\b' + re.escape(db) + r'\b', text_lower):
                skills_data["databases"].append(db.title())
        
        # Find tools
        for tool in self.tools:
            if re.search(r'\b' + re.escape(tool) + r'\b', text_lower):
                skills_data["tools"].append(tool.upper() if tool.upper() in ['AWS', 'GCP', 'SQL'] else tool.title())
        
        # Find soft skills
        for skill in self.soft_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                skills_data["soft_skills"].append(skill.title())
        
        return skills_data
    
    def _extract_interests(self, text):
        """Extract interests and hobbies"""
        interest_keywords = ["interests", "hobbies", "activities", "passion"]
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in interest_keywords):
                # Extract content after the keyword
                for keyword in interest_keywords:
                    if keyword in line_lower:
                        parts = line_lower.split(keyword)
                        if len(parts) > 1:
                            return parts[1].strip(': ')
        
        return "Not detected"
    
    def _split_into_sections(self, text):
        """Split resume text into logical sections"""
        sections = {
            'education': '',
            'experience': '',
            'projects': '',
            'skills': '',
            'certificates': '',
            'interests': '',
            'objective': '',
            'summary': ''
        }
        
        # Common section headers
        section_patterns = {
            'education': [r'education', r'academic', r'qualification', r'degree'],
            'experience': [r'experience', r'work', r'employment', r'career', r'intern'],
            'projects': [r'projects?', r'personal projects?', r'academic projects?'],
            'skills': [r'skills?', r'technical skills?', r'competencies'],
            'certificates': [r'certifications?', r'certificates?', r'licensed?', r'awards?', r'achievements?', r'credentials?'],
            'interests': [r'interests?', r'hobbies', r'activities'],
            'objective': [r'objective', r'career objective'],
            'summary': [r'summary', r'profile', r'about']
        }
        
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            # Check if this line is a section header
            section_found = None
            for section_name, patterns in section_patterns.items():
                for pattern in patterns:
                    if re.match(rf'^{pattern}[:\s]*$', line_stripped, re.IGNORECASE):
                        section_found = section_name
                        break
                if section_found:
                    break
            
            if section_found:
                current_section = section_found
            elif current_section:
                # Add content to current section
                sections[current_section] += line_stripped + '\n'
            else:
                # If no section is identified, add to summary by default
                sections['summary'] += line_stripped + '\n'
        
        return sections