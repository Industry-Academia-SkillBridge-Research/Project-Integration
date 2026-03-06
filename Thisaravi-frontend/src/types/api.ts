// Request types (match main.py Pydantic models)
export interface StudentData {
  name: string;
  current_role: string;
  skills: string[];
  experience_summary: string;
  major?: string;
  interests?: string[];
  personality?: string;
}

export interface JobData {
  role: string;
  required_skills: string[];
  description_summary: string;
}

export interface ProjectRequest {
  student_data: StudentData;
  job_data: JobData;
  target_role: string;
  model_provider: 'gemini' | 'ollama' | 'ollama_generic';
  ollama_model?: string | null;
}

// ---- Source-mode types (match main.py CombinedSourceRequest) ----
export interface CandidateSkill {
  skill_name: string;
  category?: string;
  proficiency?: string;
}

export interface CandidateProfile {
  candidate_id: string;
  name: string;
  current_role: string;
  skills: CandidateSkill[];
  work_experiences?: unknown[];
  projects?: unknown[];
}

export interface CandidateSummary {
  candidate_id: string;
  name: string;
  current_role: string;
}

export interface CombinedSourceRequest {
  job_id?: string;
  candidate_id?: string;
  role_key?: string;
  inline_job?: JobData;
  inline_candidate?: CandidateProfile;
  model_provider: 'gemini' | 'ollama' | 'ollama_generic';
}

// Role-Skill-API
export interface RoleInfo {
  role_key: string;
  name: string;
  tag?: string;
  job_count?: number;
}

// LinkedIn Scraper search result
export interface LinkedInJobResult {
  job_id: string;
  title: string;
  company?: string;
  location?: string;
  skills?: string[];
  description_summary?: string;
  description?: string;
  role_key?: string;
  role_tag?: string;
  job_role?: string;
  posted_date?: string;
  job_url?: string;
}

// Response types (match parsers.py output structure)
export interface GapAnalysis {
  missing_skills: string[];
  match_percentage: number;
  analysis_summary: string;
}

export interface ProjectRecommendation {
  project_title: string;
  objective: string;
  tech_stack: string[];
  implementation_steps: string[];
}

export interface AnalysisResult {
  gap_analysis: GapAnalysis;
  project_recommendation: ProjectRecommendation;
  error?: string;
  raw_text?: string;
}

// Feedback types (match feedback/schemas.py)
export interface FeedbackRatings {
  skill_gap_accuracy: number;
  project_relevance: number;
  tech_stack_appropriateness: number;
  implementation_step_quality: number;
  overall_quality: number;
}

export interface FeedbackEntry {
  feedback_id?: string;
  timestamp?: string;
  model_input: Record<string, unknown>;
  model_output: string;
  model_provider: string;
  ratings: FeedbackRatings;
  free_text_comments: string;
  reviewer_id?: string;
  prompt_version: string;
}

export interface ModelOutputLog {
  output_id: string;
  timestamp: string;
  model_input: Record<string, unknown>;
  model_output: string;
  model_provider: string;
  prompt_version: string;
  has_feedback: boolean;
}

// Evolution types (match feedback/schemas.py)
export interface PatternReport {
  report_id: string;
  timestamp: string;
  total_feedback_analyzed: number;
  avg_ratings: Record<string, number>;
  low_scoring_dimensions: string[];
  strong_dimensions: string[];
  recurring_themes: string[];
  actionable_insights: string[];
  raw_summary: string;
}

export interface PromptEvolution {
  evolution_id: string;
  timestamp: string;
  parent_prompt_version: string;
  new_prompt_version: string;
  pattern_report_id: string;
  original_prompt: string;
  evolved_prompt: string;
  change_summary: string;
}

// History types — student output + optional feedback
export interface HistoryEntry {
  output: ModelOutputLog;
  feedback: FeedbackEntry | null;
}

export interface EvolutionStatus {
  current_prompt_version: string;
  total_feedback: number;
  feedback_per_version: Record<string, number>;
  total_reports: number;
  total_evolutions: number;
  evolution_history: Array<{
    from: string;
    to: string;
    timestamp: string;
    summary: string;
  }>;
}
