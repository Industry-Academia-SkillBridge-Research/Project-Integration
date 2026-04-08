// Request types (match Thisaravi-backend Pydantic models)
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

// ---- Source-mode types (match Thisaravi-backend CombinedSourceRequest) ----
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
  // Manual mode: accept raw student/job data directly
  inline_student_data?: StudentData;
  inline_job_data?: JobData;
  target_role?: string;
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

// Model settings
export interface ModelSettings {
  model_provider: 'ollama' | 'gemini' | 'ollama_generic';
  ollama_model: string;
}

// Feedback types
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

// History: student output + optional expert feedback
export interface HistoryEntry {
  output: ModelOutputLog;
  feedback: FeedbackEntry | null;
}
