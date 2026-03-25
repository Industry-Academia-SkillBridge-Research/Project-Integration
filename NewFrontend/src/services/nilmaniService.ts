/**
 * Nilmani Backend API Service
 * Handles interview-related API calls to Nilmani-backend (port 8188)
 */

const NILMANI_API_BASE = import.meta.env.VITE_NILMANI_API_URL || 'http://localhost:8188';

export interface UploadJDResponse {
  session_id: string;
  text: string;
  chunks_count: number;
}

export interface StartInterviewResponse {
  question: string;
  question_number: number;
  total_questions: number;
}

export interface NextQuestionResponse {
  question: string;
  question_number: number;
  total_questions: number;
  is_complete: boolean;
}

export interface SessionStatus {
  session_id: string;
  status: string;
  current_question: number;
  total_questions: number;
}

/**
 * Upload job description PDF and initialize interview session
 */
export const uploadJobDescription = async (file: File): Promise<UploadJDResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${NILMANI_API_BASE}/api/upload-jd`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || 'Failed to upload job description');
  }
  
  return response.json();
};

/**
 * Start the interview session
 */
export const startInterview = async (sessionId: string): Promise<StartInterviewResponse> => {
  const response = await fetch(`${NILMANI_API_BASE}/api/start-interview`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
    }),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to start interview' }));
    throw new Error(error.detail || 'Failed to start interview');
  }
  
  return response.json();
};

/**
 * Submit answer and get next question
 */
export const submitAnswer = async (
  sessionId: string,
  answer: string
): Promise<NextQuestionResponse> => {
  const response = await fetch(`${NILMANI_API_BASE}/api/next-question`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      user_answer: answer,
    }),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to submit answer' }));
    throw new Error(error.detail || 'Failed to submit answer');
  }
  
  return response.json();
};

/**
 * Get session status
 */
export const getSessionStatus = async (sessionId: string): Promise<SessionStatus> => {
  const response = await fetch(`${NILMANI_API_BASE}/api/session/${sessionId}`);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get session status' }));
    throw new Error(error.detail || 'Failed to get session status');
  }
  
  return response.json();
};

/**
 * End/delete session
 */
export const endSession = async (sessionId: string): Promise<void> => {
  const response = await fetch(`${NILMANI_API_BASE}/api/session/${sessionId}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to end session' }));
    throw new Error(error.detail || 'Failed to end session');
  }
};
