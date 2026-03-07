/**
 * profileService.ts
 *
 * Syncs the browser session (localStorage) with the backend JSONL profile store.
 * All operations are best-effort: errors are surfaced to the caller but never
 * crash the session — localStorage remains the source of truth for UI state.
 */

import { ENDPOINTS } from '@/config/api';
import type { User } from '@/context/AuthContext';

// ── Backend schema types ──────────────────────────────────────────────────

export interface BackendSkill {
  skill_name: string;
  proficiency: string;
}

export interface BackendProfile {
  candidate_id: string;
  name: string;
  current_role?: string;
  experience_level?: string;
  total_experience_months?: number;
  skills?: BackendSkill[];
  work_experiences?: unknown[];
  projects?: unknown[];
  field_of_study?: string;
  interests?: string[];
  personality?: string;
}

// ── Conversion helpers ────────────────────────────────────────────────────

/** Convert a comma-separated skill string → [{skill_name, proficiency}] */
function skillStringToList(csv: string | undefined): BackendSkill[] {
  if (!csv?.trim()) return [];
  return csv
    .split(',')
    .map(s => s.trim())
    .filter(Boolean)
    .map(s => ({ skill_name: s, proficiency: 'intermediate' }));
}

/** Convert [{skill_name}] → comma-separated string */
function skillListToString(skills: BackendSkill[] | undefined): string {
  return (skills ?? []).map(s => s.skill_name).join(', ');
}

/** Convert a comma-separated interests string → string[] */
function interestStringToList(csv: string | undefined): string[] {
  if (!csv?.trim()) return [];
  return csv
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);
}

/** Convert string[] → comma-separated string */
function interestListToString(interests: string[] | undefined): string {
  return (interests ?? []).join(', ');
}

// ── Public API ────────────────────────────────────────────────────────────

/** Map a frontend User to the backend CandidateProfile payload. */
export function userToBackendProfile(user: User): BackendProfile {
  return {
    candidate_id: user.id,
    name: user.name,
    current_role: user.current_role || 'Student',
    field_of_study: user.major || 'Undeclared',
    interests: interestStringToList(user.interests),
    personality: user.personality || 'ambitious, learner',
    skills: skillStringToList(user.skills),
  };
}

/** Merge backend profile fields back into a frontend User (non-destructive). */
export function mergeBackendProfile(user: User, backend: BackendProfile): User {
  return {
    ...user,
    name: backend.name || user.name,
    current_role: backend.current_role ?? user.current_role,
    major: backend.field_of_study ?? user.major,
    interests: backend.interests?.length
      ? interestListToString(backend.interests)
      : user.interests,
    personality: backend.personality ?? user.personality,
    skills: backend.skills?.length
      ? skillListToString(backend.skills)
      : user.skills,
  };
}

/** POST /profiles — create or update the profile in the backend JSONL store. */
export async function saveBackendProfile(user: User): Promise<void> {
  const payload = userToBackendProfile(user);
  const res = await fetch(ENDPOINTS.PROFILES.SAVE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Profile sync failed (${res.status}): ${text}`);
  }
}

/** GET /profiles/{candidate_id} — fetch stored profile, or null if not found. */
export async function fetchBackendProfile(candidateId: string): Promise<BackendProfile | null> {
  const res = await fetch(ENDPOINTS.PROFILES.GET(candidateId));
  if (res.status === 404) return null;
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Profile fetch failed (${res.status}): ${text}`);
  }
  return res.json() as Promise<BackendProfile>;
}
