/**
 * Nipuni Backend API Service
 * Handles transcript processing, skill validation, quiz generation, and job recommendations
 */

const NIPUNI_API_BASE = import.meta.env.VITE_NIPUNI_API_URL || 'http://localhost:8000';

// Helper function for making API requests
async function nipuniRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${NIPUNI_API_BASE}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ 
        message: `HTTP ${response.status}: ${response.statusText}` 
      }));
      throw {
        response: {
          status: response.status,
          data: errorData
        },
        message: errorData.message || errorData.detail || `Request failed with status ${response.status}`
      };
    }

    return await response.json();
  } catch (error: any) {
    if (!error.response) {
      // Network error
      console.error('Network Error: No response from server');
      throw {
        message: `Cannot connect to Nipuni backend at ${NIPUNI_API_BASE}. Please ensure it's running.`,
        response: null
      };
    }
    throw error;
  }
}

// ===========================
// Transcript Endpoints
// ===========================

export const uploadTranscript = async (studentId: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('student_id', studentId);
  
  return nipuniRequest(`/transcript/upload`, {
    method: 'POST',
    body: formData,
  });
};

export const getTranscript = async (studentId: string) => {
  return nipuniRequest(`/transcript/${studentId}`, {
    method: 'GET',
  });
};

// ===========================
// Skills Endpoints (Flat Structure)
// ===========================

export const getClaimedSkills = async (studentId: string) => {
  return nipuniRequest(`/students/${studentId}/skills/claimed`, {
    method: 'GET',
  });
};

export const getSkillEvidence = async (studentId: string, skillName: string) => {
  return nipuniRequest(`/students/${studentId}/explain/skill/${encodeURIComponent(skillName)}`, {
    method: 'GET',
  });
};

// ===========================
// Quiz Endpoints
// ===========================

export const planQuiz = async (studentId: string, selectedSkills: string[]) => {
  return nipuniRequest(`/students/${studentId}/quiz/plan`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ selected_skills: selectedSkills }),
  });
};

export const generateQuizFromBank = async (studentId: string) => {
  return nipuniRequest(`/students/${studentId}/quiz/from-bank`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
};

export const submitQuiz = async (studentId: string, attemptId: string | number, answers: any[]) => {
  return nipuniRequest(`/students/${studentId}/quiz/${attemptId}/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ answers }),
  });
};

// ===========================
// Job Recommendation Endpoints
// ===========================

export interface JobRecommendationParams {
  topK?: number;
  threshold?: number;
  useVerified?: boolean;
  roleKey?: string;
}

// Rule-based job recommendations (with filters)
export const getJobRecommendations = async (studentId: string, params: JobRecommendationParams = {}) => {
  const searchParams = new URLSearchParams({
    top_k: String(params.topK || 10),
    threshold: String(params.threshold || 70),
  });
  
  if (params.roleKey) {
    searchParams.append('role_key', params.roleKey);
  }
  
  return nipuniRequest(`/students/${studentId}/jobs/recommend?${searchParams}`, {
    method: 'GET',
  });
};

// ML-Enhanced job recommendations (uses validated quiz results)
export const getMLJobRecommendations = async (studentId: string, params: JobRecommendationParams = {}) => {
  const searchParams = new URLSearchParams({
    top_k: String(params.topK || 10),
    threshold: String(params.threshold || 70),
    use_verified: String(params.useVerified !== undefined ? params.useVerified : true),
  });
  
  if (params.roleKey) {
    searchParams.append('role_key', params.roleKey);
  }
  
  return nipuniRequest(`/students/${studentId}/jobs/recommend/ml?${searchParams}`, {
    method: 'GET',
  });
};

export const getJobDetails = async (jobId: string) => {
  return nipuniRequest(`/jobs/${jobId}`, {
    method: 'GET',
  });
};

// ===========================
// Portfolio Endpoints
// ===========================

export const getStudentPortfolio = async (studentId: string) => {
  return nipuniRequest(`/students/${studentId}/profile/portfolio`, {
    method: 'GET',
  });
};

export const getStudentProfile = async (studentId: string) => {
  return nipuniRequest(`/students/${studentId}/profile`, {
    method: 'GET',
  });
};

export const updateStudentProfile = async (studentId: string, profileData: any) => {
  return nipuniRequest(`/students/${studentId}/profile`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(profileData),
  });
};

export const uploadProfilePhoto = async (studentId: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  return nipuniRequest(`/students/${studentId}/profile/photo`, {
    method: 'POST',
    body: formData,
  });
};

export const clearStudentPortfolio = async (studentId: string) => {
  return nipuniRequest(`/students/${studentId}/profile/portfolio`, {
    method: 'DELETE',
  });
};

// ===========================
// XAI Endpoints
// ===========================

export const getSkillsSummary = async (studentId: string) => {
  return nipuniRequest(`/students/${studentId}/xai/skills/summary`, {
    method: 'GET',
  });
};

export const getSkillExplanation = async (studentId: string, skillName: string, skillType: 'parent' | 'child' = 'parent') => {
  const searchParams = new URLSearchParams({
    skill_type: skillType
  });
  
  return nipuniRequest(`/students/${studentId}/xai/skills/${encodeURIComponent(skillName)}/explain?${searchParams}`, {
    method: 'GET',
  });
};

export default { 
  uploadTranscript,
  getTranscript,
  getClaimedSkills,
  getSkillEvidence,
  planQuiz,
  generateQuizFromBank,
  submitQuiz,
  getJobRecommendations,
  getMLJobRecommendations,
  getJobDetails,
  getStudentPortfolio,
  getStudentProfile,
  updateStudentProfile,
  uploadProfilePhoto,
  clearStudentPortfolio,
  getSkillsSummary,
  getSkillExplanation,
};

