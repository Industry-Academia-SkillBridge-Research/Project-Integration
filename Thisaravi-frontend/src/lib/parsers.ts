import type { AnalysisResult, GapAnalysis, ProjectRecommendation } from '@/types/api';

// ---------------------------------------------------------------------------
// JSON extraction
// ---------------------------------------------------------------------------

export function extractJson(text: string): Record<string, unknown> {
  try {
    // Try markdown JSON block
    const mdMatch = text.match(/```json\s*([\s\S]*?)\s*```/);
    if (mdMatch) return JSON.parse(mdMatch[1]);

    // Try raw JSON object (greedy — pick the largest braced block)
    const rawMatch = text.match(/(\{[\s\S]*\})/);
    if (rawMatch) return JSON.parse(rawMatch[1]);

    // Try direct parse
    return JSON.parse(text);
  } catch {
    return {};
  }
}

// ---------------------------------------------------------------------------
// Safe array helper — normalise an unknown value into string[]
// ---------------------------------------------------------------------------
function toStringArray(val: unknown): string[] {
  if (Array.isArray(val)) return val.map(String).filter(Boolean);
  if (typeof val === 'string') {
    return val
      .split(/,|;|\n/)
      .map((s) => s.replace(/^[-*\s\d.)]+/, '').trim())
      .filter(Boolean);
  }
  return [];
}

// ---------------------------------------------------------------------------
// Normalise a JSON blob into AnalysisResult
// ---------------------------------------------------------------------------
function normaliseJson(data: Record<string, unknown>): AnalysisResult | null {
  const gap = data.gap_analysis as Record<string, unknown> | undefined;
  const proj = data.project_recommendation as Record<string, unknown> | undefined;
  if (!gap) return null;

  // Coerce match_percentage
  let score = 0;
  if (gap.match_percentage != null) {
    score = typeof gap.match_percentage === 'number'
      ? gap.match_percentage
      : parseInt(String(gap.match_percentage).replace(/[^\d]/g, ''), 10) || 0;
  }

  const gapResult: GapAnalysis = {
    analysis_summary: String(gap.analysis_summary ?? ''),
    match_percentage: score,
    missing_skills: toStringArray(gap.missing_skills),
  };

  const projResult: ProjectRecommendation = proj
    ? {
        project_title: String(proj.project_title ?? ''),
        objective: String(proj.objective ?? ''),
        tech_stack: toStringArray(proj.tech_stack),
        implementation_steps: toStringArray(proj.implementation_steps),
      }
    : { project_title: '', objective: '', tech_stack: [], implementation_steps: [] };

  return { gap_analysis: gapResult, project_recommendation: projResult };
}

// ---------------------------------------------------------------------------
// Structured-text parser (fine-tuned Ollama markdown output)
// ---------------------------------------------------------------------------

export function parseStructuredText(text: string): AnalysisResult {
  try {
    // 1. Gap Analysis / Summary
    const gapMatch = text.match(
      /(?:Gap Analysis|Analysis)(?:[:\s-]*|\s*\n)([\s\S]*?)(?=(?:\*\*|#|Match Score|Project|Missing Skills|\[Missing))/i
    );
    // 2. Match Score
    const scoreMatch = text.match(/(?:Match Score|match_percentage)[^\d]*(\d+)/i);
    // 3. Missing Skills — handles both "[Missing Skills]:" and "**Missing Skills:**" and list formats
    const missingMatch = text.match(
      /(?:Missing Skills|Skill Gaps?)(?:\]?\s*[:\-]*\s*|\s*\**\s*[:\-]*\s*)([\s\S]*?)(?=\n\s*\n|\[Match|Match Score|\*\*Match|#|$)/i
    );
    // 4. Project Title
    const titleMatch = text.match(
      /(?:Title|Project Title|Project Recommendation|Recommended Project)[:\s*]*\s*(.+)/i
    );
    // 5. Objective
    const objectiveMatch = text.match(
      /(?:Objective)[:\s*]*\s*(.+)/i
    );
    // 6. Tech Stack
    const stackMatch = text.match(
      /(?:Tech Stack|Technologies|Stack)(?:[:\s*-]*|\s*\n)([\s\S]*?)(?=(?:\*\*|#|Steps|Implementation)|$)/i
    );
    // 7. Steps / Implementation
    const stepsMatch = text.match(
      /(?:Steps|Implementation|Plan)(?:[:\s*-]*|\s*\n)([\s\S]*)/i
    );

    // --- Extract gap summary ---
    const gapText = gapMatch
      ? gapMatch[1].replace(/\*\*/g, '').trim()
      : text.length > 500
        ? text.slice(0, 500) + '...'
        : text;

    // --- Extract missing skills ---
    const missingSkills: string[] = [];
    if (missingMatch) {
      const raw = missingMatch[1].trim();
      raw
        .split(/,|\n/)
        .map((s) => s.replace(/^[-*\s\d.)]+/, '').trim())
        .filter((s) => s.length > 1)
        .forEach((s) => missingSkills.push(s));
    }

    // --- Extract tech stack ---
    const rawStack = stackMatch ? stackMatch[1].trim() : '';
    const techStack = rawStack
      .split(/,|;|\band\b|\n\s*[-*]\s*/)
      .map((s) => s.replace(/^[-*\s]+/, '').trim())
      .filter(Boolean);

    // --- Extract steps ---
    const rawSteps = stepsMatch ? stepsMatch[1].trim() : '';
    const stepsNormalized = rawSteps.replace(/\r\n/g, '\n');
    const steps = stepsNormalized
      .split(/\n\s*(?:\d+[.):\s]\s+|Step\s+\d+[.:)?\s]\s*|[-*]\s+)/)
      .map((s) => s.replace(/^(?:Step\s*)?\d+[.):\s]\s*/i, '').trim())
      .filter((s) => s.length > 5);

    // --- Extract project title ---
    const projectTitle = titleMatch
      ? titleMatch[1].replace(/\*\*/g, '').trim()
      : 'Recommended Capstone';

    // --- Extract objective ---
    const objective = objectiveMatch
      ? objectiveMatch[1].replace(/\*\*/g, '').trim()
      : 'Capstone Project';

    return {
      gap_analysis: {
        analysis_summary: gapText,
        match_percentage: scoreMatch ? parseInt(scoreMatch[1], 10) : 0,
        missing_skills: missingSkills,
      },
      project_recommendation: {
        project_title: projectTitle,
        objective,
        tech_stack: techStack.length ? techStack : ['Python', 'General Dev'],
        implementation_steps: steps.length ? steps : ['Review full analysis for details.'],
      },
    };
  } catch (e) {
    return {
      gap_analysis: { analysis_summary: '', match_percentage: 0, missing_skills: [] },
      project_recommendation: { project_title: '', objective: '', tech_stack: [], implementation_steps: [] },
      error: `Failed to parse text: ${e}`,
      raw_text: text,
    };
  }
}

// ---------------------------------------------------------------------------
// Main entry point — tries JSON first, then structured text
// ---------------------------------------------------------------------------

export function parseResponse(text: string): AnalysisResult {
  // 1. Try JSON first (Gemini / generic models)
  const jsonData = extractJson(text);
  if (jsonData && Object.keys(jsonData).length > 0) {
    // Standard format: { gap_analysis, project_recommendation }
    const normalised = normaliseJson(jsonData);
    if (normalised) return normalised;
  }

  // 2. Try structured text parsing (fine-tuned model markdown)
  const textData = parseStructuredText(text);
  if (textData && !textData.error) {
    return textData;
  }

  // 3. Fallback
  return {
    gap_analysis: { analysis_summary: '', match_percentage: 0, missing_skills: [] },
    project_recommendation: { project_title: '', objective: '', tech_stack: [], implementation_steps: [] },
    error: 'Could not parse output',
    raw_text: text,
  };
}
