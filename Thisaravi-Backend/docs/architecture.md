# System Architecture

> Self-Evolving Skill Gap Analyzer and Guidance System

This document describes the architecture of the backend and its connections to the frontend, Agent-Runtime, and Advanced-Recommendation-System. All diagrams use Mermaid syntax.

## Table of Contents

- [High-Level System Overview](#high-level-system-overview)
- [Service Communication Architecture](#service-communication-architecture)
- [Backend Internal Architecture](#backend-internal-architecture)
- [Request Flow: Skill Gap Analysis](#request-flow-skill-gap-analysis)
- [Self-Evolving Feedback Loop](#self-evolving-feedback-loop)
- [Training Data Pipeline](#training-data-pipeline)
- [Frontend Architecture](#frontend-architecture)
- [Data Model](#data-model)
- [Knowledge Graph Schema](#knowledge-graph-schema)
- [Recommendation Engine Internals](#recommendation-engine-internals)
- [Agent-Runtime Pipeline](#agent-runtime-pipeline)
- [Deployment Architecture](#deployment-architecture)

---

## High-Level System Overview

The system follows a microservice architecture with the backend acting as the central API gateway. The frontend communicates exclusively with the backend, which orchestrates calls to specialized services.

```mermaid
graph TB
    subgraph "User Layer"
        S["Student (Browser)"]
        E["Expert (Browser)"]
    end

    subgraph "Frontend — React 19 + Vite (Port 5173)"
        UI["React Application"]
        UI --- AP["Analysis Pages<br/>Manual / Source Mode"]
        UI --- FP["Feedback Pages<br/>Review + Rate Outputs"]
        UI --- EP["Evolution Dashboard<br/>4-Phase Pipeline"]
    end

    subgraph "Backend — FastAPI (Port 8185)"
        GW["API Gateway<br/>main.py"]
        FB["Feedback Module<br/>feedback/"]
        DS["Dataset Pipeline<br/>datasets/"]
        PR["Profile Store<br/>profiles/"]
        CL["Service Clients<br/>clients/"]
    end

    subgraph "Agent-Runtime — FastAPI (Port 8002)"
        AG["Agentic Pipeline"]
        AG --- EX["Extractor Agent"]
        AG --- NM["Normalizer Agent"]
        AG --- KG["KG Writer Tool"]
        AG --- GA["Gap Analyzer Tool"]
        CVP["CV Parser Service"]
        XAI_AR["XAI Service<br/>SHAP + Skill Explain"]
    end

    subgraph "Advanced-Recommendation — FastAPI (Port 8001)"
        RC["Recommendation Core"]
        RC --- TF["TF-IDF Importance"]
        RC --- DF["Deficit Service"]
        RC --- CR["Course Recommender"]
        RC --- GNN["GNN Inference<br/>HeteroGNN SAGEConv"]
        RC --- SHP["SHAP Explainer"]
    end

    subgraph "External Services"
        NEO[("Neo4j Aura<br/>Knowledge Graph")]
        HF["HuggingFace Hub<br/>Datasets + Models"]
        OL["Ollama<br/>Fine-tuned Gemma 3 4B"]
        GM["Google Gemini API"]
        COLAB["Google Colab<br/>L4 GPU Training"]
    end

    S --> UI
    E --> UI
    UI -->|"HTTP via Vite proxy /api"| GW

    GW --> CL
    CL -->|"HTTP :8002"| AG
    CL -->|"HTTP :8001"| RC
    GW -->|"Cypher"| NEO
    GW -->|"Streaming"| OL
    GW -->|"Streaming"| GM
    DS -->|"Upload JSONL"| HF
    COLAB -->|"Pull dataset"| HF
    COLAB -->|"Push GGUF"| HF
    OL -->|"Load GGUF"| HF

    AG -->|"Write nodes"| NEO
    RC -->|"Read graph"| NEO
    GA -->|"HTTP :8001"| RC

    style GW fill:#4a90d9,color:#fff
    style UI fill:#5cb85c,color:#fff
    style AG fill:#f0ad4e,color:#fff
    style RC fill:#d9534f,color:#fff
    style NEO fill:#68217a,color:#fff
```

---

## Service Communication Architecture

Detailed view of inter-service HTTP communication with specific endpoints.

```mermaid
flowchart LR
    subgraph Frontend["Frontend :5173"]
        direction TB
        FE_AN["analysisService.ts"]
        FE_FB["feedbackService.ts"]
        FE_EV["evolutionService.ts"]
        FE_PR["profileService.ts"]
    end

    subgraph Backend["Backend :8185"]
        direction TB
        B_GEN["/generate-project<br/>/generate-project-from-sources"]
        B_FB["/submit-feedback<br/>/unreviewed-outputs<br/>/all-feedback"]
        B_EV["/run-analysis<br/>/preview-evolution<br/>/apply-evolution<br/>/run-regeneration"]
        B_PR["/profiles CRUD"]
        B_JOB["/jobs-by-role<br/>/search-jobs"]
    end

    subgraph AgentRT["Agent-Runtime :8002"]
        direction TB
        AR_RUN["/agent/run<br/>/agent/run-from-pdf"]
        AR_XAI["/runtime/skill-explain<br/>/runtime/predict-explain"]
        AR_CAND["/candidates/{id}"]
    end

    subgraph AdvRec["Recommendation :8001"]
        direction TB
        REC_ROLE["/roles<br/>/roles/{key}/skill-profile"]
        REC_GAP["/candidates/{id}/roles/{role}/skill-gap-advanced"]
        REC_COURSE["/candidates/{id}/roles/{role}/recommendations"]
        REC_PROJ["/candidates/{id}/roles/{role}/project-relevance"]
        REC_GNN["/candidates/{id}/roles/{role}/missing-skills-gnn"]
    end

    FE_AN -->|"POST /api/generate-project"| B_GEN
    FE_AN -->|"POST /api/generate-project-from-sources"| B_GEN
    FE_FB -->|"POST /api/submit-feedback"| B_FB
    FE_EV -->|"POST /api/run-analysis"| B_EV
    FE_PR -->|"GET/POST /api/profiles"| B_PR

    B_GEN -->|"AgentRuntimeClient"| AR_RUN
    B_GEN -->|"AgentRuntimeClient"| AR_XAI
    B_GEN -->|"RecommendationClient"| REC_GAP
    B_GEN -->|"RecommendationClient"| REC_COURSE
    B_GEN -->|"RecommendationClient"| REC_PROJ
    B_GEN -->|"RecommendationClient"| REC_GNN
    B_PR -->|"Sync profile"| AR_CAND
    B_GEN -->|"RecommendationClient"| REC_ROLE
```

---

## Backend Internal Architecture

The backend's internal module structure and data flow.

```mermaid
graph TB
    subgraph "main.py — API Gateway"
        REQ["Incoming Request"]
        ROUTE["Route Handler"]
        STREAM["Streaming Response Builder"]
        LOG["Output Logger<br/>(logging_wrapper)"]
        MAP["Data Mappers<br/>linkedin_job_to_job_data<br/>candidate_profile_to_student_data"]
    end

    subgraph "clients/"
        ARC["AgentRuntimeClient<br/>→ localhost:8002"]
        RECC["RecommendationClient<br/>→ localhost:8001"]
    end

    subgraph "feedback/"
        SCH["schemas.py<br/>FeedbackEntry, PatternReport<br/>PromptEvolution"]
        STO["storage.py<br/>JSONL Persistence<br/>Prompt Version Tracking"]
        ANA["analysis.py<br/>Statistical Analysis<br/>+ LLM Theme Extraction"]
        EVO["prompt_evolver.py<br/>Meta-Prompting<br/>Prompt Engineering"]
        PIP["pipeline.py<br/>Orchestration"]
    end

    subgraph "datasets/"
        SEED["generate_seeds.py<br/>50+ Role Archetypes"]
        RSEED["extract_real_seeds.py<br/>SHA-256 Dedup"]
        SMART["smart_generator.py<br/>Domain Expert Engine"]
        AUG["augment_dataset.py<br/>Teacher Model Generation"]
        HFU["hf_uploader.py<br/>→ HuggingFace Hub"]
    end

    subgraph "profiles/"
        PSTO["storage.py<br/>JSONL CRUD"]
    end

    subgraph "LLM Providers"
        GEM["Gemini API<br/>gemini-3-flash-preview"]
        OLF["Ollama Fine-tuned<br/>student-advisor"]
        OLG["Ollama Generic<br/>gemma3:1b"]
    end

    subgraph "Storage (JSONL Files)"
        F_FB[("feedback_data/<br/>expert_feedback.jsonl<br/>model_outputs_log.jsonl")]
        F_PR[("profile_data/<br/>candidate_profiles.jsonl")]
        F_DS[("datasets/<br/>*.jsonl training files")]
        F_EV[("feedback_data/<br/>pattern_reports.jsonl<br/>prompt_evolutions.jsonl")]
    end

    REQ --> ROUTE
    ROUTE --> MAP
    MAP --> ARC
    MAP --> RECC
    ROUTE --> STREAM
    STREAM --> GEM & OLF & OLG
    STREAM --> LOG
    LOG --> F_FB

    ROUTE --> PIP
    PIP --> ANA --> STO
    PIP --> EVO --> STO
    PIP --> AUG --> HFU
    ANA --> F_EV
    STO --> F_FB

    ROUTE --> PSTO --> F_PR

    SEED --> F_DS
    RSEED --> F_DS
    SMART --> AUG
    AUG --> F_DS

    style REQ fill:#4a90d9,color:#fff
    style PIP fill:#f0ad4e,color:#000
    style AUG fill:#5cb85c,color:#fff
```

---

## Request Flow: Skill Gap Analysis

Sequence diagram showing the complete flow for the orchestrated `/generate-project-from-sources` endpoint.

```mermaid
sequenceDiagram
    participant U as Student (Browser)
    participant FE as Frontend
    participant BE as Backend :8185
    participant AR as Agent-Runtime :8002
    participant RS as Recommendation :8001
    participant N4 as Neo4j Aura
    participant LLM as Gemini / Ollama

    U->>FE: Submit analysis request<br/>(job_id, candidate_id, role_key)
    FE->>BE: POST /generate-project-from-sources

    Note over BE: Resolve input data

    alt Has candidate_id
        BE->>AR: GET /candidates/{id}
        AR-->>BE: Candidate profile (skills, experience)
    end

    alt Has job_id
        BE->>N4: MATCH (j:Job {job_id}) RETURN j
        N4-->>BE: Job details (title, skills, description)
    end

    alt Has role_key
        BE->>RS: GET /roles/{role_key}/skill-profile
        RS-->>BE: TF-IDF skill importance profile
    end

    Note over BE: Map data formats<br/>(candidate → StudentData, job → JobData)

    par Parallel API calls to Recommendation System
        BE->>RS: GET /candidates/{id}/roles/{role}/skill-gap-advanced
        RS->>N4: Query skill confidence + role importance
        RS-->>BE: Graded skill gaps with deficit ranking

        BE->>RS: GET /candidates/{id}/roles/{role}/recommendations
        RS->>N4: Query courses covering deficit skills
        RS-->>BE: Ranked course recommendations

        BE->>RS: GET /candidates/{id}/roles/{role}/project-relevance
        RS->>N4: Match project skills to role skills
        RS-->>BE: Project relevance scores

        BE->>RS: GET /candidates/{id}/roles/{role}/missing-skills-gnn
        RS->>N4: Load graph + GNN inference
        RS-->>BE: GNN-ranked missing skills
    end

    Note over BE: Aggregate all results

    BE-->>FE: Combined JSON response<br/>(gaps + courses + projects + GNN)
    FE-->>U: Render ResultsDashboard<br/>(SkillMatchScore + missing skills + ProjectCard)
```

---

## Self-Evolving Feedback Loop

The 4-phase continuous improvement cycle that distinguishes this system.

```mermaid
flowchart TB
    subgraph "Phase 1: Feedback Collection"
        GEN["Model generates<br/>skill gap analysis"]
        LOG["Output logged to<br/>model_outputs_log.jsonl"]
        REV["Expert reviews output"]
        RATE["Rates on 5 dimensions (1-5):<br/>• Skill Gap Accuracy<br/>• Project Relevance<br/>• Tech Stack Appropriateness<br/>• Implementation Step Quality<br/>• Overall Quality"]
        COMM["Adds free-text comments"]
        STORE["Stored in<br/>expert_feedback.jsonl"]

        GEN --> LOG --> REV --> RATE --> COMM --> STORE
    end

    subgraph "Phase 2: Pattern Analysis"
        STAT["Statistical Analysis<br/>per-dimension mean/median/stddev"]
        CLASS["Classify dimensions<br/>WEAK / NEUTRAL / STRONG"]
        LLM_T["LLM Theme Extraction<br/>from expert comments"]
        REPORT["PatternReport<br/>criticisms + praises +<br/>actionable insights"]

        STORE --> STAT --> CLASS --> REPORT
        STORE --> LLM_T --> REPORT
    end

    subgraph "Phase 3: Prompt Evolution"
        META["LLM as Prompt Engineer<br/>receives current prompt +<br/>PatternReport"]
        RULES["Rules:<br/>• Preserve JSON schema<br/>• Add measurable instructions<br/>• Address each criticism<br/>• ≤ 800 words"]
        DIFF["Generate unified diff<br/>for human review"]
        VER["Version tracking<br/>v2_base → v2_evolved_N"]

        REPORT --> META --> RULES --> DIFF --> VER
    end

    subgraph "Phase 4: Dataset Regeneration & Re-Training"
        REGEN["augment_dataset.py<br/>with evolved prompt"]
        TEACH["Teacher model (Gemini)<br/>generates 200 examples"]
        HF["Upload to HuggingFace<br/>Hashinika/student-advisor-dataset"]
        FT["Fine-tune on Colab<br/>Gemma 3 4B + LoRA"]
        GGUF["Export Q4_K_M GGUF"]
        DEPLOY["Deploy to Ollama<br/>student-advisor model"]

        VER --> REGEN --> TEACH --> HF --> FT --> GGUF --> DEPLOY
    end

    DEPLOY -.->|"Improved model<br/>generates better outputs"| GEN

    style GEN fill:#4a90d9,color:#fff
    style REPORT fill:#f0ad4e,color:#000
    style VER fill:#5cb85c,color:#fff
    style DEPLOY fill:#d9534f,color:#fff
```

### Prompt Version Lineage

```mermaid
gitGraph
    commit id: "v2_base" tag: "Initial prompt"
    commit id: "v2_evolved_1" tag: "Improved tech stack depth"
    commit id: "v2_evolved_2" tag: "Better implementation steps"
    commit id: "v2_evolved_3" tag: "Refined gap accuracy"
    commit id: "v2_evolved_4" tag: "Current version"
```

---

## Training Data Pipeline

End-to-end flow from seed generation through model deployment.

```mermaid
flowchart LR
    subgraph "Seed Sources"
        SYN["generate_seeds.py<br/>50+ role archetypes<br/>(nurse, pilot, chef, ...)"]
        REAL["extract_real_seeds.py<br/>From actual user sessions<br/>SHA-256 dedup"]
    end

    subgraph "Enrichment"
        SMART["smart_generator.py<br/>Domain Expert Engine"]
        SMART_D["Maps backgrounds to:<br/>• Curated skill gaps<br/>• Project titles<br/>• Tech stacks<br/>• Implementation plans"]
    end

    subgraph "Generation"
        AUG["augment_dataset.py"]
        PROMPT["Constructs prompt with:<br/>• System prompt (evolved)<br/>• Seed profile<br/>• Smart generator context"]
        TEACHER["Teacher Model<br/>Gemini / Ollama"]
    end

    subgraph "Dataset"
        V1["V1 Dataset (text format)<br/>student_advisor_dataset_v1"]
        V2["V2 Dataset (JSON format)<br/>student_advisor_dataset_v2"]
        HFU["hf_uploader.py"]
        HFR["HuggingFace Hub<br/>Hashinika/student-advisor-dataset"]
    end

    subgraph "Training (Colab)"
        NB1["V1 Notebook<br/>Markdown output model"]
        NB2["V2 Notebook<br/>JSON output model"]
        LORA["LoRA Config:<br/>r=64, alpha=64<br/>119M / 4.4B params (2.7%)"]
        SFT["SFTTrainer<br/>1 epoch, 20 steps<br/>lr=2e-4, batch=8"]
    end

    subgraph "Deployment"
        GGUF["Q4_K_M GGUF<br/>~2.49 GB"]
        HFM["HuggingFace Hub<br/>Hashinika/gemma-3-4b-<br/>student-advisor-*-GGUF"]
        OLLAMA["Ollama<br/>student-advisor"]
    end

    SYN --> SMART
    REAL --> SMART
    SMART --- SMART_D
    SMART_D --> AUG
    AUG --- PROMPT --> TEACHER
    TEACHER --> V1 & V2
    V1 --> HFU
    V2 --> HFU
    HFU --> HFR
    HFR --> NB1 & NB2
    NB1 & NB2 --- LORA --- SFT
    SFT --> GGUF --> HFM --> OLLAMA

    style AUG fill:#5cb85c,color:#fff
    style SFT fill:#4a90d9,color:#fff
    style OLLAMA fill:#d9534f,color:#fff
```

### Domain Expert Mappings (smart_generator.py)

```mermaid
graph LR
    subgraph "Student Background"
        FIN["Finance / Quant"]
        MED["Medical / Health"]
        CRE["Creative / Design"]
        SVC["Service / Social"]
        ENG["Engineering / Transport"]
        SEC["Security / Law"]
        DEF["Other"]
    end

    subgraph "Generated Project"
        P1["Algorithmic Trading<br/>Strategy Backtester"]
        P2["Medical Imaging<br/>Triage Assistant"]
        P3["AI-Assisted Creative Tool<br/>/ Lo-Fi Beat Maker"]
        P4["Personalized<br/>Recommendation Engine"]
        P5["Operational Trajectory<br/>Optimizer"]
        P6["Anomaly Detection in<br/>Surveillance/Network Data"]
        P7["Domain-Specific<br/>Interaction Analyzer"]
    end

    FIN --> P1
    MED --> P2
    CRE --> P3
    SVC --> P4
    ENG --> P5
    SEC --> P6
    DEF --> P7
```

---

## Frontend Architecture

The React frontend structure, focusing on how it interacts with the backend.

```mermaid
graph TB
    subgraph "React Application"
        direction TB
        ROUTER["React Router DOM 7<br/>Nested Routes"]

        subgraph "Auth Layer"
            AUTH["AuthContext<br/>localStorage-backed sessions"]
            PROT["ProtectedRoute<br/>→ /login redirect"]
            ROLE["RoleProtectedRoute<br/>student vs expert"]
        end

        subgraph "Student Pages"
            ANAL["AnalysisPage<br/>Manual mode / Source mode"]
            HIST["HistoryPage<br/>Past analyses + feedback"]
        end

        subgraph "Expert Pages"
            FEED["FeedbackPage<br/>Review + Rate outputs"]
            EVOL["EvolutionPage<br/>4-Phase pipeline dashboard"]
            SETT["SettingsPage<br/>Model provider config"]
        end

        subgraph "Shared"
            PROF["ProfilePage<br/>Edit academic profile"]
            LOGIN["LoginPage / RegisterPage"]
        end

        subgraph "Services Layer"
            AS["analysisService.ts<br/>Streaming fetch + generators"]
            FS["feedbackService.ts<br/>TanStack Query mutations"]
            ES["evolutionService.ts<br/>Pattern analysis + evolution"]
            PS["profileService.ts<br/>Profile sync to backend"]
        end

        subgraph "State Management"
            RQ["TanStack React Query<br/>staleTime: 30s, retry: 1"]
            HMS["useModelSettings<br/>localStorage"]
            UST["useStreaming<br/>AbortController + chunk accumulation"]
        end
    end

    subgraph "Vite Dev Server Proxy"
        P_API["/api → :8185<br/>(Backend)"]
        P_AR["/agent-runtime → :8002<br/>(Agent-Runtime)"]
    end

    ROUTER --> AUTH --> PROT & ROLE
    PROT --> ANAL & HIST & PROF
    ROLE --> FEED & EVOL & SETT

    ANAL --> AS --> UST
    FEED --> FS --> RQ
    EVOL --> ES --> RQ
    PROF --> PS

    AS & FS & ES & PS --> P_API
    AS --> P_AR

    style ROUTER fill:#5cb85c,color:#fff
    style RQ fill:#4a90d9,color:#fff
    style P_API fill:#f0ad4e,color:#000
```

### Frontend Output Parsing

The frontend handles two distinct LLM output formats:

```mermaid
flowchart LR
    subgraph "LLM Response"
        STREAM["Streamed text chunks"]
    end

    subgraph "parsers.ts"
        DETECT["Detect format"]
        JSON_P["JSON Parser<br/>Extract gap_analysis +<br/>project_recommendation objects"]
        TEXT_P["Structured Text Parser<br/>Regex extraction of:<br/>Match Score, Missing Skills,<br/>Analysis, Project, Tech Stack,<br/>Implementation Steps"]
    end

    subgraph "Parsed Result"
        RESULT["ParsedResult<br/>matchPercentage: number<br/>missingSkills: string[]<br/>analysisSummary: string<br/>projectTitle: string<br/>techStack: string[]<br/>implementationSteps: Step[]"]
    end

    subgraph "UI Components"
        SCORE["SkillMatchScore<br/>Color-coded percentage"]
        BADGES["Missing Skills<br/>Badge list"]
        CARD["ProjectCard<br/>Tabs: Tech Stack + Steps"]
    end

    STREAM --> DETECT
    DETECT -->|"Gemini / Generic"| JSON_P
    DETECT -->|"Fine-tuned Ollama"| TEXT_P
    JSON_P --> RESULT
    TEXT_P --> RESULT
    RESULT --> SCORE & BADGES & CARD
```

---

## Data Model

### Pydantic Schemas (Backend)

```mermaid
classDiagram
    class StudentData {
        +str name
        +str current_role
        +list~str~ skills
        +str experience_summary
        +str major
        +str interests
        +str personality
    }

    class JobData {
        +str role
        +list~str~ required_skills
        +str description_summary
    }

    class ProjectRequest {
        +StudentData student_data
        +JobData job_data
        +str target_role
        +str model_provider
        +str ollama_model
    }

    class CandidateProfile {
        +str candidate_id
        +str name
        +str current_role
        +str experience_level
        +int total_experience_months
        +list~CandidateSkill~ skills
        +list~WorkExperience~ work_experiences
        +list~CandidateProject~ projects
        +str field_of_study
        +str interests
        +str personality
    }

    class CandidateSkill {
        +str skill_name
        +str proficiency
    }

    class WorkExperience {
        +str title
        +str company_name
        +int duration_months
        +list~str~ skills_used
    }

    class FeedbackEntry {
        +str feedback_id
        +str timestamp
        +dict model_input
        +str model_output
        +str model_provider
        +FeedbackRatings ratings
        +str free_text_comments
        +str reviewer_id
        +str prompt_version
    }

    class FeedbackRatings {
        +int skill_gap_accuracy
        +int project_relevance
        +int tech_stack_appropriateness
        +int implementation_step_quality
        +int overall_quality
    }

    class PatternReport {
        +str report_id
        +int total_feedback_analyzed
        +dict avg_ratings
        +list low_scoring_dimensions
        +list strong_dimensions
        +list recurring_themes
        +list actionable_insights
    }

    class PromptEvolution {
        +str evolution_id
        +str parent_prompt_version
        +str new_prompt_version
        +str pattern_report_id
        +str original_prompt
        +str evolved_prompt
        +str change_summary
    }

    ProjectRequest --> StudentData
    ProjectRequest --> JobData
    CandidateProfile --> CandidateSkill
    CandidateProfile --> WorkExperience
    FeedbackEntry --> FeedbackRatings
    PromptEvolution --> PatternReport : references
```

---

## Knowledge Graph Schema

The Neo4j knowledge graph shared across all services.

```mermaid
graph LR
    P((Person))
    S((Skill))
    WE((WorkExperience))
    PR((Project))
    CE((Certification))
    ED((Education))
    J((Job))
    R((Role))
    SC((SkillCategory))
    CO((Course))

    P -->|HAS_SKILL| S
    P -->|WORKED_AT| WE
    WE -->|USED_SKILL| S
    P -->|WORKED_ON| PR
    PR -->|USES_TECHNOLOGY| S
    P -->|HAS_CERTIFICATION| CE
    P -->|STUDIED_AT| ED
    J -->|REQUIRES_ROLE| R
    R -->|REQUIRES_SKILL| S
    S -->|BELONGS_TO| SC
    S -->|SIMILAR_TO| S
    CO -->|COVERS_SKILL| S

    style P fill:#4a90d9,color:#fff
    style S fill:#5cb85c,color:#fff
    style J fill:#f0ad4e,color:#000
    style R fill:#d9534f,color:#fff
    style SC fill:#68217a,color:#fff
    style CO fill:#17a2b8,color:#fff
```

**Node Properties:**

| Node | Key Properties |
|------|---------------|
| `Person` | candidate_id, name, current_role, experience_level, total_experience_months |
| `Skill` | name, category |
| `WorkExperience` | title, company_name, duration_months |
| `Project` | name, description |
| `Certification` | name |
| `Education` | institution, field_of_study, degree |
| `Job` | job_id, title, company_name, location, role_key, description, job_url |
| `Role` | role_key, name |
| `SkillCategory` | name |
| `Course` | title, provider, rating, url |

**Relationship Weights (Evidence for Skill Confidence):**

| Relationship | Weight | Meaning |
|-------------|--------|---------|
| `USED_SKILL` (WorkExperience) | 0.90 | Used professionally in a job |
| `USES_TECHNOLOGY` (Project) | 0.80 | Applied in a personal/academic project |
| `HAS_SKILL` (Person) | 0.70 | Self-declared on CV |
| `HAS_CERTIFICATION` | 0.60 | Formal certification |

Skill confidence uses the noisy-OR formula: `P(has_skill) = 1 - product(1 - weight_i)` across all evidence sources.

---

## Recommendation Engine Internals

How the Advanced-Recommendation-System computes skill gaps and rankings.

```mermaid
flowchart TB
    subgraph "Input"
        CID["candidate_id"]
        RK["role_key"]
    end

    subgraph "Step 1: Skill Confidence (P_has)"
        EV["Query all evidence edges<br/>HAS_SKILL, USED_SKILL,<br/>USES_TECHNOLOGY, CERTIFICATION"]
        NOR["Noisy-OR aggregation<br/>P(has) = 1 - ∏(1 - w_i)"]
    end

    subgraph "Step 2: Role Importance (TF-IDF)"
        TF["TF = jobs_requiring_skill / total_role_jobs"]
        IDF["IDF = log(total_roles / roles_with_skill)"]
        TFIDF["importance = TF × IDF"]
    end

    subgraph "Step 3: Graded Matching"
        GM["4-tier Match Strength"]
        GM1["1.0 — Exact match"]
        GM2["0.7 — Cluster match<br/>(same semantic cluster)"]
        GM3["0.6 — High similarity<br/>(SIMILAR_TO ≥ 0.80)"]
        GM4["0.4 — Medium similarity<br/>(SIMILAR_TO ≥ 0.68)"]
    end

    subgraph "Step 4: Deficit Computation"
        DEF["deficit = importance × (1 - match_strength)"]
        RANK["Rank by deficit (descending)"]
    end

    subgraph "Step 5: GNN Ranking"
        HGNN["HeteroGNN (SAGEConv)<br/>2 layers, 128-dim, 0.3 dropout"]
        PGNN["P_gnn = sigmoid(person_embed · skill_embed)"]
        FINAL["final_score = gap × importance_norm × P_gnn"]
    end

    subgraph "Step 6: Course Recommendation"
        COVER["Greedy Set Cover<br/>maximize deficit reduction"]
        GAIN["gain = Σ(deficits_covered) + rating_boost"]
    end

    CID --> EV --> NOR
    RK --> TF --> TFIDF
    RK --> IDF --> TFIDF
    NOR --> GM --> DEF
    TFIDF --> DEF
    GM --- GM1 & GM2 & GM3 & GM4
    DEF --> RANK
    RANK --> HGNN --> PGNN --> FINAL
    RANK --> COVER --> GAIN

    style HGNN fill:#4a90d9,color:#fff
    style FINAL fill:#d9534f,color:#fff
    style COVER fill:#5cb85c,color:#fff
```

---

## Agent-Runtime Pipeline

The 4-agent pipeline that processes CVs and writes to the knowledge graph.

```mermaid
sequenceDiagram
    participant C as Client (Backend)
    participant AR as Agent-Runtime :8002
    participant EX as Extractor Agent
    participant NM as Normalizer Agent
    participant KG as KG Writer Tool
    participant GA as Gap Analyzer Tool
    participant N4 as Neo4j
    participant RS as Recommendation :8001

    C->>AR: POST /agent/run (CV JSON)

    AR->>EX: Validate ExtractedData schema
    EX-->>AR: Validated data

    AR->>NM: Normalize skills
    Note over NM: 200+ alias mappings<br/>"python3" → "Python"<br/>"k8s" → "Kubernetes"<br/>+ category assignment
    NM-->>AR: Normalized skills

    AR->>KG: Write to knowledge graph
    KG->>N4: MERGE Person node
    KG->>N4: MERGE Skill nodes (UNWIND batch)
    KG->>N4: CREATE relationships<br/>(HAS_SKILL, WORKED_AT,<br/>USED_SKILL, WORKED_ON, ...)
    N4-->>KG: Success
    KG-->>AR: KG write complete

    AR->>GA: Analyze skill gaps
    GA->>RS: GET /skill-confidence
    RS->>N4: Query evidence edges
    RS-->>GA: P(has) per skill
    GA->>RS: GET /skill-gap-advanced or /missing-skills-gnn
    RS->>N4: Query role importance + GNN inference
    RS-->>GA: Ranked skill gaps
    Note over GA: Compute readiness_score<br/>= 1 - Σ(deficits)/Σ(importances)
    GA-->>AR: Gap analysis results

    AR-->>C: AgentRunResponse<br/>(extracted_data, gap_analysis,<br/>readiness_score, rankings)
```

### PDF Upload Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant AR as Agent-Runtime
    participant CVP as CVParserService
    participant OR as Open Router<br/>(Llama 3.1)
    participant GM as Gemini<br/>(Flash, fallback)
    participant PIPE as Agentic Pipeline

    C->>AR: POST /agent/run-from-pdf<br/>(multipart file upload)
    AR->>CVP: Parse PDF
    CVP->>CVP: Extract text (pdfplumber)<br/>OCR fallback if needed
    CVP->>OR: Structure text via LLM<br/>(Llama 3.1 8B via Open Router)
    alt Open Router fails
        CVP->>GM: Fallback to Gemini Flash
    end
    OR-->>CVP: Structured JSON
    CVP-->>AR: ExtractedData

    AR->>PIPE: Run full pipeline<br/>(Normalize → KG Write → Gap Analyze)
    PIPE-->>AR: Results
    AR-->>C: AgentRunResponse
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Developer Machine / Server"
        FE["Frontend<br/>npm run dev<br/>:5173"]
        BE["Backend<br/>uvicorn :8185"]
        AR["Agent-Runtime<br/>uvicorn :8002"]
        RS["Recommendation<br/>uvicorn :8001"]
        OL["Ollama Server<br/>(local or remote via CF Tunnel)"]
    end

    subgraph "Cloud Services"
        N4[("Neo4j Aura<br/>neo4j+s://2185b358<br/>.databases.neo4j.io")]
        HF["HuggingFace Hub<br/>Hashinika/*"]
        GEM["Google Gemini API"]
        COLAB["Google Colab<br/>NVIDIA L4 GPU"]
    end

    subgraph "HuggingFace Repos"
        HF_DS["Hashinika/student-advisor-dataset"]
        HF_V1["Hashinika/gemma-3-4b-student-advisor-v1"]
        HF_V2["Hashinika/gemma-3-4b-student-advisor-v2"]
        HF_G1["Hashinika/gemma-3-4b-student-advisor-v1-GGUF"]
        HF_G2["Hashinika/gemma-3-4b-student-advisor-v2-GGUF"]
    end

    FE -->|"Vite proxy"| BE
    BE --> AR & RS
    BE & AR & RS --> N4
    BE --> OL & GEM
    BE -->|"Upload datasets"| HF_DS
    COLAB -->|"Pull datasets"| HF_DS
    COLAB -->|"Push LoRA"| HF_V1 & HF_V2
    COLAB -->|"Push GGUF"| HF_G1 & HF_G2
    OL -->|"Pull GGUF"| HF_G1 & HF_G2

    style BE fill:#4a90d9,color:#fff
    style N4 fill:#68217a,color:#fff
    style HF fill:#ff9d00,color:#000
    style COLAB fill:#f9ab00,color:#000
```
