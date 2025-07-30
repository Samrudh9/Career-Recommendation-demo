import csv
import os
from collections import defaultdict

class RoadmapGenerator:
    def __init__(self, resource_map_path='/dataset/Resource_mapping.csv'):
        self.skill_info = self._build_skill_info(resource_map_path)
        self.difficulty_map = self._create_difficulty_map()
    
    def _create_difficulty_map(self):
        """Categorize skills by difficulty level for prioritization"""
        return {
            # Foundational skills (difficulty=1)
            1: [
                'python', 'sql', 'excel', 'html', 'css', 'javascript', 'git', 
                'pandas', 'numpy', 'linux', 'bash', 'powershell', 'oop', 
                'agile', 'scrum', 'kanban', 'rest api', 'wordpress'
            ],
            # Intermediate skills (difficulty=2)
            2: [
                'scikit-learn', 'machine learning', 'data science', 'pytorch', 
                'react', 'nodejs', 'express', 'django', 'flask', 'mongodb', 
                'postgresql', 'docker', 'aws', 'azure', 'tableau', 'power bi',
                'seo', 'google analytics', 'photoshop', 'illustrator', 'figma'
            ],
            # Advanced skills (difficulty=3)
            3: [
                'tensorflow', 'deep learning', 'gan', 'nlp', 'computer vision',
                'kubernetes', 'jenkins', 'terraform', 'ansible', 'metasploit',
                'kali linux', 'penetration testing', 'cybersecurity', 'reinforcement learning'
            ]
        }
    
    def _build_skill_info(self, csv_path):
        """Build skill database from CSV resource mapping"""
        skill_info = {}
        
        if not os.path.exists(csv_path):
            print(f"Warning: Resource map not found at {csv_path}")
            return skill_info
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                skill = row['Skill'].strip().lower()
                resources = []
                
                # Process free resource
                free_resource = row['Resource(free)'].strip()
                if free_resource and free_resource.startswith('http'):
                    resources.append({
                        "title": f"Free Resource: {skill.title()}",
                        "type": "free",
                        "link": free_resource
                    })
                
                # Process paid resource
                paid_resource = row['Resource(paid)'].strip()
                if paid_resource and paid_resource.startswith('http'):
                    resources.append({
                        "title": f"Paid Resource: {skill.title()}",
                        "type": "paid",
                        "link": paid_resource
                    })
                
                if resources:
                    skill_info[skill] = {
                        "resources": resources,
                        "estimated_time_weeks": self._estimate_time(skill)
                    }
        
        return skill_info

    def _estimate_time(self, skill):
        """Estimate learning time based on difficulty level"""
        for difficulty, skills in self.difficulty_map.items():
            if skill in skills:
                return {1: 4, 2: 6, 3: 8}.get(difficulty, 6)
        return 6  # Default for unclassified skills

    def _get_difficulty(self, skill):
        """Get difficulty level for a skill"""
        for difficulty, skills in self.difficulty_map.items():
            if skill in skills:
                return difficulty
        return 2  # Default to intermediate

    def generate_roadmap(self, predicted_career, skill_gaps, matched_skills=None, 
                         skill_coverage_percent=None, resource_type=None):
        """
        Generate prioritized learning roadmap based on skill gaps
        
        :param predicted_career: Target career role
        :param skill_gaps: List of missing skills
        :param resource_type: Filter for resource type ('free' or 'paid')
        :return: Sorted list of learning steps with resources
        """
        # Prioritize skills by difficulty (foundational first)
        prioritized_skills = sorted(
            [s.lower() for s in skill_gaps],
            key=lambda s: (self._get_difficulty(s), s)
        )
        
        roadmap = []
        for skill in prioritized_skills:
            # Get resources from database or create fallback
            if skill in self.skill_info:
                entry = self.skill_info[skill]
                resources = entry["resources"]
                
                # Apply resource type filter if specified
                if resource_type:
                    resources = [r for r in resources if r["type"] == resource_type]
                
                # Use fallback if no resources after filtering
                if not resources:
                    resources = self._create_fallback_resource(skill)
            else:
                resources = self._create_fallback_resource(skill)
            
            roadmap.append({
                "skill": skill,
                "resources": resources,
                "estimated_time_weeks": self.skill_info.get(skill, {}).get("estimated_time_weeks", 6)
            })
        
        return roadmap

    def _create_fallback_resource(self, skill):
        """Create default resource entry for unknown skills"""
        return [{
            "title": f"Learn {skill.title()} (Custom Search)",
            "type": "general",
            "link": f"https://www.google.com/search?q=learn+{skill.replace(' ', '+')}"
        }]

    def generate_pdf_roadmap(self, roadmap, output_path="learning_roadmap.pdf", 
                             resource_type=None, title="Learning Roadmap"):
        """Generate PDF version of the roadmap (requires fpdf)"""
        try:
            from fpdf import FPDF
        except ImportError:
            print("PDF generation requires fpdf. Install with: pip install fpdf")
            return False

        # Create PDF document
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, title, 0, 1, "C")
        pdf.ln(10)
        
        # Add career information
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, f"Career Path: {roadmap[0]['skill'] if roadmap else 'N/A'}", 0, 1)
        pdf.ln(5)
        
        # Add roadmap items
        pdf.set_font("Arial", "", 12)
        for i, step in enumerate(roadmap):
            # Skill header
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(0, 10, f"Step {i+1}: {step['skill'].title()} ({step['estimated_time_weeks']} weeks)", 0, 1, "L", 1)
            pdf.ln(2)
            
            # Resources
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 8, "Resources:", 0, 1)
            pdf.set_font("Arial", "", 10)
            
            for resource in step["resources"]:
                # Apply resource type filter
                if resource_type and resource["type"] != resource_type:
                    continue
                    
                pdf.multi_cell(0, 6, f"- {resource['title']} ({resource['type'].title()})", 0, 1)
                pdf.set_text_color(0, 0, 255)
                pdf.cell(0, 6, f"  Link: {resource['link']}", 0, 1, link=resource["link"])
                pdf.set_text_color(0, 0, 0)
                pdf.ln(2)
            
            pdf.ln(5)
        
        # Save PDF
        pdf.output(output_path)
        return True