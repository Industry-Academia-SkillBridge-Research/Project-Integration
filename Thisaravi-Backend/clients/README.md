# Client Libraries for External Services

Python wrapper classes for seamless integration with the two main backend services:
- **Agent-Runtime** (CV processing, skill extraction, gap analysis with XAI)
- **Advanced-Recommendation** (skill gaps, course recommendations, project analysis, GNN)

---

## 📋 Quick Start

### 1. Installation

Ensure both backend services are running:

```bash
# Terminal 1: Agent-Runtime (port 8002)
cd Agent-Runtime
uv run main.py

# Terminal 2: Advanced-Recommendation (port 8001)
cd Advanced-Recommendation-System
uv run main.py

# Terminal 3: Thisaravi-Backend (port 8010)
cd Thisaravi-Backend
uv run main.py
```

### 2. Basic Usage

```python
from clients import AgentRuntimeClient, RecommendationClient

# Initialize clients
agent = AgentRuntimeClient()
rec = RecommendationClient()

# Health check
print(agent.health())

# List available roles
roles = rec.list_roles()
print(roles)
```

---

## 🔗 Service Architecture

```
┌─────────────────────────────────────┐
│   Thisaravi-Backend (Port 8010)     │ ◄── Main API Gateway
├─────────────────────────────────────┤
│                                     │
├──► Agent-Runtime (Port 8002)        │ ◄── CV Processing, Gap Analysis, XAI
│    • POST /agent/run                │
│    • POST /agent/run-from-pdf       │
│    • GET /runtime/skill-explain     │
│    • GET /runtime/predict-explain   │
│                                     │
├──► Advanced-Recommendation (Port 8001) ◄── Skill Gaps, Courses, Projects, GNN
│    • GET /roles                     │
│    • GET /candidates/{id}/skill-gap │
│    • GET /candidates/{id}/recommend │
│    • GET /candidates/{id}/projects  │
│    • GET /candidates/{id}/gnn-skills│
│                                     │
└─────────────────────────────────────┘
```

---

## 📚 Module Reference

### AgentRuntimeClient

Wrapper for Agent-Runtime backend. Handles CV data extraction, normalization, skill gap analysis, and explainability.

#### Methods

```python
agent = AgentRuntimeClient(base_url="http://localhost:8002")

# Health check
agent.health() -> Dict[str, Any]

# Run full pipeline with CV JSON
agent.run_agent(
    cv_data: Dict,           # ExtractedData format
    role_key: str,           # e.g., "ai_ml_engineer"
    top_k: int = 25,
    include_xai: bool = True,
    ranking_method: Optional[str] = "hybrid"  # "symbolic" | "hybrid" | "additive_gnn"
) -> Dict[str, Any]

# Run pipeline from PDF/DOCX resume
agent.run_agent_from_pdf(
    pdf_path: str,           # Path to PDF or DOCX file
    role_key: str,
    top_k: int = 25,
    include_xai: bool = True,
    ranking_method: Optional[str] = None
) -> Dict[str, Any]

# Skill-level explainability
agent.skill_explain(
    candidate_id: str,
    role_key: str,
    top_n: int = 10
) -> Dict[str, Any]

# SHAP-based explainability (user-friendly)
agent.predict_explain(
    candidate_id: str,
    role_key: str,
    top_k: int = 5
) -> Dict[str, Any]
```

#### Example

```python
from clients import AgentRuntimeClient

client = AgentRuntimeClient()

# Submit CV
cv_data = {
    "candidate_id": "CAND_001",
    "candidate_name": "John Doe",
    "skills": [
        {"skill_name": "Python", "proficiency": "advanced"},
        {"skill_name": "FastAPI", "proficiency": "intermediate"},
    ],
    # ... more fields
}

response = client.run_agent(
    cv_data=cv_data,
    role_key="ai_ml_engineer",
    ranking_method="hybrid"
)

print(f"Readiness: {response['readiness_score']}")
print(f"Top gaps: {response['skill_gap_top'][:3]}")
print(f"XAI: {response['xai']}")
```

---

### RecommendationClient

Wrapper for Advanced-Recommendation backend. Handles role profiles, skill gaps, course recommendations, project analysis, and GNN-based predictions.

#### Methods

```python
rec = RecommendationClient(base_url="http://localhost:8001")

# List available roles
rec.list_roles() -> List[Dict[str, Any]]

# Get TF-IDF skill profile for a role
rec.role_skill_profile(
    role_key: str,
    top_n: int = 100
) -> Dict[str, Any]

# Get category-aggregated profile for a role
rec.role_category_profile(
    role_key: str,
    top_skills: int = 5
) -> Dict[str, Any]

# Get candidate skill confidence
rec.skill_confidence(
    candidate_id: str,
    top_n: int = 100
) -> Dict[str, Any]

# Advanced skill gap analysis (with categories)
rec.skill_gap(
    candidate_id: str,
    role_key: str,
    top_k: int = 25
) -> Dict[str, Any]

# Course recommendations
rec.recommend_courses(
    candidate_id: str,
    role_key: str,
    top_k: int = 25,
    top_n: int = 10
) -> Dict[str, Any]

# Course recommendations for custom job gap
rec.recommend_for_job_gap(
    candidate_id: str,
    deficits: List[SkillDeficit],  # or List[Dict]
    top_n: int = 10
) -> Dict[str, Any]

# Analyze project relevance to a role
rec.project_relevance(
    candidate_id: str,
    role_key: str,
    top_n: int = 5,
    top_k_role: int = 100
) -> Dict[str, Any]

# GNN-based missing skills (link prediction)
rec.missing_skills_gnn(
    candidate_id: str,
    role_key: str,
    top_k: int = 20,
    explain: Optional[str] = None  # "formula" | "feature" | "graph"
) -> Dict[str, Any]

# Clear cache (admin)
rec.clear_cache() -> Dict[str, Any]
```

#### Example

```python
from clients import RecommendationClient, SkillDeficit

client = RecommendationClient()

# Get skill gap
gap = client.skill_gap("CAND_001", "ai_ml_engineer", top_k=25)
print(f"Role: {gap['role_name']}")
print(f"Deficits: {len(gap['deficits'])}")

# Get course recommendations
courses = client.recommend_courses("CAND_001", "ai_ml_engineer")
for course in courses['recommendations'][:5]:
    print(f"{course['course_name']}: {course['gain_score']:.2f}")

# Recommend for custom job gap (no role key)
deficits = [
    SkillDeficit("Python", deficit=0.7, importance=0.9),
    SkillDeficit("TensorFlow", deficit=0.8, importance=0.8),
]
recs = client.recommend_for_job_gap("CAND_001", deficits)

# Project relevance
projects = client.project_relevance("CAND_001", "ai_ml_engineer")
print(f"Project score: {projects['candidate_project_score']:.2f}")

# GNN-based missing skills
gnn = client.missing_skills_gnn("CAND_001", "ai_ml_engineer", top_k=20)
for skill in gnn['missing_skills'][:5]:
    print(f"{skill['skill_name']}: {skill['final_score']:.4f}")
```

---

## 🧪 Integration Test

Run the end-to-end workflow validation:

```bash
cd Thisaravi-Backend/clients

# Run with default candidate and AI/ML Engineer role
python integration_test.py

# Or specify candidate and role
python integration_test.py "CAND_CUSTOM_001" "data_scientist"
```

**Output:**
```
================================================================================
  🚀 INTEGRATION TEST: Agent-Runtime + Advanced-Recommendation
================================================================================

▶ Step 1: Agent-Runtime Pipeline Execution
────────────────────────────────────────────────────────────────────────────────
✓ Pipeline executed successfully
  Readiness Score: 0.64
  Normalized Skills: 6
  Top Skill Gaps: 25
  Project Relevance Score: 0.72

  Top 5 Skill Deficits:
    1. TensorFlow: deficit=0.85, importance=0.0185
    2. PyTorch: deficit=0.80, importance=0.0171
    ...

▶ Step 2: Advanced Skill Gap Analysis
────────────────────────────────────────────────────────────────────────────────
✓ Skill gap analysis retrieved
  Target Role: AI/ML Engineer
  Total Role Jobs: 342
  Top Deficits: 25
...

✅ INTEGRATION TEST COMPLETE
```

---

## 🔄 Common Workflows

### 1. Submit CV and Get Recommendations

```python
from clients import AgentRuntimeClient, RecommendationClient

agent = AgentRuntimeClient()
rec = RecommendationClient()

# Submit CV
cv = {...}  # See sample_extracted_cv.json format
pipeline_result = agent.run_agent(cv, role_key="ai_ml_engineer")

# Get detailed recommendations
gap = rec.skill_gap(cv["candidate_id"], "ai_ml_engineer", top_k=25)
courses = rec.recommend_courses(cv["candidate_id"], "ai_ml_engineer")

# Analyze projects
projects = rec.project_relevance(cv["candidate_id"], "ai_ml_engineer")
```

### 2. Process Resume (PDF) and Recommend Courses

```python
from clients import AgentRuntimeClient, RecommendationClient

agent = AgentRuntimeClient()
rec = RecommendationClient()

# Upload PDF resume
result = agent.run_agent_from_pdf(
    "resume.pdf",
    role_key="data_scientist"
)

candidate_id = result["candidate_id"]

# Get tailored course recommendations
courses = rec.recommend_courses(
    candidate_id,
    "data_scientist",
    top_k=25,
    top_n=10
)

# Show top 5 courses
for i, course in enumerate(courses["recommendations"][:5], 1):
    print(f"{i}. {course['course_name']} (gain: {course['gain_score']:.2f})")
```

### 3. Analyze Custom Job Description (No Role Key)

```python
from clients import RecommendationClient, SkillDeficit

rec = RecommendationClient()

# Build deficits from custom job analysis
deficits = [
    SkillDeficit("Python", deficit=0.8, importance=0.95),
    SkillDeficit("AWS", deficit=0.9, importance=0.85),
    SkillDeficit("Kubernetes", deficit=0.7, importance=0.75),
]

# Get course recommendations without needing a role_key
courses = rec.recommend_for_job_gap(
    candidate_id="CAND_001",
    deficits=deficits,
    top_n=10
)
```

### 4. Get Explainability for a Skill Gap

```python
from clients import AgentRuntimeClient

agent = AgentRuntimeClient()

# Skill-level explanation (which skills contribute most to the gap)
skill_xai = agent.skill_explain(
    candidate_id="CAND_001",
    role_key="ai_ml_engineer",
    top_n=10
)

for skill in skill_xai["top_contributors"][:5]:
    print(f"{skill['skill_name']}: {skill['contribution_percent']:.1f}%")

# SHAP-based explanation (why is skill gap high/low)
shap_xai = agent.predict_explain(
    candidate_id="CAND_001",
    role_key="ai_ml_engineer"
)

if shap_xai["enabled"]:
    print(f"Skill gap prediction: {shap_xai['predicted_skill_gap_index']:.2f}")
    for factor in shap_xai["top_increasing_factors"]:
        print(f"  ➗ {factor['feature']}: {factor['message']}")
```

---

## 🛠 Configuration

### Environment Variables

```bash
# Agent-Runtime (Thisaravi-Backend/main.py)
AGENT_RUNTIME_URL=http://localhost:8002

# Advanced-Recommendation (Thisaravi-Backend/main.py)
RECOMMENDATION_API_BASE_URL=http://localhost:8001

# Neo4j (shared across all services)
NEO4J_URI=neo4j+s://...
NEO4J_USER=...
NEO4J_PASSWORD=...
```

### Default Ports

| Service | Port |
|---------|------|
| Agent-Runtime | 8002 |
| Advanced-Recommendation | 8001 |
| Thisaravi-Backend | 8010 |
| LinkedIn Scraper | 8000 |

Change in client constructors if running on different ports:

```python
agent = AgentRuntimeClient(base_url="http://custom-host:9999")
rec = RecommendationClient(base_url="http://custom-host:9998")
```

---

## 📖 API Documentation

Full Swagger/OpenAPI documentation available at:

- **Agent-Runtime**: http://localhost:8002/docs
- **Advanced-Recommendation**: http://localhost:8001/docs
- **Thisaravi-Backend**: http://localhost:8010/docs

---

## 🐛 Troubleshooting

### Service Connection Errors

```python
# Check if services are running
import requests

try:
    r = requests.get("http://localhost:8002", timeout=5)
    print("✓ Agent-Runtime is running")
except requests.ConnectionError:
    print("✗ Agent-Runtime is not reachable")
    print("  Start with: cd Agent-Runtime && uv run main.py")
```

### Timeout Errors

Increase timeout for large CV files or complex graph queries:

```python
# For PDF uploads (can take 2-3 minutes with LLM parsing)
result = agent.run_agent_from_pdf(
    "large_resume.pdf",
    role_key="ai_ml_engineer",
    # Default timeout is 180s (3 minutes)
)
```

### Missing Neo4j Data

If you get "Candidate not found" or "Role not found" errors:

1. Ensure Neo4j database is populated with test data
2. Check Neo4j connection in service startup logs
3. Verify candidate_id matches exactly (case-sensitive)
4. Use `rec.list_roles()` to see available roles

---

## 📝 Example CV Format

For `agent.run_agent()`, use this structure:

```json
{
  "candidate_id": "CAND_001",
  "candidate_name": "Jane Smith",
  "current_role": "Data Analyst",
  "total_experience_months": 36,
  "field_of_study": "Computer Science",
  "interests": ["Machine Learning", "Data Engineering"],
  "personality": "ambitious, collaborative",
  "skills": [
    {
      "skill_name": "Python",
      "proficiency": "advanced"
    },
    {
      "skill_name": "SQL",
      "proficiency": "advanced"
    }
  ],
  "work_experiences": [
    {
      "title": "Data Analyst",
      "company_name": "TechCorp",
      "duration_months": 24,
      "skills_used": ["Python", "SQL", "Tableau"]
    }
  ],
  "projects": [
    {
      "name": "Sales Dashboard",
      "description": "Interactive dashboard",
      "technologies": ["Tableau", "SQL"]
    }
  ]
}
```

---

## 📞 Support

For issues:

1. Check service logs: `tail -f logs/service.log`
2. Verify Neo4j connectivity: `GET /health` on any service
3. Check API docs at `/docs` endpoint
4. Review response status codes and error messages

---

**Last Updated:** March 5, 2026
