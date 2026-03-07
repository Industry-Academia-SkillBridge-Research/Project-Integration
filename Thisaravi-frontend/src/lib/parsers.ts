import type { AnalysisResult } from '@/types/api';

export function extractJson(text: string): Record<string, unknown> {
  try {
    // Try markdown JSON block
    const mdMatch = text.match(/```json\s*([\s\S]*?)\s*```/);
    if (mdMatch) return JSON.parse(mdMatch[1]);

    // Try raw JSON object
    const rawMatch = text.match(/(\{[\s\S]*\})/);
    if (rawMatch) return JSON.parse(rawMatch[1]);

    // Try direct parse
    return JSON.parse(text);
  } catch {
    return {};
  }
}

export function parseStructuredText(text: string): AnalysisResult {
  try {
    // 1. Gap Analysis
    const gapMatch = text.match(
      /(?:Gap Analysis|Analysis)(?:[:\s-]*|\s*\n)([\s\S]*?)(?=(?:\*\*|#|Match Score|Project)|$)/i
    );
    // 2. Match Score
    const scoreMatch = text.match(/Match Score[^\d]*(\d+)/i);
    // 3. Project Recommendation
    const projMatch = text.match(
      /(?:Project Recommendation|Recommended Project|Project)(?:[:\s-]*|\s*\n)([\s\S]*?)(?=(?:\*\*|#|Tech Stack)|$)/i
    );
    // 4. Tech Stack
    const stackMatch = text.match(
      /(?:Tech Stack|Technologies|Stack)(?:[:\s-]*|\s*\n)([\s\S]*?)(?=(?:\*\*|#|Steps|Implementation)|$)/i
    );
    // 5. Steps
    const stepsMatch = text.match(
      /(?:Steps|Implementation|Plan)(?:[:\s-]*|\s*\n)([\s\S]*)/i
    );

    const gapText = gapMatch
      ? gapMatch[1].trim()
      : text.length > 500
        ? text.slice(0, 500) + '...'
        : text;

    const rawStack = stackMatch ? stackMatch[1].trim() : '';
    const techStack = rawStack
      // Split only on commas, "and", semicolons, or a newline followed by a bullet/dash
      // Do NOT split on bare "-" — that breaks hyphenated tech names like "CI/CD"
      .split(/,|;|\band\b|\n\s*[-*]\s*/)
      .map((s) => s.replace(/^[-*\s]+/, '').trim())
      .filter(Boolean);

    const rawSteps = stepsMatch ? stepsMatch[1].trim() : '';
    // Only split on actual list markers at the start of a line:
    //   - "1." / "1)" / "1:" followed by whitespace
    //   - "Step N" variants
    //   - "- " or "* " (dash/bullet followed by a space — NOT bare "-" inside words)
    // This prevents fragmentation of hyphenated words like "domain-specific".
    const stepsNormalized = rawSteps.replace(/\r\n/g, '\n');
    const steps = stepsNormalized
      .split(/\n\s*(?:\d+[.):\s]\s+|Step\s+\d+[.:)?\s]\s*|[-*]\s+)/)
      .map((s) => s.replace(/^(?:Step\s*)?\d+[.):\s]\s*/i, '').trim())
      .filter((s) => s.length > 5);

    return {
      gap_analysis: {
        analysis_summary: gapText,
        match_percentage: scoreMatch ? parseInt(scoreMatch[1], 10) : 0,
        missing_skills: [],
      },
      project_recommendation: {
        project_title: projMatch ? projMatch[1].trim() : 'Recommended Capstone',
        objective: 'Capstone Project',
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

export function parseResponse(text: string): AnalysisResult {
  // 1. Try JSON first (generic models)
  const jsonData = extractJson(text);
  if (jsonData && 'gap_analysis' in jsonData) {
    const result = jsonData as unknown as AnalysisResult;
    // Coerce match_percentage to a number — some models return "85%" or "85"
    const raw = (result.gap_analysis as Record<string, unknown>).match_percentage;
    if (typeof raw !== 'number') {
      (result.gap_analysis as Record<string, unknown>).match_percentage =
        parseInt(String(raw).replace(/[^\d]/g, ''), 10) || 0;
    }
    return result;
  }

  // 2. Try structured text parsing (fine-tuned model)
  const textData = parseStructuredText(text);
  if (textData && 'gap_analysis' in textData && !textData.error) {
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
