# Architecture: Thisaravi Backend

## 1. System Overview

The Thisaravi Backend (`port 8010`) is the central orchestration layer of the Self-Evolving Skill Gap Analyzer and Guidance System. It acts as a **Backend-for-Frontend (BFF)** that:

1. Streams LLM-generated skill gap analyses and project recommendations to the frontend
2. Orchestrates two downstream microservices (Agent-Runtime, Advanced-Recommendation-System)
3. Queries Neo4j directly for job search operations
4. Manages the self-evolving feedback loop (collection, analysis, prompt evolution, dataset regeneration)
5. Stores candidate profiles and model output logs locally

---

## 2. High-Level Service Topology

```mermaid
graph TB
    subgraph "Client Layer"
        FE["Thisaravi Frontend<br/>(React + Vite)<br/>:5173"]
    end

    subgraph "Gateway Layer"
        BE["Thisaravi Backend<br/>(FastAPI)<br/>:8010"]
    end

    subgraph "Intelligence Layer"
        AR["Agent-Runtime<br/>(FastAPI)<br/>:8002"]
        RS["Advanced-Recommendation-System<br/>(FastAPI)<br/>:8001"]
    end

    subgraph "Data Layer"
        NEO["Neo4j AuraDB<br/>(Cloud Graph Database)"]
        JSONL["Local JSONL Storage<br/>(Profiles, Feedback, Outputs)"]
    end

    subgraph "LLM Providers"
        GEM["Google Gemini API<br/>(gemini-3-flash-preview)"]
        OLL["Ollama<br/>(Gemma 3 4B Fine-tuned)"]
    end

    subgraph "ML Models"
        GNN["GNN Model<br/>(GraphSAGE, PyTorch Geometric)"]
        XGB["XGBoost Surrogate<br/>(SHAP Explainability)"]
        SKL["sklearn Pipeline<br/>(Skill Gap Prediction)"]
        QWN["Qwen 2.5 3B<br/>(AI Explainer, LoRA)"]
    end

    subgraph "External Services"
        HF["HuggingFace Hub<br/>(Dataset Upload)"]
    end

    FE -->|"HTTP / SSE<br/>Streaming + REST"| BE
    BE -->|"REST<br/>CV Pipeline, XAI"| AR
    BE -->|"REST<br/>Skill Gap, Courses, GNN"| RS
    BE -->|"Bolt (neo4j+s)<br/>Job Queries"| NEO
    BE -->|"Read/Write"| JSONL
    BE -->|"Streaming API"| GEM
    BE -->|"Streaming API"| OLL
    BE -->|"API Upload"| HF

    AR -->|"Bolt<br/>Graph Write/Read"| NEO
    AR -->|"REST<br/>Skill Gap Data"| RS
    AR -.->|"Inference"| SKL
    AR -.->|"Inference"| QWN

    RS -->|"Bolt<br/>Graph Read"| NEO
    RS -.->|"Inference"| GNN
    RS -.->|"Inference"| XGB

    style BE fill:#4a90d9,stroke:#2c5282,color:#fff
    style AR fill:#48bb78,stroke:#276749,color:#fff
    style RS fill:#ed8936,stroke:#c05621,color:#fff
    style FE fill:#9f7aea,stroke:#6b46c1,color:#fff
    style NEO fill:#e53e3e,stroke:#9b2c2c,color:#fff
```

---

## 3. Thisaravi Backend Internal Architecture

```mermaid
graph TB
    subgraph "Thisaravi Backend (:8010)"
        direction TB

        subgraph "API Layer (main.py)"
            GEN["/generate-project<br/>POST - Streaming LLM"]
            SRC["/generate-project-from-sources<br/>POST - Multi-service orchestration"]
            ROLES["/roles<br/>GET - Role listing"]
            JOBS["/jobs-by-role, /search-jobs<br/>GET - Neo4j job search"]
            FB_API["/submit-feedback, /all-feedback<br/>/unreviewed-outputs, /my-outputs<br/>Feedback endpoints"]
            EVO_API["/run-analysis, /preview-evolution<br/>/apply-evolution, /prompt-evolutions<br/>Evolution endpoints"]
            DS_API["/run-regeneration<br/>/list-datasets, /upload-to-hf<br/>Dataset endpoints"]
            PROF_API["/profiles CRUD<br/>/profiles/:id/sync-from-runtime<br/>Profile endpoints"]
        end

        subgraph "Client Layer (clients/)"
            ARC["AgentRuntimeClient<br/>HTTP → :8002"]
            REC["RecommendationClient<br/>HTTP → :8001"]
        end

        subgraph "Feedback System (feedback/)"
            SCH["schemas.py<br/>Pydantic Models"]
            STO["storage.py<br/>JSONL Read/Write"]
            ANA["analysis.py<br/>Stats + LLM Patterns"]
            PEV["prompt_evolver.py<br/>Meta-prompting"]
            PIP["pipeline.py<br/>Orchestration"]
        end

        subgraph "Profile Store (profiles/)"
            PSTO["storage.py<br/>JSONL CRUD"]
        end

        subgraph "Dataset Pipeline (datasets/)"
            SEED["seeds.jsonl / real_seeds.jsonl"]
            SGEN["generate_seeds.py"]
            SMART["smart_generator.py<br/>Domain-expert logic"]
            AUG["augment_dataset.py<br/>Teacher model generation"]
            HFUP["hf_uploader.py<br/>HuggingFace upload"]
        end

        subgraph "LLM Integration"
            GPROV["Gemini Provider<br/>google.genai streaming"]
            OPROV["Ollama Provider<br/>ollama.chat streaming"]
            LOG["logging_wrapper<br/>Output capture + seed extraction"]
        end

        subgraph "Neo4j Direct"
            NQ["_neo4j_query()<br/>Lazy singleton driver"]
        end
    end

    GEN --> GPROV
    GEN --> OPROV
    GPROV --> LOG
    OPROV --> LOG
    LOG --> STO

    SRC --> ARC
    SRC --> REC
    ROLES --> REC

    JOBS --> NQ

    FB_API --> STO
    EVO_API --> PIP
    PIP --> ANA
    PIP --> PEV
    PIP --> AUG
    DS_API --> AUG
    DS_API --> HFUP

    PROF_API --> PSTO
    PROF_API --> ARC

    AUG --> SMART

    style GEN fill:#4a90d9,stroke:#2c5282,color:#fff
    style SRC fill:#4a90d9,stroke:#2c5282,color:#fff
```

---

## 4. Request Flows

### 4.1 Manual Analysis (LLM Streaming)

This is the primary flow when a student enters their profile and a target job manually.

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant BE as Backend (:8010)
    participant LLM as Gemini / Ollama
    participant ST as JSONL Storage

    FE->>BE: POST /generate-project<br/>{student_data, job_data, model_provider}
    BE->>BE: Select provider (Gemini or Ollama)
    BE->>BE: Construct prompt (SYSTEM_PROMPT + user data)

    rect rgb(230, 245, 255)
        Note over BE,LLM: Streaming via Thread + asyncio.Queue
        BE->>LLM: generate_content_stream() / chat(stream=True)
        loop Each chunk
            LLM-->>BE: text chunk
            BE-->>FE: StreamingResponse chunk (text/plain)
            FE->>FE: Append to markdown renderer
        end
    end

    BE->>ST: log_model_output(full_text)
    BE->>BE: Background: extract_real_seeds()

    FE->>FE: parseResponse(fullText)<br/>Extract JSON or structured text
    FE->>FE: Render ResultsDashboard<br/>(match %, missing skills, project card)
```

**Streaming implementation detail**: Both Gemini and Ollama use synchronous streaming APIs. The backend bridges these to async via a background `threading.Thread` that pushes chunks onto an `asyncio.Queue`. An async generator awaits the queue and yields chunks to FastAPI's `StreamingResponse`.

### 4.2 Source-Based Analysis (Multi-Service Orchestration)

This flow pulls real candidate and job data from companion services instead of manual input.

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant BE as Backend (:8010)
    participant AR as Agent-Runtime (:8002)
    participant RS as Recommendation (:8001)

    FE->>BE: POST /generate-project-from-sources<br/>{candidate_id, role_key, job_id}

    par Parallel service calls
        BE->>AR: GET /runtime/skill-explain<br/>?candidate_id=...&role_key=...
        AR-->>BE: Skill-level contributions

        BE->>RS: GET /candidates/{id}/roles/{role}/skill-gap-advanced
        RS-->>BE: Deficit list (skill, importance, gap, match_strength)

        BE->>RS: GET /candidates/{id}/roles/{role}/recommendations
        RS-->>BE: Course recommendations (greedy set cover)

        BE->>RS: GET /candidates/{id}/roles/{role}/project-relevance
        RS-->>BE: Project alignment scores

        BE->>RS: GET /candidates/{id}/roles/{role}/missing-skills-gnn
        RS-->>BE: GNN-ranked missing skills (optional)
    end

    BE->>BE: Aggregate results<br/>(tolerate partial failures)
    BE-->>FE: JSONResponse {skill_gap, recommendations,<br/>project_relevance, missing_skills_gnn}
```

**Error tolerance**: Each downstream call is independently wrapped in try/catch. If a service fails (e.g., GNN model not loaded), the response includes an `_error` key for that section while returning successful results from other services.

### 4.3 Self-Evolution Feedback Loop

```mermaid
sequenceDiagram
    participant EX as Expert (Frontend)
    participant BE as Backend (:8010)
    participant ST as JSONL Storage
    participant LLM as Gemini / Ollama

    Note over EX,LLM: Phase 1: Feedback Collection
    EX->>BE: GET /unreviewed-outputs
    BE->>ST: Load outputs without feedback
    ST-->>BE: Unreviewed output list
    BE-->>EX: Output list for review
    EX->>BE: POST /submit-feedback<br/>{ratings: {5 dims}, comments, output_ref}
    BE->>ST: Append to expert_feedback.jsonl

    Note over EX,LLM: Phase 2: Pattern Analysis (manual trigger)
    EX->>BE: POST /run-analysis {provider}
    BE->>ST: Load all feedback for current prompt version
    BE->>BE: Compute rating statistics (mean, std, classify)
    BE->>LLM: Theme extraction meta-prompt<br/>(stats + all comments)
    LLM-->>BE: {criticisms, praises, recommendations}
    BE->>ST: Save PatternReport
    BE-->>EX: Analysis results

    Note over EX,LLM: Phase 3: Prompt Evolution (manual trigger)
    EX->>BE: POST /preview-evolution {report_id}
    BE->>LLM: "You are an expert Prompt Engineer..."<br/>(current prompt + feedback patterns)
    LLM-->>BE: Evolved prompt text
    BE-->>EX: Diff preview
    EX->>BE: POST /apply-evolution {report_id}
    BE->>ST: Save PromptEvolution record
    BE-->>EX: Evolution applied

    Note over EX,LLM: Phase 4: Dataset Regeneration
    EX->>BE: POST /run-regeneration<br/>{evolution_id, target_count, provider}
    BE->>BE: Load evolved prompt
    BE->>LLM: Generate target_count samples<br/>using evolved system prompt
    BE->>ST: Save new .jsonl dataset
    BE-->>EX: {output_path}

    Note over EX,LLM: Phase 5: Upload and Re-Fine-Tune
    EX->>BE: POST /upload-to-hf {filename}
    BE->>BE: Upload dataset to HuggingFace Hub
    BE-->>EX: Upload confirmation
    Note right of EX: Manual: LoRA fine-tune on Colab<br/>→ GGUF → Register with Ollama
```

---

## 5. Downstream Service Architecture

### 5.1 Agent-Runtime Pipeline

```mermaid
graph LR
    subgraph "Agent-Runtime (:8002)"
        direction LR
        A1["1. Extractor Agent<br/>Validate CV JSON"]
        A2["2. Normalizer Agent<br/>Canonical skill names<br/>(alias dict + LLM)"]
        A3["3. KG Writer Tool<br/>MERGE nodes/edges<br/>to Neo4j"]
        A4["4. Gap Analyzer Tool<br/>Call Recommendation<br/>API (:8001)"]

        A1 --> A2 --> A3 --> A4
    end

    PDF["CV PDF/DOCX"] -->|"OCR + LLM Parse"| A1
    JSON["CV JSON"] --> A1
    A3 -->|"MERGE Person, Skill,<br/>Project, WorkExp,<br/>Cert, Education"| NEO["Neo4j"]
    A4 -->|"GET skill-gap-advanced"| RS["Recommendation<br/>System (:8001)"]

    subgraph "XAI Layer"
        XAI1["Skill-Level Explain<br/>(contribution %)"]
        XAI2["SHAP Explain<br/>(sklearn pipeline)"]
        XAI3["AI Explain<br/>(Qwen 2.5 3B LoRA)"]
    end

    A4 --> XAI1
    A4 --> XAI2
    XAI2 -.-> XAI3
```

**Graph schema written by KG Writer:**

```mermaid
graph LR
    P((Person)) -->|HAS_SKILL| S((Skill))
    P -->|WORKED_AT| WE((WorkExperience))
    P -->|WORKED_ON| PR((Project))
    P -->|HAS_CERTIFICATION| C((Certification))
    P -->|STUDIED_AT| E((Education))
    WE -->|USED_SKILL| S
    PR -->|USES_TECHNOLOGY| S

    style P fill:#4a90d9,stroke:#2c5282,color:#fff
    style S fill:#48bb78,stroke:#276749,color:#fff
    style WE fill:#ed8936,stroke:#c05621,color:#fff
    style PR fill:#9f7aea,stroke:#6b46c1,color:#fff
```

### 5.2 Advanced-Recommendation-System Computation Pipeline

```mermaid
graph TB
    subgraph "Input"
        CID["candidate_id"]
        RK["role_key"]
    end

    subgraph "Step 1: Skill Confidence (P_has)"
        SC["Evidence-Weighted<br/>Confidence"]
        SC1["HAS_SKILL (CV): 0.70"]
        SC2["USED_SKILL (Work): 0.90"]
        SC3["USES_TECHNOLOGY (Project): 0.80"]
        SC4["CERTIFICATION: 0.60"]
        SC1 --> SC
        SC2 --> SC
        SC3 --> SC
        SC4 --> SC
    end

    subgraph "Step 2: Role Importance"
        RI["TF-IDF<br/>importance(role, skill)"]
    end

    subgraph "Step 3: Graded Matching"
        GM["Match Strength"]
        GM1["1.0 - Exact name"]
        GM2["0.7 - Cluster match"]
        GM3["0.6 - SIMILAR_TO ≥ 0.80"]
        GM4["0.4 - SIMILAR_TO ≥ 0.68"]
        GM1 --> GM
        GM2 --> GM
        GM3 --> GM
        GM4 --> GM
    end

    subgraph "Step 4: Deficit Ranking"
        DEF["deficit = importance × (1 - match_strength)"]
    end

    subgraph "Step 5: GNN Prediction"
        GNNP["P_gnn = sigmoid(person_embed · skill_embed)<br/>GraphSAGE, 2-layer, 128-dim"]
    end

    subgraph "Step 6: Hybrid Ranking"
        HYB["final_score = gap × importance_norm × P_gnn"]
    end

    subgraph "Outputs"
        OUT1["Ranked Missing Skills"]
        OUT2["Course Recommendations<br/>(greedy set cover)"]
        OUT3["Project Relevance Scores"]
        OUT4["SHAP Explanations<br/>(3 levels)"]
    end

    CID --> SC
    CID --> GM
    RK --> RI
    SC --> DEF
    RI --> DEF
    GM --> DEF
    DEF --> HYB
    GNNP --> HYB
    HYB --> OUT1
    DEF --> OUT2
    CID --> OUT3
    RK --> OUT3
    HYB --> OUT4

    style HYB fill:#e53e3e,stroke:#9b2c2c,color:#fff
    style GNNP fill:#4a90d9,stroke:#2c5282,color:#fff
    style DEF fill:#ed8936,stroke:#c05621,color:#fff
```

**Formula reference:**

| Formula | Description |
|---------|-------------|
| `P_has(skill) = 1 - Π(1 - w_i)` | Probability candidate has skill, across all evidence instances |
| `importance(role, skill) = TF × IDF` | How important a skill is for a role, based on job postings |
| `deficit(skill) = importance × (1 - match_strength)` | How much this skill gap matters |
| `P_gnn = σ(z_person · z_skill)` | GNN link prediction: learnability score |
| `final_score = gap × importance_norm × P_gnn` | Hybrid multiplicative ranking |
| `course_gain = Σ(deficit) + rating_boost - difficulty_penalty` | Course selection criterion |

---

## 6. Data Flow: End-to-End

```mermaid
graph TB
    subgraph "Data Sources"
        LI["LinkedIn<br/>(Scraped Jobs)"]
        CV["Candidate CVs<br/>(PDF/DOCX/JSON)"]
        EXP["Expert Reviewers"]
    end

    subgraph "Ingestion"
        SCR["LinkedIn Scraper<br/>(:8000)"]
        ARP["Agent-Runtime<br/>CV Pipeline"]
    end

    subgraph "Knowledge Graph (Neo4j)"
        JN["Job Nodes<br/>(title, skills, company)"]
        RN["Role Nodes<br/>(role_key, name)"]
        SN["Skill Nodes<br/>(name, category, embeddings)"]
        PN["Person Nodes<br/>(demographics, skills, projects)"]
        CN["Course Nodes<br/>(title, skills_taught, rating)"]
    end

    subgraph "Analysis Engine"
        RS2["Recommendation System<br/>TF-IDF + Deficit + GNN"]
    end

    subgraph "Generation"
        BE2["Thisaravi Backend"]
        LLM2["LLM Providers<br/>(Gemini / Ollama)"]
    end

    subgraph "Feedback Loop"
        FBC["Expert Feedback<br/>(5 dimensions + text)"]
        PAT["Pattern Analysis<br/>(Stats + LLM themes)"]
        EVO["Prompt Evolution<br/>(Meta-prompting)"]
        REG["Dataset Regeneration"]
        FT["Model Fine-Tuning<br/>(LoRA on Colab)"]
    end

    LI --> SCR --> JN
    CV --> ARP --> PN
    ARP --> SN

    JN --> RN
    RN --> RS2
    SN --> RS2
    PN --> RS2
    CN --> RS2

    RS2 -->|"Skill gaps, courses,<br/>project relevance"| BE2
    BE2 -->|"System prompt +<br/>candidate + job"| LLM2
    LLM2 -->|"Streaming output"| BE2

    EXP --> FBC
    FBC --> PAT
    PAT --> EVO
    EVO --> REG
    REG --> FT
    FT -->|"Updated model"| LLM2

    style FBC fill:#48bb78,stroke:#276749,color:#fff
    style PAT fill:#ed8936,stroke:#c05621,color:#fff
    style EVO fill:#e53e3e,stroke:#9b2c2c,color:#fff
    style FT fill:#4a90d9,stroke:#2c5282,color:#fff
```

---

## 7. Technology Stack Summary

```mermaid
graph LR
    subgraph "Frontend"
        R["React 19"] --- TS["TypeScript"]
        R --- V["Vite"]
        R --- TW["Tailwind CSS"]
        R --- SH["shadcn/ui"]
        R --- RQ["TanStack Query"]
    end

    subgraph "Backend Gateway"
        FA1["FastAPI"] --- PY1["Python 3.12+"]
        FA1 --- PD1["Pydantic v2"]
        FA1 --- OL["ollama (Python)"]
        FA1 --- GN["google-genai"]
        FA1 --- N4J1["neo4j (driver)"]
    end

    subgraph "Agent-Runtime"
        FA2["FastAPI"] --- PY2["Python 3.12+"]
        FA2 --- OCR["EasyOCR"]
        FA2 --- PDF["PyPDF2 + pdfplumber"]
        FA2 --- SHAP1["SHAP"]
        FA2 --- TF["Transformers + PEFT"]
    end

    subgraph "Recommendation Engine"
        FA3["FastAPI"] --- PY3["Python 3.12+"]
        FA3 --- PTG["PyTorch Geometric"]
        FA3 --- PT["PyTorch"]
        FA3 --- XG["XGBoost"]
        FA3 --- SHAP2["SHAP"]
        FA3 --- N4J2["neo4j (driver)"]
    end

    subgraph "Infrastructure"
        NEO2["Neo4j AuraDB"]
        OLL2["Ollama (local GPU)"]
        GEM2["Gemini API (cloud)"]
        HF2["HuggingFace Hub"]
        COL["Google Colab (fine-tuning)"]
    end
```

---

## 8. Communication Patterns

| From | To | Protocol | Pattern | Purpose |
|------|----|----------|---------|---------|
| Frontend | Backend | HTTP | Streaming (text/plain) | LLM generation with live rendering |
| Frontend | Backend | HTTP | REST (JSON) | Feedback, profiles, jobs, evolution |
| Backend | Agent-Runtime | HTTP | REST (JSON) | CV pipeline, XAI, profile sync |
| Backend | Recommendation | HTTP | REST (JSON) | Skill gap, courses, GNN ranking |
| Backend | Neo4j | Bolt (neo4j+s) | Cypher queries | Job search and lookup |
| Backend | Gemini | HTTPS | Streaming API | Cloud LLM generation |
| Backend | Ollama | HTTP | Streaming API | Local LLM generation |
| Backend | HuggingFace | HTTPS | REST API | Dataset upload |
| Agent-Runtime | Neo4j | Bolt | Cypher MERGE/CREATE | Graph writing |
| Agent-Runtime | Recommendation | HTTP | REST (JSON) | Gap analysis data |
| Recommendation | Neo4j | Bolt | Cypher READ | Graph traversal, TF-IDF, matching |

---

## 9. Neo4j Knowledge Graph Schema

```mermaid
erDiagram
    Person ||--o{ HAS_SKILL : has
    Person ||--o{ WORKED_AT : "worked at"
    Person ||--o{ WORKED_ON : "worked on"
    Person ||--o{ HAS_CERTIFICATION : holds
    Person ||--o{ STUDIED_AT : "studied at"
    Person ||--o{ TARGETS_ROLE : targets

    WorkExperience ||--o{ USED_SKILL : used
    Project ||--o{ USES_TECHNOLOGY : uses

    Role ||--o{ Job : groups
    Job ||--o{ REQUIRES_SKILL : requires

    Skill ||--o{ SIMILAR_TO : "similar to"
    Skill ||--o{ BELONGS_TO_CATEGORY : "belongs to"
    Course ||--o{ TEACHES_SKILL : teaches

    Person {
        string candidate_id PK
        string name
        string email
        string current_role
        string target_role
        int experience_months
        int num_skills
        int num_projects
    }

    Skill {
        string name PK
        string category
        string cluster_id
    }

    Role {
        string role_key PK
        string name
    }

    Job {
        string job_id PK
        string title
        string company_name
        string location
        string role_key FK
        string description
    }

    Course {
        string course_id PK
        string title
        float avg_rating
        string difficulty
    }

    WorkExperience {
        string role
        string company
        int duration_months
    }

    Project {
        string name
        string description
        string complexity
    }

    SkillCategory {
        string category_id PK
        string name
    }
```

---

## 10. Deployment Topology

```
┌─────────────────────────────────────────────────────────────────┐
│  Development Machine                                             │
│                                                                  │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│   │  Frontend     │  │  Backend     │  │  Agent-Runtime       │  │
│   │  :5173        │  │  :8010       │  │  :8002               │  │
│   │  (Vite dev)   │  │  (uvicorn)   │  │  (uvicorn)           │  │
│   └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│          │                 │                      │              │
│          │   ┌─────────────┴──────────────┐       │              │
│          │   │  Recommendation System     │       │              │
│          │   │  :8001 (uvicorn)           │       │              │
│          │   └─────────────┬──────────────┘       │              │
│          │                 │                      │              │
│   ┌──────┴─────────────────┴──────────────────────┴───────────┐  │
│   │  Ollama (:11434)   │  Neo4j AuraDB (Cloud)                │  │
│   │  - Gemma 3 4B FT   │  - Candidates, Skills, Roles, Jobs  │  │
│   │  - Gemma 3 1B      │  - Courses, Projects, Categories    │  │
│   │  - Qwen 2.5 3B     │                                     │  │
│   └─────────────────────┴─────────────────────────────────────┘  │
│                                                                  │
│   External APIs: Gemini (cloud), HuggingFace Hub, Open Router   │
└─────────────────────────────────────────────────────────────────┘
```

All services currently run on a single development machine. For production deployment, the recommended split would be:

| Tier | Services | Notes |
|------|----------|-------|
| **Edge** | Frontend (static build) | CDN or Nginx |
| **Application** | Backend, Agent-Runtime | Stateless, horizontally scalable |
| **Compute** | Recommendation System, Ollama | GPU-capable node for GNN + LLM inference |
| **Data** | Neo4j AuraDB | Managed cloud service |

---

## 11. Security Considerations (Current State)

| Area | Status | Notes |
|------|--------|-------|
| Authentication | localStorage-based | No real auth; frontend stores user data in localStorage |
| Authorization | Role-based (student/expert) | Frontend-enforced only |
| CORS | Restricted to localhost origins | `localhost:5173` and `localhost:8080` |
| Input validation | Pydantic models | All request bodies validated, but no rate limiting |
| Secrets | `.env` files | Not committed to git (in `.gitignore`) |
| Inter-service auth | None | All services trust each other on localhost |
| Neo4j | Cloud with credentials | Connection string and password in environment variables |
