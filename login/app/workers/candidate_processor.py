"""
Candidate Background Processor - Handles CV parsing, LinkedIn scraping, GitHub analysis
"""
import os
import json
import asyncio
import threading
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Candidate, CandidateDocument, ProcessingStatus, DocumentType
from app.services.candidate_service import CandidateService


class CandidateProcessor:
    """
    Background processor for candidate data extraction and analysis.
    Handles CV parsing, LinkedIn scraping, and GitHub analysis.
    """

    def __init__(self):
        self.processing_queue = asyncio.Queue()
        self.is_running = False

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """
        Extract text from PDF CV using PyPDF2
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            import PyPDF2
            
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            return text.strip()
        except ImportError:
            print("PyPDF2 not installed. Install with: pip install PyPDF2")
            return ""
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    @staticmethod
    def extract_skills_from_cv_text(cv_text: str) -> list[str]:
        """
        Extract skills from CV text using keyword matching and NLP
        
        This is a simplified version. In production, you would use:
        - spaCy for NER (Named Entity Recognition)
        - Custom trained models
        - Industry-specific skill databases
        
        Args:
            cv_text: Extracted CV text
            
        Returns:
            List of identified skills
        """
        # Common technical skills to look for (expand this list)
        skill_keywords = {
            # Programming Languages
            "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
            "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
            
            # Data Science & ML
            "machine learning", "deep learning", "neural networks", "nlp", "computer vision",
            "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
            "data analysis", "data visualization", "statistics", "sql", "nosql",
            
            # Data Engineering
            "apache spark", "hadoop", "kafka", "airflow", "etl", "data pipeline",
            "aws", "azure", "gcp", "docker", "kubernetes", "jenkins",
            
            # Databases
            "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
            "cassandra", "dynamodb", "snowflake", "bigquery",
            
            # Web Development
            "react", "angular", "vue", "node.js", "express", "django", "flask",
            "fastapi", "html", "css", "rest api", "graphql",
            
            # Tools & Platforms
            "git", "github", "gitlab", "jira", "confluence", "slack",
            "linux", "bash", "powershell", "tableau", "power bi",
        }

        cv_text_lower = cv_text.lower()
        extracted_skills = []

        for skill in skill_keywords:
            if skill in cv_text_lower:
                extracted_skills.append(skill.title())

        return list(set(extracted_skills))  # Remove duplicates

    @staticmethod
    def parse_cv(db: Session, candidate_id: int) -> Dict[str, Any]:
        """
        Parse CV and extract text and skills
        
        Args:
            db: Database session
            candidate_id: Candidate ID
            
        Returns:
            Dictionary with extracted data
        """
        print(f"[CV Parser] Starting CV parsing for candidate {candidate_id}")
        
        # Get CV document
        cv_document = db.query(CandidateDocument).filter(
            CandidateDocument.candidate_id == candidate_id,
            CandidateDocument.document_type == DocumentType.CV
        ).first()

        if not cv_document:
            raise ValueError("No CV document found for candidate")

        # Extract text from PDF
        extracted_text = CandidateProcessor.extract_text_from_pdf(cv_document.file_path)
        
        # Extract skills
        skills = CandidateProcessor.extract_skills_from_cv_text(extracted_text)

        # Update document with extracted text
        cv_document.extracted_text = extracted_text[:10000]  # Store first 10k chars
        cv_document.is_processed = True
        cv_document.processed_at = datetime.utcnow()
        
        db.commit()

        print(f"[CV Parser] Extracted {len(skills)} skills from CV")
        
        return {
            "text_length": len(extracted_text),
            "skills": skills,
            "processed_at": datetime.utcnow().isoformat()
        }

    @staticmethod
    def scrape_linkedin_profile(linkedin_url: str) -> Dict[str, Any]:
        """
        Scrape LinkedIn profile data
        
        NOTE: This is a placeholder. Real LinkedIn scraping requires:
        - LinkedIn API access (official way)
        - Or web scraping with selenium/playwright (check LinkedIn TOS)
        - Proper authentication and rate limiting
        
        Args:
            linkedin_url: LinkedIn profile URL
            
        Returns:
            Dictionary with LinkedIn data
        """
        print(f"[LinkedIn Scraper] Scraping profile: {linkedin_url}")
        
        # Placeholder implementation
        # In production, integrate with LinkedIn API or scraping service
        linkedin_data = {
            "url": linkedin_url,
            "scraped_at": datetime.utcnow().isoformat(),
            "status": "placeholder",
            "message": "LinkedIn integration pending - requires API access",
            "experience": [],
            "education": [],
            "skills": [],
            "certifications": []
        }

        # TODO: Implement actual LinkedIn scraping
        # Example with LinkedIn API:
        # - Use OAuth to authenticate
        # - Call /v2/me endpoint for profile
        # - Extract experience, education, skills
        
        print("[LinkedIn Scraper] Note: Using placeholder data. Implement LinkedIn API integration.")
        
        return linkedin_data

    @staticmethod
    def analyze_github_profile(github_url: str) -> Dict[str, Any]:
        """
        Analyze GitHub profile using existing Git Analyzer
        
        Args:
            github_url: GitHub profile URL
            
        Returns:
            Dictionary with GitHub analysis data
        """
        print(f"[GitHub Analyzer] Analyzing profile: {github_url}")
        
        try:
            # Extract username from URL
            # Example: https://github.com/username -> username
            username = github_url.rstrip('/').split('/')[-1]
            
            # TODO: Integrate with existing Git Analyzer
            # Import and use the analyzer from Git Analyzer folder
            # from github_analyzer import GitHubAnalyzer
            # analyzer = GitHubAnalyzer()
            # data = analyzer.analyze_user(username)
            
            # Placeholder implementation
            github_data = {
                "username": username,
                "url": github_url,
                "analyzed_at": datetime.utcnow().isoformat(),
                "status": "placeholder",
                "message": "GitHub integration pending - use existing Git Analyzer module",
                "repositories_count": 0,
                "languages": [],
                "topics": [],
                "contribution_stats": {}
            }

            print("[GitHub Analyzer] Note: Using placeholder data. Integrate with Git Analyzer module.")
            
            return github_data
            
        except Exception as e:
            print(f"[GitHub Analyzer] Error: {e}")
            return {
                "error": str(e),
                "analyzed_at": datetime.utcnow().isoformat()
            }

    @staticmethod
    def process_candidate_data(candidate_id: int):
        """
        Main processing pipeline for candidate data
        
        Pipeline stages:
        1. Parse CV and extract text
        2. Extract skills from CV
        3. Scrape LinkedIn profile (if URL provided)
        4. Analyze GitHub profile (if URL provided)
        5. Consolidate all skills and data
        6. Update status to ready for recommendations
        
        Args:
            candidate_id: Candidate ID to process
        """
        db = SessionLocal()
        
        try:
            print(f"\n{'='*60}")
            print(f"[Processor] Starting processing for candidate {candidate_id}")
            print(f"{'='*60}\n")

            # Update status to PROCESSING
            candidate = CandidateService.update_candidate_status(
                db, candidate_id, ProcessingStatus.PROCESSING
            )

            all_skills = []
            
            # Stage 1: Parse CV
            try:
                cv_data = CandidateProcessor.parse_cv(db, candidate_id)
                all_skills.extend(cv_data.get("skills", []))
                
                CandidateService.update_candidate_status(
                    db, candidate_id, ProcessingStatus.CV_PARSED
                )
                print("✓ CV parsing completed")
            except Exception as e:
                print(f"✗ CV parsing failed: {e}")
                CandidateService.update_candidate_status(
                    db, candidate_id, ProcessingStatus.FAILED,
                    error_message=f"CV parsing failed: {str(e)}"
                )
                return

            # Stage 2: Scrape LinkedIn (if URL provided)
            if candidate.linkedin_url:
                try:
                    linkedin_data = CandidateProcessor.scrape_linkedin_profile(
                        candidate.linkedin_url
                    )
                    candidate.linkedin_profile_data = json.dumps(linkedin_data)
                    db.commit()
                    
                    # Extract skills from LinkedIn
                    linkedin_skills = linkedin_data.get("skills", [])
                    all_skills.extend(linkedin_skills)
                    
                    CandidateService.update_candidate_status(
                        db, candidate_id, ProcessingStatus.LINKEDIN_SCRAPED
                    )
                    print("✓ LinkedIn scraping completed")
                except Exception as e:
                    print(f"⚠ LinkedIn scraping failed (non-critical): {e}")

            # Stage 3: Analyze GitHub (if URL provided)
            if candidate.github_url:
                try:
                    github_data = CandidateProcessor.analyze_github_profile(
                        candidate.github_url
                    )
                    candidate.github_profile_data = json.dumps(github_data)
                    db.commit()
                    
                    # Extract languages/skills from GitHub
                    github_languages = github_data.get("languages", [])
                    all_skills.extend(github_languages)
                    
                    CandidateService.update_candidate_status(
                        db, candidate_id, ProcessingStatus.GITHUB_ANALYZED
                    )
                    print("✓ GitHub analysis completed")
                except Exception as e:
                    print(f"⚠ GitHub analysis failed (non-critical): {e}")

            # Stage 4: Consolidate and store skills
            unique_skills = list(set(all_skills))
            candidate.extracted_skills = json.dumps(unique_skills)
            db.commit()
            
            CandidateService.update_candidate_status(
                db, candidate_id, ProcessingStatus.SKILLS_EXTRACTED
            )
            print(f"✓ Skills extraction completed ({len(unique_skills)} unique skills)")

            # Stage 5: Mark as ready for recommendations
            CandidateService.update_candidate_status(
                db, candidate_id, ProcessingStatus.READY_FOR_RECOMMENDATIONS
            )

            print(f"\n{'='*60}")
            print(f"[Processor] Processing completed for candidate {candidate_id}")
            print(f"Status: READY_FOR_RECOMMENDATIONS")
            print(f"Total skills extracted: {len(unique_skills)}")
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"\n[Processor] ERROR: {e}\n")
            CandidateService.update_candidate_status(
                db, candidate_id, ProcessingStatus.FAILED,
                error_message=str(e)
            )
        finally:
            db.close()

    @staticmethod
    def start_processing_in_background(candidate_id: int):
        """
        Start processing in a background thread
        
        Args:
            candidate_id: Candidate ID to process
        """
        thread = threading.Thread(
            target=CandidateProcessor.process_candidate_data,
            args=(candidate_id,),
            daemon=True
        )
        thread.start()
        print(f"[Processor] Background processing started for candidate {candidate_id}")


# Global processor instance
processor = CandidateProcessor()
