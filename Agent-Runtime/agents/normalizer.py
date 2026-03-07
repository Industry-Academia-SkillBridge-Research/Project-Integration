"""
Normalizer Agent - Maps skills to canonical names with alias resolution.

Handles:
- Lowercasing and whitespace normalization
- Alias resolution (Python3 -> Python, ML -> Machine Learning)
- Category assignment (optional)
- Skill validation against Neo4j (optional)
"""
import logging
from typing import List, Dict, Set
from models import ExtractedData, NormalizedSkill

logger = logging.getLogger(__name__)


# ============================================================================
# Skill Alias Dictionary
# ============================================================================
# Format: alias -> canonical_name
# Extend this dictionary with your domain-specific aliases

SKILL_ALIASES = {
    # Programming Languages
    "python3": "Python",
    "python2": "Python",
    "py": "Python",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "c++": "C++",
    "cpp": "C++",
    "cplusplus": "C++",
    "c#": "C#",
    "csharp": "C#",
    "c sharp": "C#",
    "c/c++": "C++",
    "r": "R",
    "rlang": "R",
    
    # Machine Learning / AI
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "ai": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    "nlp": "Natural Language Processing",
    "natural language processing": "Natural Language Processing",
    "cv": "Computer Vision",
    "computer vision": "Computer Vision",
    
    # Frameworks
    "tf": "TensorFlow",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "angular": "Angular",
    "angularjs": "Angular",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "express": "Express.js",
    "expressjs": "Express.js",
    "express.js": "Express.js",
    
    # Databases
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "mysql": "MySQL",
    "sql server": "SQL Server",
    "mssql": "SQL Server",
    "redis": "Redis",
    "neo4j": "Neo4j",
    
    # Cloud / DevOps
    "aws": "Amazon Web Services",
    "amazon web services": "Amazon Web Services",
    "azure": "Microsoft Azure",
    "microsoft azure": "Microsoft Azure",
    "gcp": "Google Cloud Platform",
    "google cloud": "Google Cloud Platform",
    "google cloud platform": "Google Cloud Platform",
    "docker": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    
    # Tools
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "jira": "Jira",
    "confluence": "Confluence",
    "figma": "Figma",
    "sketch": "Sketch",
    "adobe xd": "Adobe XD",
    "invision": "InVision",
    "postman": "Postman",
    "insomnia": "Insomnia",
    "android studio": "Android Studio",
    "androidstudio": "Android Studio",
    "visual studio": "Visual Studio",
    "visual studio code": "Visual Studio Code",
    "vs code": "Visual Studio Code",
    "vscode": "Visual Studio Code",
    "intellij": "IntelliJ IDEA",
    "intellij idea": "IntelliJ IDEA",
    "pycharm": "PyCharm",
    "eclipse": "Eclipse",
    "jupyter": "Jupyter Notebook",
    
    # Business Intelligence & Analytics Tools
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "power-bi": "Power BI",
    "microsoft power bi": "Power BI",
    "ms power bi": "Power BI",
    "tableau": "Tableau",
    "tableau desktop": "Tableau",
    "tableau public": "Tableau",
    "looker": "Looker",
    "qlik": "Qlik",
    "qlikview": "Qlik",
    "qlik sense": "Qlik Sense",
    "excel": "Excel",
    "microsoft excel": "Excel",
    "ms excel": "Excel",
    "google sheets": "Google Sheets",
    "data studio": "Google Data Studio",
    "google data studio": "Google Data Studio",
    "business intelligence": "Business Intelligence",
    "bi": "Business Intelligence",
    
    # Data Engineering & Big Data
    "apache spark": "Apache Spark",
    "pyspark": "PySpark",
    "hadoop": "Hadoop",
    "apache hadoop": "Hadoop",
    "kafka": "Apache Kafka",
    "apache kafka": "Apache Kafka",
    "airflow": "Apache Airflow",
    "apache airflow": "Apache Airflow",
    "databricks": "Databricks",
    "snowflake": "Snowflake",
    "redshift": "Amazon Redshift",
    "amazon redshift": "Amazon Redshift",
    "bigquery": "BigQuery",
    "google bigquery": "BigQuery",
    "hive": "Apache Hive",
    "apache hive": "Apache Hive",
    "elasticsearch": "Elasticsearch",
    "elastic search": "Elasticsearch",
    "elastic": "Elasticsearch",
    "kibana": "Kibana",
    "logstash": "Logstash",
    
    # Statistical & Data Science Tools
    "r": "R",
    "r programming": "R",
    "rstudio": "R",
    "sas": "SAS",
    "spss": "SPSS",
    "stata": "Stata",
    "matlab": "MATLAB",
    "julia": "Julia",
    
    # Data Science Libraries
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scipy": "SciPy",
    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "matplotlib": "Matplotlib",
    "seaborn": "Seaborn",
    "plotly": "Plotly",
    "jupyter": "Jupyter Notebook",
    "jupyter notebook": "Jupyter Notebook",
    "jupyter lab": "JupyterLab",
    "jupyterlab": "JupyterLab",
    "streamlit": "Streamlit",
    "dash": "Plotly Dash",
    "plotly dash": "Plotly Dash",
    "prophet": "Prophet",
    "facebook prophet": "Prophet",
    "xgboost": "XGBoost",
    "lightgbm": "LightGBM",
    "catboost": "CatBoost",
    
    # Data Science & Analytics (concepts)
    "data science": "Data Science",
    "data analysis": "Data Analysis",
    "data analytics": "Data Analytics",
    "business analytics": "Business Analytics",
    "statistical analysis": "Statistical Analysis",
    "quantitative analysis": "Quantitative Analysis",
    "predictive modeling": "Predictive Modeling",
    "predictive analytics": "Predictive Analytics",
    "data modeling": "Data Modeling",
    "data modelling": "Data Modeling",
    "reporting": "Reporting",
    "analytics": "Analytics",
    
    # Web Technologies
    "html": "HTML",
    "html5": "HTML5",
    "css": "CSS",
    "css3": "CSS3",
    "sass": "Sass",
    "scss": "Sass",
    "less": "Less",
    "bootstrap": "Bootstrap",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",
    "jquery": "jQuery",
    "ajax": "Ajax",
    "xml": "XML",
    "json": "JSON",
    "yaml": "YAML",
    "markdown": "Markdown",
    
    # Backend Technologies
    "nodejs": "Node.js",
    "node": "Node.js",
    "node.js": "Node.js",
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "asp.net": "ASP.NET",
    "aspnet": "ASP.NET",
    "dotnet": ".NET",
    ".net": ".NET",
    "laravel": "Laravel",
    "symfony": "Symfony",
    "ruby on rails": "Ruby on Rails",
    "rails": "Ruby on Rails",
    
    # Testing & QA
    "junit": "JUnit",
    "pytest": "Pytest",
    "selenium": "Selenium",
    "cypress": "Cypress",
    "jest": "Jest",
    "mocha": "Mocha",
    "chai": "Chai",
    
    # API & Integration
    "rest": "REST API",
    "restful": "REST API",
    "rest api": "REST API",
    "graphql": "GraphQL",
    "soap": "SOAP",
    "grpc": "gRPC",
    "webhooks": "Webhooks",
    
    # Mobile Development
    "react native": "React Native",
    "react-native": "React Native",
    "flutter": "Flutter",
    "swift": "Swift",
    "swiftui": "SwiftUI",
    "kotlin": "Kotlin",
    "xamarin": "Xamarin",
    
    # Version Control & CI/CD
    "svn": "Subversion",
    "subversion": "Subversion",
    "mercurial": "Mercurial",
    "jenkins": "Jenkins",
    "travis ci": "Travis CI",
    "circle ci": "CircleCI",
    "circleci": "CircleCI",
    "github actions": "GitHub Actions",
    "gitlab ci": "GitLab CI",
    
    # Add more aliases as needed...
}


# ============================================================================
# Skill Categories (Optional)
# ============================================================================

SKILL_CATEGORIES = {
    # Programming
    "Python": "Programming Language",
    "JavaScript": "Programming Language",
    "TypeScript": "Programming Language",
    "Java": "Programming Language",
    "C++": "Programming Language",
    "C#": "Programming Language",
    "Go": "Programming Language",
    "Rust": "Programming Language",
    "Ruby": "Programming Language",
    "PHP": "Programming Language",
    
    # ML/AI
    "Machine Learning": "Machine Learning",
    "Deep Learning": "Machine Learning",
    "Artificial Intelligence": "Machine Learning",
    "Natural Language Processing": "Machine Learning",
    "Computer Vision": "Machine Learning",
    "TensorFlow": "ML Framework",
    "PyTorch": "ML Framework",
    "Keras": "ML Framework",
    "Scikit-learn": "ML Framework",
    
    # Web Frameworks
    "React": "Web Framework",
    "Angular": "Web Framework",
    "Vue.js": "Web Framework",
    "Django": "Web Framework",
    "Flask": "Web Framework",
    "FastAPI": "Web Framework",
    "Express.js": "Web Framework",
    "Node.js": "Runtime",
    "Spring Boot": "Web Framework",
    
    # Data Science & Analytics
    "Data Science": "Data Science",
    "Data Analysis": "Data Science",
    "Data Analytics": "Data Science",
    "Business Analytics": "Data Science",
    "Statistical Analysis": "Data Science",
    "Predictive Analytics": "Data Science",
    "Predictive Modeling": "Data Science",
    "Jupyter Notebook": "Data Science Tool",
    "JupyterLab": "Data Science Tool",
    "Streamlit": "Data Science Tool",
    "Pandas": "Data Science Library",
    "NumPy": "Data Science Library",
    "Scikit-learn": "ML Framework",
    "Matplotlib": "Data Visualization",
    "Seaborn": "Data Visualization",
    "Plotly": "Data Visualization",
    "Tableau": "BI Tool",
    "Power BI": "BI Tool",
    "Excel": "Productivity Tool",
    
    # Web Technologies
    "HTML": "Web Technology",
    "HTML5": "Web Technology",
    "CSS": "Web Technology",
    "CSS3": "Web Technology",
    "JavaScript": "Programming Language",
    "jQuery": "Web Library",
    "Tailwind CSS": "Web Framework",
    "Bootstrap": "Web Framework",
    
    # Databases
    "PostgreSQL": "Database",
    "MongoDB": "Database",
    "MySQL": "Database",
    "SQL Server": "Database",
    "Redis": "Database",
    "Neo4j": "Database",
    
    # Cloud
    "Amazon Web Services": "Cloud Platform",
    "Microsoft Azure": "Cloud Platform",
    "Google Cloud Platform": "Cloud Platform",
    "Docker": "DevOps",
    "Kubernetes": "DevOps",
    "CI/CD": "DevOps",
    
    # Tools
    "Git": "Version Control",
    "GitHub": "Version Control",
    "GitLab": "Version Control",
    "Jira": "Project Management",
    "Android Studio": "IDE",
    "Visual Studio": "IDE",
    "Visual Studio Code": "IDE",
    "IntelliJ IDEA": "IDE",
    "PyCharm": "IDE",
    "Eclipse": "IDE",
    "Figma": "Design Tool",
    "Sketch": "Design Tool",
}


# Add OS categories
SKILL_CATEGORIES.update({
    "Windows": "Operating System",
    "Linux": "Operating System",
    "Ubuntu": "Operating System",
    "macOS": "Operating System",
    "Unix": "Operating System",
    "Android": "Mobile OS",
    "iOS": "Mobile OS",
})


class NormalizerAgent:
    """
    Normalizer Agent responsible for skill canonicalization.
    
    Performs:
    1. Basic normalization (strip, lowercase)
    2. Alias resolution using SKILL_ALIASES dictionary
    3. Category assignment (optional)
    """
    
    def __init__(self, aliases: Dict[str, str] = None):
        """
        Initialize normalizer with custom alias dictionary.
        
        Args:
            aliases: Custom skill alias mapping (default: SKILL_ALIASES)
        """
        self.aliases = aliases or SKILL_ALIASES
        logger.info(f"Normalizer initialized with {len(self.aliases)} aliases")
    
    def normalize_skill(self, skill_name: str) -> NormalizedSkill:
        """
        Normalize a single skill name.
        
        Args:
            skill_name: Original skill name
            
        Returns:
            NormalizedSkill with canonical name and category
        """
        original = skill_name
        
        # Step 1: Basic normalization
        normalized = skill_name.strip().lower()
        
        # Step 2: Alias resolution
        canonical = self.aliases.get(normalized, skill_name.strip())
        
        # Step 3: Category assignment
        category = SKILL_CATEGORIES.get(canonical, "unknown")
        
        return NormalizedSkill(
            original_name=original,
            canonical_name=canonical,
            category=category
        )
    
    def normalize_skills(self, skills: List[str]) -> List[NormalizedSkill]:
        """
        Normalize a list of skill names.
        
        Args:
            skills: List of original skill names
            
        Returns:
            List of NormalizedSkill objects (deduplicated by canonical name)
        """
        normalized_map: Dict[str, NormalizedSkill] = {}
        
        for skill in skills:
            norm_skill = self.normalize_skill(skill)
            # Deduplicate by canonical name (keep first occurrence)
            if norm_skill.canonical_name not in normalized_map:
                normalized_map[norm_skill.canonical_name] = norm_skill
        
        normalized_list = list(normalized_map.values())
        
        logger.info(
            f"Normalized {len(skills)} skills -> {len(normalized_list)} unique canonical skills"
        )
        
        return normalized_list
    
    def normalize_extracted_data(self, extracted_data: ExtractedData) -> ExtractedData:
        """
        Normalize all skills in the extracted data.
        
        Normalizes skills from:
        - Categorized skills structure (programming_languages, frameworks, etc.)
        - Project technologies
        
        Args:
            extracted_data: Raw extracted data from combined_resumes.json
            
        Returns:
            ExtractedData with normalized skill names and populated all_skills
        """
        logger.info(f"Normalizing skills for candidate: {extracted_data.candidate_id}")
        
        # DEBUG logging
        logger.info(f"DEBUG normalizer: extracted_data type = {type(extracted_data)}")
        logger.info(f"DEBUG normalizer: has skills? {hasattr(extracted_data, 'skills')}")
        logger.info(f"DEBUG normalizer: skills value = {extracted_data.skills if hasattr(extracted_data, 'skills') else 'NO ATTR'}")
        
        # Collect all unique skill names
        all_skill_names: Set[str] = set()
        
        # From categorized skills
        if extracted_data.skills and len(extracted_data.skills) > 0:
            skills_obj = extracted_data.skills[0]  # First element contains categorized skills
            
            # Handle both Pydantic object and dict (defensive coding)
            if isinstance(skills_obj, dict):
                all_skill_names.update(skills_obj.get('programming_languages', []))
                all_skill_names.update(skills_obj.get('frameworks', []))
                all_skill_names.update(skills_obj.get('technologies', []))
                all_skill_names.update(skills_obj.get('technical_skills', []))
                all_skill_names.update(skills_obj.get('database', []))
                all_skill_names.update(skills_obj.get('soft_skills', []))
            else:
                # Pydantic object
                all_skill_names.update(skills_obj.programming_languages)
                all_skill_names.update(skills_obj.frameworks)
                all_skill_names.update(skills_obj.technologies)
                all_skill_names.update(skills_obj.technical_skills)
                all_skill_names.update(skills_obj.database)
                all_skill_names.update(skills_obj.soft_skills)
        
        # From projects
        for project in extracted_data.projects_and_technologies_involved:
            all_skill_names.update(project.technologies_used)
        
        # Normalize all unique skills
        normalized_skills = self.normalize_skills(list(all_skill_names))
        
        # Create mapping: original -> canonical
        normalization_map = {
            ns.original_name: ns.canonical_name
            for ns in normalized_skills
        }
        
        # Apply normalization to categorized skills
        if extracted_data.skills and len(extracted_data.skills) > 0:
            skills_obj = extracted_data.skills[0]
            
            skills_obj.programming_languages = [
                normalization_map.get(s, s) for s in skills_obj.programming_languages
            ]
            skills_obj.frameworks = [
                normalization_map.get(s, s) for s in skills_obj.frameworks
            ]
            skills_obj.technologies = [
                normalization_map.get(s, s) for s in skills_obj.technologies
            ]
            skills_obj.technical_skills = [
                normalization_map.get(s, s) for s in skills_obj.technical_skills
            ]
            skills_obj.database = [
                normalization_map.get(s, s) for s in skills_obj.database
            ]
            skills_obj.soft_skills = [
                normalization_map.get(s, s) for s in skills_obj.soft_skills
            ]
        
        # Apply normalization to project technologies
        for project in extracted_data.projects_and_technologies_involved:
            project.technologies_used = [
                normalization_map.get(t, t) for t in project.technologies_used
            ]
        
        # Update all_skills with normalized unique skills
        normalized_unique = sorted(set(normalization_map.values()))
        extracted_data.all_skills = normalized_unique
        extracted_data.num_skills = len(normalized_unique)
        
        logger.info(
            f"✓ Normalized {len(all_skill_names)} original skills -> "
            f"{len(normalized_unique)} unique canonical skills"
        )
        
        return extracted_data
    
    @staticmethod
    def add_alias(alias: str, canonical: str):
        """
        Add a new alias to the global dictionary at runtime.
        
        Args:
            alias: Alias name (will be lowercased)
            canonical: Canonical skill name
        """
        SKILL_ALIASES[alias.lower()] = canonical
        logger.info(f"Added alias: {alias} -> {canonical}")
    
    @staticmethod
    def get_all_aliases() -> Dict[str, str]:
        """Get the complete alias dictionary."""
        return SKILL_ALIASES.copy()
