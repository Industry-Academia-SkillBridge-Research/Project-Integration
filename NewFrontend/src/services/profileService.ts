import { toast } from "@/hooks/use-toast";

const API_URL = import.meta.env.VITE_AUTH_API || 'http://localhost:8182';

export interface AnalysisUpdateData {
  readiness_score?: number;
  skill_gap_index?: any;
  ai_explanation?: string;
  matched_skills?: any[];
  missing_skills?: any[];
  analysis_summary?: string;
  extracted_skills?: string[];
  target_role?: string;
}

/**
 * Save analysis results to candidate profile
 */
export async function saveAnalysisToProfile(analysisData: AnalysisUpdateData): Promise<boolean> {
  try {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      console.warn('⚠️ No auth token available');
      return false;
    }

    console.log('📤 Saving analysis to profile:', {
      readiness_score: analysisData.readiness_score,
      ai_explanation_length: analysisData.ai_explanation?.length || 0,
      matched_skills_count: analysisData.matched_skills?.length || 0,
      missing_skills_count: analysisData.missing_skills?.length || 0,
      missing_skills_with_gnn: analysisData.missing_skills?.filter((s: any) => s.P_gnn !== undefined).length || 0
    });

    const response = await fetch(`${API_URL}/candidate/me/analysis`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(analysisData),
    });

    if (!response.ok) {
      const error = await response.json();
      console.error('❌ Failed to save analysis:', error);
      return false;
    }

    const result = await response.json();
    console.log('✅ Analysis saved to profile:', result);
    
    toast({
      title: "Analysis Saved",
      description: "Your profile has been updated with latest analysis results.",
    });
    
    return true;
  } catch (error) {
    console.error('❌ Error saving analysis to profile:', error);
    return false;
  }
}

/**
 * Build analysis data object from pipeline results
 */
export function buildAnalysisData(results: any, targetRole?: string): AnalysisUpdateData {
  console.log('🔍 Building analysis data from results:', {
    has_skill_confidence_top: !!results.skill_confidence_top,
    has_skill_gap_top: !!results.skill_gap_top,
    has_explanation: !!results.explanation,
    has_explanation_text: !!results.explanation_text,
    readiness_score: results.readiness_score,
    targetRole
  });

  // Extract skills from matched skills
  const extractedSkills = results.skill_confidence_top?.map((skill: any) => skill.skill_name) || [];
  
  // Format matched skills with confidence
  const matchedSkills = results.skill_confidence_top?.map((skill: any) => ({
    skill: skill.skill_name,
    confidence: skill.confidence,
    evidence_count: skill.evidence_count || 1
  })) || [];
  
  // Format missing skills with ALL GNN fields (when available)
  const missingSkills = results.skill_gap_top?.map((skill: any) => ({
    skill: skill.skill_name,
    deficit: skill.deficit,
    importance: skill.importance,
    match_strength: skill.match_strength || 0,
    // GNN-specific fields (present when using hybrid/additive_gnn ranking)
    P_gnn: skill.P_gnn,
    final_score: skill.final_score,
    gap: skill.gap || skill.gap_magnitude,
    importance_norm: skill.importance_norm,
    reason: skill.reason,  // Human-readable GNN explanation
    category: skill.category,
    ranking_method: skill.ranking_method
  })) || [];
  
  // Get AI explanation text - check all possible sources
  const aiExplanation = results.explanation?.explanation_text ||  // From explainer service
                       results.explanation?.explanation ||       // Alternate format
                       results.explanation?.text ||               // Alternate format
                       results.explanation_text ||                // Direct property
                       null;
  
  console.log('🔍 AI Explanation extraction:', {
    has_explanation_object: !!results.explanation,
    explanation_keys: results.explanation ? Object.keys(results.explanation) : [],
    has_explanation_text_property: !!results.explanation?.explanation_text,
    extracted_length: aiExplanation?.length || 0,
    extracted_preview: aiExplanation ? aiExplanation.substring(0, 100) + '...' : 'NULL'
  });
  
  console.log('📊 Analysis data built:', {
    readiness_score: Math.round((results.readiness_score || 0) * 100),
    matched_skills: matchedSkills.length,
    missing_skills: missingSkills.length,
    missing_skills_with_gnn: missingSkills.filter((s: any) => s.P_gnn !== undefined).length,
    ai_explanation_chars: aiExplanation?.length || 0
  });

  // Generate summary
  const readinessScore = Math.round((results.readiness_score || 0) * 100);
  const matchedCount = matchedSkills.length;
  const missingCount = missingSkills.length;
  
  const analysisSummary = `Analyzed for ${targetRole || results.roleLabel || 'target role'}. ` +
    `Readiness: ${readinessScore}%. ` +
    `${matchedCount} skills matched, ${missingCount} skills to improve.`;
  
  return {
    readiness_score: readinessScore,
    skill_gap_index: results.skill_gap_index,
    ai_explanation: aiExplanation,
    matched_skills: matchedSkills,
    missing_skills: missingSkills,
    analysis_summary: analysisSummary,
    extracted_skills: extractedSkills,
    target_role: targetRole || results.roleLabel
  };
}
