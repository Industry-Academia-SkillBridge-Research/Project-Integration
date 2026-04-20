"""
Comprehensive Data Analysis and Training Data Preparation
For Skill Gap Detection and Career Recommendation System

This script provides:
1. Data statistics and overview
2. Data model relationships visualization
3. Student skill profile generation from transcripts
4. Job requirement analysis
5. Training dataset generation with features and labels
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from collections import defaultdict
import warnings

warnings.filterwarnings('ignore')

class DataModelAnalyzer:
    """Analyze the skill gap training data model"""
    
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.data = {}
        self.analysis_results = {}
        
    def load_data(self):
        """Load all CSV files"""
        print("=" * 80)
        print("LOADING DATA FILES")
        print("=" * 80)
        
        files_to_load = {
            'transcripts': 'transcript_data.csv',
            'job_skills': 'job_parent_skill_features.csv',
            'course_skills': 'course_skill_map.csv'
        }
        
        for key, filename in files_to_load.items():
            filepath = self.base_path / filename
            if filepath.exists():
                self.data[key] = pd.read_csv(filepath)
                print(f"✓ Loaded {key}: {filepath}")
                print(f"  - Shape: {self.data[key].shape}")
            else:
                print(f"✗ File not found: {filepath}")
        
        return self
    
    def analyze_transcripts(self):
        """Analyze student transcript structure and content"""
        print("\n" + "=" * 80)
        print("STUDENT TRANSCRIPT ANALYSIS")
        print("=" * 80)
        
        df = self.data['transcripts']
        
        # Basic statistics
        n_students = len(df)
        print(f"\nStudent Records: {n_students}")
        
        # Extract student metadata
        meta_cols = [col for col in df.columns if col.startswith(('Name', 'Reg', 'Program', 'Specialization', 'Medium', 'Admission'))]
        print(f"\nMetadata Columns: {meta_cols}")
        
        # Identify course columns (Year 1-4)
        year_patterns = defaultdict(list)
        for col in df.columns:
            for year in range(1, 5):
                if f'Y{year}_' in col:
                    year_patterns[f'Year{year}'].append(col)
        
        print(f"\nCourse Columns by Year:")
        for year, cols in sorted(year_patterns.items()):
            print(f"  {year}: {len(cols)} columns")
            # Show sample columns
            code_cols = [c for c in cols if 'Code' in c]
            grade_cols = [c for c in cols if 'Grade' in c]
            gpa_cols = [c for c in cols if 'GPA' in c or 'Credit' in c]
            if code_cols:
                print(f"    - Courses: {code_cols[:3]}...")
            if grade_cols:
                print(f"    - Grades: {grade_cols[:3]}...")
            if gpa_cols:
                print(f"    - Metrics: {gpa_cols}")
        
        # Grade analysis
        grade_cols = [col for col in df.columns if col.endswith('_Grade')]
        all_grades = []
        for col in grade_cols:
            all_grades.extend(df[col].dropna().unique())
        
        print(f"\nGrade Values Found: {sorted(set(all_grades))}")
        
        # GPA analysis
        gpa_cols = [col for col in df.columns if 'GPA' in col or 'WGPA' in col]
        print(f"\nGPA Columns: {gpa_cols}")
        
        for col in ['WGPA'] if 'WGPA' in df.columns else []:
            print(f"  {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, mean={df[col].mean():.2f}")
        
        # Sample records
        print(f"\nSample Student Records (first 3):")
        for idx, row in df.head(3).iterrows():
            print(f"  {idx+1}. {row['Name']} (ID: {row['RegNo']}) - WGPA: {row['WGPA']:.2f}")
        
        self.analysis_results['transcripts'] = {
            'n_students': n_students,
            'year_patterns': dict(year_patterns),
            'grade_cols': grade_cols,
            'gpa_cols': gpa_cols
        }
        
        return self
    
    def analyze_course_skill_mapping(self):
        """Analyze how courses map to skills"""
        print("\n" + "=" * 80)
        print("COURSE-SKILL MAPPING ANALYSIS")
        print("=" * 80)
        
        df = self.data['course_skills']
        
        print(f"\nTotal Mappings: {len(df)}")
        print(f"Unique Courses: {df['course_code'].nunique()}")
        print(f"Unique Skills: {df['skill_name'].nunique()}")
        
        # Skills per course
        skills_per_course = df.groupby('course_code').size()
        print(f"\nSkills per Course:")
        print(f"  - Average: {skills_per_course.mean():.2f}")
        print(f"  - Min: {skills_per_course.min()}")
        print(f"  - Max: {skills_per_course.max()}")
        
        # Weight distribution
        print(f"\nWeight Analysis:")
        print(f"  - Min: {df['map_weight'].min():.3f}")
        print(f"  - Max: {df['map_weight'].max():.3f}")
        print(f"  - Mean: {df['map_weight'].mean():.3f}")
        print(f"  - Median: {df['map_weight'].median():.3f}")
        
        # Sample mappings
        print(f"\nSample Course-Skill Mappings:")
        for course in df['course_code'].unique()[:3]:
            skills = df[df['course_code'] == course][['skill_name', 'map_weight']]
            print(f"  {course}:")
            for _, row in skills.iterrows():
                print(f"    - {row['skill_name']}: {row['map_weight']:.2f}")
        
        # Most common skills
        top_skills = df['skill_name'].value_counts().head(10)
        print(f"\nTop 10 Most Taught Skills:")
        for skill, count in top_skills.items():
            print(f"  - {skill}: {count} courses")
        
        self.analysis_results['course_skills'] = {
            'n_mappings': len(df),
            'n_unique_courses': df['course_code'].nunique(),
            'n_unique_skills': df['skill_name'].nunique(),
            'skills_per_course': {
                'mean': skills_per_course.mean(),
                'min': int(skills_per_course.min()),
                'max': int(skills_per_course.max())
            }
        }
        
        return self
    
    def analyze_job_requirements(self):
        """Analyze job market requirements"""
        print("\n" + "=" * 80)
        print("JOB MARKET REQUIREMENTS ANALYSIS")
        print("=" * 80)
        
        df = self.data['job_skills']
        
        # Count jobs
        print(f"\nTotal Job Listings: {len(df)}")
        
        # Extract skill columns (all columns except metadata)
        meta_cols = ['job_id', 'title', 'company', 'role_key', 'seniority_level', 'Medium']
        skill_cols = [col for col in df.columns if col not in meta_cols]
        
        print(f"Unique Skills in Job Market: {len(skill_cols)}")
        print(f"Metadata Columns: {meta_cols}")
        
        # Job distribution by role
        if 'role_key' in df.columns:
            print(f"\nJobs by Role:")
            role_counts = df['role_key'].value_counts()
            for role, count in role_counts.items():
                print(f"  - {role}: {count} positions")
        
        # Seniority distribution
        if 'seniority_level' in df.columns:
            print(f"\nJobs by Seniority:")
            seniority_counts = df['seniority_level'].value_counts()
            for level, count in seniority_counts.items():
                print(f"  - {level}: {count} positions")
        
        # Skills distribution
        skills_required = df[skill_cols].sum()
        print(f"\nSkill Requirement Distribution:")
        print(f"  - Skills required by all jobs: {(skills_required == len(df)).sum()}")
        print(f"  - Skills required by 50%+ jobs: {(skills_required >= len(df)/2).sum()}")
        print(f"  - Skills required by <10% jobs: {(skills_required < len(df)/10).sum()}")
        
        # Most required skills
        top_required = skills_required.nlargest(15)
        print(f"\nTop 15 Most Required Skills:")
        for skill, count in top_required.items():
            pct = (count / len(df)) * 100
            print(f"  - {skill}: {count} jobs ({pct:.1f}%)")
        
        # Sample jobs
        print(f"\nSample Job Listings:")
        for idx, row in df.head(3).iterrows():
            n_skills = row[skill_cols].sum()
            print(f"  {idx+1}. {row['title']} @ {row['company']} ({row['seniority_level']})")
            print(f"     Skills Required: {int(n_skills)}")
        
        self.analysis_results['job_skills'] = {
            'n_jobs': len(df),
            'n_unique_skills': len(skill_cols),
            'avg_skills_per_job': skills_required.mean(),
            'top_skills': top_required.to_dict()
        }
        
        return self
    
    def analyze_data_alignment(self):
        """Analyze alignment between data sources"""
        print("\n" + "=" * 80)
        print("DATA ALIGNMENT ANALYSIS")
        print("=" * 80)
        
        # Compare skill spaces
        course_skills_set = set(self.data['course_skills']['skill_name'].unique())
        
        job_skills_df = self.data['job_skills']
        meta_cols = ['job_id', 'title', 'company', 'role_key', 'seniority_level', 'Medium']
        job_skills_columns = [col for col in job_skills_df.columns if col not in meta_cols]
        job_skills_set = set(job_skills_columns)
        
        print(f"\nSkill Space Comparison:")
        print(f"  - Skills in courses: {len(course_skills_set)}")
        print(f"  - Skills in jobs: {len(job_skills_set)}")
        print(f"  - Overlap: {len(course_skills_set & job_skills_set)}")
        print(f"  - Coverage: {len(course_skills_set & job_skills_set) / len(job_skills_set) * 100:.1f}%")
        
        # Unique skills
        course_only = course_skills_set - job_skills_set
        job_only = job_skills_set - course_skills_set
        
        print(f"\n  Course-only skills: {len(course_only)}")
        if course_only:
            print(f"    Examples: {list(course_only)[:5]}")
        
        print(f"\n  Job-only skills: {len(job_only)}")
        if job_only:
            print(f"    Examples: {list(job_only)[:5]}")
        
        # Coverage by job
        overlapping_cols = course_skills_set & job_skills_set
        print(f"\nCoverage Analysis:")
        print(f"  - Overlapping skills: {len(overlapping_cols)}")
        
        job_skills_subset = job_skills_df[list(overlapping_cols)]
        avg_coverage = (job_skills_subset.sum(axis=1) / len(overlapping_cols) * 100).mean()
        print(f"  - Average coverage per job: {avg_coverage:.1f}%")
        
        self.analysis_results['alignment'] = {
            'course_skills': len(course_skills_set),
            'job_skills': len(job_skills_set),
            'overlapping': len(course_skills_set & job_skills_set),
            'coverage_pct': len(course_skills_set & job_skills_set) / len(job_skills_set) * 100
        }
        
        return self
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        print("\n" + "=" * 80)
        print("SUMMARY REPORT")
        print("=" * 80)
        
        report = {
            'data_model': {
                'students': self.analysis_results['transcripts']['n_students'],
                'courses': self.analysis_results['course_skills']['n_unique_courses'],
                'course_skills_mappings': self.analysis_results['course_skills']['n_mappings'],
                'unique_skills_in_curriculum': self.analysis_results['course_skills']['n_unique_skills'],
                'job_listings': self.analysis_results['job_skills']['n_jobs'],
                'unique_skills_in_market': self.analysis_results['job_skills']['n_unique_skills'],
                'skill_coverage': self.analysis_results['alignment']['coverage_pct'],
            },
            'training_potential': {
                'notes': [
                    f"Can generate skill profiles for {self.analysis_results['transcripts']['n_students']} students",
                    f"Using {self.analysis_results['course_skills']['n_unique_courses']} courses with {self.analysis_results['course_skills']['n_mappings']} skill mappings",
                    f"Match against {self.analysis_results['job_skills']['n_jobs']} job listings",
                    f"Skill space alignment: {self.analysis_results['alignment']['coverage_pct']:.1f}% coverage"
                ]
            }
        }
        
        print("\nKey Statistics:")
        for key, value in report['data_model'].items():
            print(f"  {key}: {value}")
        
        print("\nTraining Potential:")
        for note in report['training_potential']['notes']:
            print(f"  • {note}")
        
        print("\nNext Steps for Training Data Preparation:")
        print("  1. Define training objective (classification task)")
        print("  2. Create student skill profiles from transcripts and course mappings")
        print("  3. Generate labels based on job matching or readiness classes")
        print("  4. Create time-series features (skills over 4 years)")
        print("  5. Handle skill space mismatch (600+ job skills vs 50+ curriculum skills)")
        
        return report
    
    def run_analysis(self):
        """Run complete analysis pipeline"""
        self.load_data()
        self.analyze_transcripts()
        self.analyze_course_skill_mapping()
        self.analyze_job_requirements()
        self.analyze_data_alignment()
        report = self.generate_summary_report()
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        
        return report


def main():
    """Run complete data analysis"""
    # Adjust path if needed
    base_path = Path(__file__).parent
    
    analyzer = DataModelAnalyzer(base_path)
    report = analyzer.run_analysis()
    
    # Save report
    report_path = base_path / 'data_analysis_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
