import { ENDPOINTS } from '@/config/industryConnectApi';
import type { ProjectRequest, CombinedSourceRequest, RoleInfo, LinkedInJobResult, CandidateSummary } from '@/types/industryConnect';

// ---- Streaming generators ----

export async function* generateProject(
  request: ProjectRequest,
  signal?: AbortSignal,
): AsyncGenerator<string> {
  const response = await fetch(ENDPOINTS.ANALYSIS.GENERATE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Generation failed: ${response.status} ${response.statusText}`);
  }

  yield* _streamResponse(response);
}

export async function* generateProjectFromSources(
  request: CombinedSourceRequest,
  signal?: AbortSignal,
): AsyncGenerator<string> {
  const response = await fetch(ENDPOINTS.ANALYSIS.GENERATE_FROM_SOURCES, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Generation failed: ${response.status} ${response.statusText}`);
  }

  yield* _streamResponse(response);
}

async function* _streamResponse(response: Response): AsyncGenerator<string> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      yield decoder.decode(value, { stream: true });
    }
  } finally {
    reader.releaseLock();
  }
}

// ---- Companion service fetchers ----

export async function fetchRoles(): Promise<RoleInfo[]> {
  const response = await fetch(ENDPOINTS.ROLE_SKILLS.ROLES);
  if (!response.ok) throw new Error(`Failed to fetch roles: ${response.status}`);
  const data = await response.json();
  // Backend returns { roles: [...], count: N }
  return Array.isArray(data) ? data : (data.roles ?? []);
}

export async function fetchJobsByRole(roleKey: string): Promise<LinkedInJobResult[]> {
  // Primary endpoint: gaps-analyzer /jobs-by-role (reads from Neo4j)
  const primaryUrl = ENDPOINTS.ROLE_SKILLS.JOBS_BY_ROLE(roleKey);
  const response = await fetch(primaryUrl);
  if (!response.ok) throw new Error(`Failed to fetch jobs: ${response.status}`);

  const data = await response.json();
  // /jobs-by-role returns { role_key, count, jobs: [...] }
  return Array.isArray(data) ? data : (data.jobs ?? data.hits ?? []);
}

export async function searchJobs(query: string, pageSize = 10): Promise<LinkedInJobResult[]> {
  const url = `${ENDPOINTS.SCRAPER.SEARCH}?query=${encodeURIComponent(query)}&page_size=${pageSize}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Job search failed: ${response.status}`);
  const data = await response.json();
  // Neo4j search returns { total, hits: [...], page, page_size, pages }
  return Array.isArray(data) ? data : (data.hits ?? []);
}

export async function fetchCandidates(): Promise<CandidateSummary[]> {
  const response = await fetch(ENDPOINTS.AGENT.CANDIDATES);
  if (!response.ok) throw new Error(`Failed to fetch candidates: ${response.status}`);
  return response.json();
}
