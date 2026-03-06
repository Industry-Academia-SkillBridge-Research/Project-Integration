import { ENDPOINTS } from '@/config/api';
import type { FeedbackEntry, ModelOutputLog, EvolutionStatus, HistoryEntry } from '@/types/api';

export async function fetchUnreviewedOutputs(): Promise<ModelOutputLog[]> {
  const res = await fetch(ENDPOINTS.FEEDBACK.UNREVIEWED);
  if (!res.ok) throw new Error(`Failed to fetch unreviewed outputs: ${res.status}`);
  return res.json();
}

export async function fetchAllFeedback(): Promise<FeedbackEntry[]> {
  const res = await fetch(ENDPOINTS.FEEDBACK.ALL);
  if (!res.ok) throw new Error(`Failed to fetch feedback: ${res.status}`);
  return res.json();
}

export async function fetchFeedbackStatus(): Promise<EvolutionStatus> {
  const res = await fetch(ENDPOINTS.FEEDBACK.STATUS);
  if (!res.ok) throw new Error(`Failed to fetch status: ${res.status}`);
  return res.json();
}

export async function submitFeedback(
  entry: FeedbackEntry,
): Promise<{ status: string; feedback_id: string }> {
  const res = await fetch(ENDPOINTS.FEEDBACK.SUBMIT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  });
  if (!res.ok) throw new Error(`Failed to submit feedback: ${res.status}`);
  return res.json();
}

export async function fetchMyHistory(studentName: string): Promise<HistoryEntry[]> {
  const url = `${ENDPOINTS.FEEDBACK.MY_OUTPUTS}?student_name=${encodeURIComponent(studentName)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch history: ${res.status}`);
  return res.json();
}
