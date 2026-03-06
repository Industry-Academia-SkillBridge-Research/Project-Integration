import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { CheckCircle2, Loader2, Circle, AlertTriangle } from "lucide-react";
import { runAgentPipeline, runAgentPipelineFromPDF } from "@/services/agentService";
import { analyzeJobGap } from "@/services/jobGapService";
import { generateExplanation, buildExplainerPayload } from "@/services/explainerService";
import { saveAnalysisToProfile, buildAnalysisData } from "@/services/profileService";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "@/hooks/use-toast";

interface PipelineStage {
  id: string;
  label: string;
  description: string;
  gradient: string;
  estimatedDuration: number;
}

const pipelineStages: PipelineStage[] = [
  {
    id: "extracting",
    label: "Extracting",
    description: "Parsing candidate profile and extracting key information",
    gradient: "pipeline-stage-1",
    estimatedDuration: 1500,
  },
  {
    id: "normalizing",
    label: "Normalizing",
    description: "Standardizing skills and experience data",
    gradient: "pipeline-stage-2",
    estimatedDuration: 1200,
  },
  {
    id: "neo4j",
    label: "Writing to Neo4j",
    description: "Storing data in knowledge graph database",
    gradient: "pipeline-stage-3",
    estimatedDuration: 1800,
  },
  {
    id: "analyzing",
    label: "Analyzing Gaps",
    description: "Identifying skill gaps against target requirements",
    gradient: "pipeline-stage-4",
    estimatedDuration: 2000,
  },
  {
    id: "projects",
    label: "Project Relevance",
    description: "Analyzing project experience and relevance scores",
    gradient: "pipeline-stage-5",
    estimatedDuration: 1400,
  },
  {
    id: "explaining",
    label: "AI Explanation",
    description: "Generating intelligent insights and explanations",
    gradient: "pipeline-stage-6",
    estimatedDuration: 2500,
  },
];

const Pipeline = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { checkAuth } = useAuth();
  const [currentStage, setCurrentStage] = useState(0);
  const [completedStages, setCompletedStages] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);

  // Execute the actual API pipeline
  useEffect(() => {
    const runPipeline = async () => {
      try {
        const { type, profile, cvFile, roleKey, roleLabel, jobFile, storeInGraph } = location.state || {};
        
        if (!profile && !cvFile) {
          throw new Error("No profile data or CV file provided");
        }

        let gapResults;
        let projectData;
        let explanation;

        // Stage 1-4: Run Gap Analysis
        if (type === 'role-based') {
          if (!roleKey) throw new Error("No role selected");
          
          // Simulate progress through first 3 stages (extracting, normalizing, neo4j)
          for (let i = 0; i < 3; i++) {
            await new Promise(resolve => setTimeout(resolve, 300));
            setCompletedStages(prev => [...prev, pipelineStages[i].id]);
            setCurrentStage(i + 1);
          }

          // Stage 4: Analyzing (actual API call)
          if (cvFile) {
            // NEW: PDF upload path
            console.log(`🚀 Running agent pipeline from PDF: ${cvFile.name}`);
            gapResults = await runAgentPipelineFromPDF(cvFile, roleKey, 25, true);
            console.log("✅ PDF parsing and gap analysis complete:", gapResults);
          } else {
            // Original JSON path
            console.log(`🚀 Running agent pipeline for role: ${roleKey}`);
            gapResults = await runAgentPipeline(profile, roleKey, 25, true);
            console.log("✅ Gap analysis complete:", gapResults);
          }
          
          setCompletedStages(prev => [...prev, pipelineStages[3].id]);
          setCurrentStage(4);

          // Stage 5: Project Relevance (already included in response)
          console.log(`📊 Project relevance score: ${gapResults.project_relevance_score || 0}`);
          setCompletedStages(prev => [...prev, pipelineStages[4].id]);
          setCurrentStage(5);

          // Stage 6: AI Explanation
          console.log(`🤖 Generating AI explanation...`);
          try {
            const explainerPayload = buildExplainerPayload(gapResults, 'role', roleKey, roleLabel);
            explanation = await generateExplanation(explainerPayload);
            console.log("✅ Explanation generated:", explanation);
            gapResults.explanation = explanation;
          } catch (err) {
            console.warn("⚠️ Explanation generation failed:", err);
            gapResults.explanation = null;
          }

          setCompletedStages(prev => [...prev, pipelineStages[5].id]);
          setCurrentStage(6);

          // Add metadata
          gapResults.roleLabel = roleLabel;
          gapResults.roleKey = roleKey;
          
        } else if (type === 'job-based') {
          if (!jobFile) throw new Error("No job description file provided");
          
          // Simulate progress through first 3 stages
          for (let i = 0; i < 3; i++) {
            await new Promise(resolve => setTimeout(resolve, 300));
            setCompletedStages(prev => [...prev, pipelineStages[i].id]);
            setCurrentStage(i + 1);
          }

          // Stage 4: Job Gap Analysis
          console.log(`🚀 Running job-gap analysis...`);
          const jobGapData = await analyzeJobGap(
            JSON.stringify(profile),
            jobFile,
            storeInGraph || false,
            25
          );
          console.log("✅ Job gap analysis complete:", jobGapData);
          
          // Normalize job-based response to match role-based format
          gapResults = {
            candidate_id: jobGapData.candidate_id,
            job_id: jobGapData.job_id,
            readiness_score: jobGapData.readiness,
            skill_gap_index: jobGapData.skill_gap_index,
            // Convert matched_skills to skill_confidence_top format
            skill_confidence_top: (jobGapData.matched_skills || []).map((s: any) => ({
              skill_name: s.skill,
              confidence: s.match_strength,
              evidence_count: 1
            })),
            // Convert missing_skills_ranked to skill_gap_top format
            skill_gap_top: (jobGapData.missing_skills_ranked || []).map((s: any) => ({
              skill_name: s.skill,
              deficit: s.deficit,
              importance: s.importance,
              match_strength: s.match_strength
            })),
            // Include XAI data from backend if available
            xai: jobGapData.xai,
            // Store explanation text if available
            explanation_text: jobGapData.explanation_text,
            candidate_upsert: jobGapData.candidate_upsert
          };
          
          setCompletedStages(prev => [...prev, pipelineStages[3].id]);
          setCurrentStage(4);

          // Skip project relevance for job-based
          setCompletedStages(prev => [...prev, pipelineStages[4].id]);
          setCurrentStage(5);

          // Stage 6: AI Explanation
          console.log(`🤖 Generating AI explanation...`);
          try {
            const explainerPayload = buildExplainerPayload(
              gapResults, 
              'job-gap', 
              'custom_job',
              jobGapData.job_title || 'Job Description'
            );
            explanation = await generateExplanation(explainerPayload);
            console.log("✅ Explanation generated:", explanation);
            gapResults.explanation = explanation;
          } catch (err) {
            console.warn("⚠️ Explanation generation failed:", err);
            // Use backend explanation text as fallback
            gapResults.explanation = jobGapData.explanation_text ? {
              explanation: jobGapData.explanation_text,
              text: jobGapData.explanation_text
            } : null;
          }

          setCompletedStages(prev => [...prev, pipelineStages[5].id]);
          setCurrentStage(6);

          // Add metadata
          gapResults.roleLabel = jobGapData.job_title || "Custom Job Role";
          gapResults.roleKey = "custom_job";
        }

        setResults(gapResults);

        // Save analysis results to profile
        try {
          const analysisData = buildAnalysisData(gapResults, roleLabel ||gapResults.roleLabel);
          await saveAnalysisToProfile(analysisData);
          console.log("✅ Analysis saved to candidate profile");
          
          // Refresh user profile data to include the new analysis
          await checkAuth();
          console.log("✅ Profile data refreshed");
        } catch (saveErr) {
          console.warn("⚠️ Could not save analysis to profile:", saveErr);
          // Continue even if save fails - analysis is still available
        }

        // Navigate to results page after a short delay
        setTimeout(() => {
          navigate('/skill-gap', { state: { results: gapResults, type } });
        }, 800);

      } catch (err: any) {
        console.error("❌ Pipeline error:", err);
        setError(err.message || "An error occurred during analysis");
        toast({
          title: "Analysis Failed",
          description: err.message || "An error occurred during analysis",
          variant: "destructive",
        });
      }
    };

    runPipeline();
  }, [location.state, navigate]);

  const getStageStatus = (index: number) => {
    if (error) return index <= currentStage ? "error" : "pending";
    if (completedStages.includes(pipelineStages[index].id)) return "completed";
    if (index === currentStage) return "active";
    return "pending";
  };

  return (
    <div className="min-h-screen bg-gradient-hero flex items-center justify-center">
      {/* Background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent/5 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
      </div>

      <div className="relative z-10 container mx-auto px-6 py-12 max-w-3xl">
        <div className="text-center mb-12 animate-fade-in">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            {error ? "Analysis Error" : "Running Agentic Pipeline"}
          </h1>
          <p className="text-muted-foreground">
            {error ? "Something went wrong during analysis" : "Processing your analysis request..."}
          </p>
        </div>

        <div className="space-y-4">
          {pipelineStages.map((stage, index) => {
            const status = getStageStatus(index);
            
            return (
              <div
                key={stage.id}
                className={`relative bg-gradient-card rounded-xl border p-6 shadow-card transition-all duration-500 ${
                  status === "active" 
                    ? "border-primary shadow-glow scale-[1.02]" 
                    : status === "completed"
                    ? "border-primary/50 opacity-80"
                    : status === "error"
                    ? "border-destructive/50 opacity-80"
                    : "border-border opacity-50"
                }`}
                style={{
                  animationDelay: `${index * 0.1}s`,
                }}
              >
                {/* Connection line */}
                {index < pipelineStages.length - 1 && (
                  <div className={`absolute left-10 top-full w-0.5 h-4 transition-colors duration-300 ${
                    completedStages.includes(stage.id) 
                      ? 'bg-primary' 
                      : status === "error"
                      ? 'bg-destructive'
                      : 'bg-border'
                  }`} />
                )}

                <div className="flex items-center gap-4">
                  {/* Status Icon */}
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    status === "completed" 
                      ? stage.gradient 
                      : status === "active"
                      ? stage.gradient + " animate-pulse"
                      : status === "error"
                      ? "bg-destructive"
                      : "bg-muted"
                  }`}>
                    {status === "completed" ? (
                      <CheckCircle2 className="w-5 h-5 text-white" />
                    ) : status === "active" ? (
                      <Loader2 className="w-5 h-5 text-white animate-spin" />
                    ) : status === "error" ? (
                      <AlertTriangle className="w-5 h-5 text-white" />
                    ) : (
                      <Circle className="w-5 h-5 text-muted-foreground" />
                    )}
                  </div>

                  {/* Stage Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className={`font-semibold ${
                        status === "pending" ? "text-muted-foreground" : "text-foreground"
                      }`}>
                        {stage.label}
                      </h3>
                      {status === "active" && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-primary/20 text-primary">
                          Processing...
                        </span>
                      )}
                      {status === "error" && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-destructive/20 text-destructive">
                          Failed
                        </span>
                      )}
                    </div>
                    <p className={`text-sm ${
                      status === "pending" ? "text-muted-foreground/60" : "text-muted-foreground"
                    }`}>
                      {stage.description}
                    </p>
                  </div>
                </div>

                {/* Progress bar for active stage */}
                {status === "active" && !error && (
                  <div className="mt-4 h-1 bg-muted rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${stage.gradient} rounded-full animate-pulse`}
                      style={{ width: '70%' }}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Completion or Error Message */}
        {currentStage >= pipelineStages.length && !error && (
          <div className="text-center mt-8 animate-scale-in">
            <div className="inline-flex items-center gap-2 px-6 py-3 rounded-full bg-primary/20 text-primary">
              <CheckCircle2 className="w-5 h-5" />
              <span className="font-medium">Analysis Complete! Redirecting...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="text-center mt-8 animate-scale-in">
            <div className="inline-flex flex-col items-center gap-4 px-6 py-4 rounded-xl bg-destructive/10 border border-destructive/30">
              <div className="flex items-center gap-2 text-destructive">
                <AlertTriangle className="w-5 h-5" />
                <span className="font-medium">Analysis Failed</span>
              </div>
              <p className="text-sm text-muted-foreground max-w-md">{error}</p>
              <button
                onClick={() => navigate('/analysis')}
                className="mt-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
              >
                Return to Analysis
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Pipeline;
