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
    // 1. Match Score (do this early — it's unambiguous)
    const scoreMatch = text.match(/(?:Match Score|match_percentage)[^\d]*(\d+)/i);

    // 2. Missing Skills — "[Missing Skills]:" or "**Missing Skills:**" etc.
    const missingMatch = text.match(
      /(?:\[Missing Skills\]|\*\*Missing Skills\*\*|Missing Skills)\s*[:\-]*\s*([\s\S]*?)(?=\n\s*\n|\[Match|Match Score|\*\*Match|\*\*Objective|\*\*Title|###|$)/i
    );

    // 3. Analysis Summary — "[Analysis]:" or "**Analysis:**" or general gap block
    const analysisMatch = text.match(
      /(?:\[Analysis\]|\*\*Analysis\*\*|Analysis Summary)\s*[:\-]*\s*([\s\S]*?)(?=\n\s*\n|###|$)/i
    );
    // Fallback: grab the Gap Analysis section header content
    const gapHeaderMatch = !analysisMatch
      ? text.match(
          /(?:Gap Analysis)(?:[:\s-]*|\s*\n)([\s\S]*?)(?=###|\*\*Title|\*\*Objective|Project Recommendation|$)/i
        )
      : null;

    // 4. Project Title — "**Title:**" or "Project Title:" etc.
    const titleMatch = text.match(
      /(?:\*\*Title\*\*|\*\*Project Title\*\*|Project Title|Title)\s*[:\-]*\s*\*{0,2}\s*(.+)/i
    );

    // 5. Objective — "**Objective:**"
    const objectiveMatch = text.match(
      /(?:\*\*Objective\*\*|Objective)\s*[:\-]*\s*\*{0,2}\s*(.+)/i
    );

    // 6. Tech Stack — "**Tech Stack:**" or "**Technologies:**"
    //    Require bold markers or newline-anchored heading to avoid matching
    //    casual mentions of "stack" / "technologies" inside Gap Analysis prose.
    const stackMatch = text.match(
      /(?:\*\*Tech Stack\b[^*]*\*\*|\*\*Technologies\b[^*]*\*\*|\n\s*Tech Stack)\s*[:\-]*\s*([\s\S]*?)(?=\*\*Implementation|\*\*Steps|\*\*\d+[.)]\s|---\s*\n\s*\*\*\d|\n\s*\n|###|$)/i
    );

    // 7. Implementation Steps — "**Implementation Plan:**" or "**Steps:**"
    //    Must match "Implementation Plan" as a unit so "Plan:**" isn't left in the capture
    let stepsMatch = text.match(
      /(?:\*\*Implementation Plan\*\*|\*\*Implementation Steps\*\*|\*\*Implementation\*\*|Implementation Plan|Implementation Steps|Steps)\s*[:\-]*\s*\*{0,2}\s*([\s\S]*)/i
    );

    // Fallback: numbered bold steps after tech stack (e.g. "---\n\n**1. Step Name**:")
    if (!stepsMatch && stackMatch) {
      const afterStack = text.slice(stackMatch.index! + stackMatch[0].length);
      const numberedMatch = afterStack.match(/(?:---\s*\n+)?\s*(\*\*1[.)]\s+[\s\S]*)/);
      if (numberedMatch) stepsMatch = numberedMatch;
    }

    // --- Extract gap summary ---
    let gapText = '';
    if (analysisMatch) {
      gapText = analysisMatch[1].replace(/\*\*/g, '').trim();
    } else if (gapHeaderMatch) {
      // Strip out [Missing Skills] and [Match Score] lines if they got captured
      gapText = gapHeaderMatch[1]
        .replace(/\[Missing Skills\][\s\S]*?(?=\[Analysis\]|\n\s*\n|$)/i, '')
        .replace(/\[Match Score\][\s\S]*?(?=\[Analysis\]|\n\s*\n|$)/i, '')
        .replace(/\*\*/g, '')
        .trim();
    }
    if (!gapText) {
      gapText = text.length > 500 ? text.slice(0, 500) + '...' : text;
    }

    // --- Extract missing skills ---
    const missingSkills: string[] = [];
    if (missingMatch) {
      missingMatch[1]
        .trim()
        .split(/,|\n/)
        .map((s) => s.replace(/^[-*\s\d.)]+/, '').trim())
        .filter((s) => s.length > 1)
        .forEach((s) => missingSkills.push(s));
    }

    // --- Extract tech stack ---
    const rawStack = stackMatch ? stackMatch[1].trim() : '';
    const techStack = rawStack
      .split(/,|;|\band\b|\n\s*[-*]\s*/)
      .map((s) => s.replace(/^[-*\s]+/, '').replace(/\*\*/g, '').trim())
      .filter(Boolean);

    // --- Extract steps ---
    let rawSteps = stepsMatch ? stepsMatch[1].trim() : '';
    // Strip leading --- separator that may precede numbered steps
    rawSteps = rawSteps.replace(/^---\s*\n*/g, '').trim();
    const stepsNormalized = rawSteps.replace(/\r\n/g, '\n');
    const stepParts = stepsNormalized
      .split(/\n\s*(?:\*{0,2}\d+[.):\s]\s+|Step\s+\d+[.:)?\s]\s*|[-*]\s+)/);
    // Remove ghost first element (preamble before first numbered step)
    if (stepParts.length > 1 && stepParts[0].length < 20) stepParts.shift();
    const steps = stepParts
      .map((s) => s
        .replace(/^\*{0,2}(?:Step\s*)?\d+[.):\-]\s*\*{0,2}\s*/i, '')  // strip bold-wrapped numbering
        .replace(/^\*\*/, '')                          // strip leading **
        .replace(/\*\*[:\s]*$/, '')                    // strip trailing **:
        .replace(/\*\*/g, '')                          // strip remaining **
        .trim()
      )
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
