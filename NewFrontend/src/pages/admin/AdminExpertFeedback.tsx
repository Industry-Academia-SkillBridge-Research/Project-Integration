import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, CheckCircle2, ClipboardCheck, Loader2, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { parseResponse } from "@/lib/parsers";
import { toast } from "sonner";

const EXPERT_API_URL = import.meta.env.VITE_THISARAVI_API_URL || "http://localhost:8010";

interface UnreviewedOutput {
  output_id?: string;
  timestamp?: string;
  model_provider?: string;
  prompt_version?: string;
  model_input?: {
    student_name?: string;
    job_data?: {
      target_job_role?: string;
    };
    student_data?: {
      demographics?: string;
    };
  };
  model_output?: string;
}

interface FeedbackStatus {
  total_outputs: number;
  reviewed_outputs: number;
  unreviewed_outputs: number;
  review_coverage_percent: number;
}

interface FeedbackDraft {
  reviewer_id: string;
  free_text_comments: string;
  ratings: {
    skill_gap_accuracy: number;
    project_relevance: number;
    tech_stack_appropriateness: number;
    implementation_step_quality: number;
    overall_quality: number;
  };
}

const initialStatus: FeedbackStatus = {
  total_outputs: 0,
  reviewed_outputs: 0,
  unreviewed_outputs: 0,
  review_coverage_percent: 0,
};

const defaultDraft: FeedbackDraft = {
  reviewer_id: "",
  free_text_comments: "",
  ratings: {
    skill_gap_accuracy: 3,
    project_relevance: 3,
    tech_stack_appropriateness: 3,
    implementation_step_quality: 3,
    overall_quality: 3,
  },
};

const ratingFields: Array<{ key: keyof FeedbackDraft["ratings"]; label: string }> = [
  { key: "skill_gap_accuracy", label: "Skill Gap Accuracy" },
  { key: "project_relevance", label: "Project Relevance" },
  { key: "tech_stack_appropriateness", label: "Tech Stack Appropriateness" },
  { key: "implementation_step_quality", label: "Implementation Step Quality" },
  { key: "overall_quality", label: "Overall Quality" },
];

function formatDate(value?: string) {
  if (!value) return "N/A";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

function resolveStudentName(item: UnreviewedOutput) {
  return item.model_input?.student_name || item.model_input?.student_data?.demographics || "Unknown";
}

function resolveTargetRole(item: UnreviewedOutput) {
  return item.model_input?.job_data?.target_job_role || "Unknown Role";
}

export default function AdminExpertFeedback() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<FeedbackStatus>(initialStatus);
  const [outputs, setOutputs] = useState<UnreviewedOutput[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedIds, setExpandedIds] = useState<Record<string, boolean>>({});
  const [drafts, setDrafts] = useState<Record<string, FeedbackDraft>>({});
  const [submittingId, setSubmittingId] = useState<string | null>(null);

  const getOutputId = (item: UnreviewedOutput, index: number) => item.output_id || `row-${index}`;

  const ensureDraft = (outputId: string) => {
    setDrafts((prev) => {
      if (prev[outputId]) return prev;
      return { ...prev, [outputId]: { ...defaultDraft, ratings: { ...defaultDraft.ratings } } };
    });
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [statusResponse, outputsResponse] = await Promise.all([
        fetch(`${EXPERT_API_URL}/feedback-status`),
        fetch(`${EXPERT_API_URL}/unreviewed-outputs`),
      ]);

      if (!statusResponse.ok) {
        throw new Error("Failed to fetch feedback status");
      }
      if (!outputsResponse.ok) {
        throw new Error("Failed to fetch unreviewed outputs");
      }

      const statusData = await statusResponse.json();
      const outputsData = await outputsResponse.json();
      const list: UnreviewedOutput[] = Array.isArray(outputsData) ? outputsData : [];

      const reviewedOutputs = Number(statusData.reviewed_outputs ?? statusData.total_feedback ?? 0);
      const unreviewedOutputs = Number(statusData.unreviewed_outputs ?? list.length ?? 0);
      const totalOutputs = Number(statusData.total_outputs ?? (reviewedOutputs + unreviewedOutputs));
      const coveragePercent =
        Number(statusData.review_coverage_percent) ||
        (totalOutputs > 0 ? (reviewedOutputs / totalOutputs) * 100 : 0);

      setStatus({
        total_outputs: totalOutputs,
        reviewed_outputs: reviewedOutputs,
        unreviewed_outputs: unreviewedOutputs,
        review_coverage_percent: coveragePercent,
      });
      setOutputs(list);

      setDrafts((prev) => {
        const next = { ...prev };
        list.forEach((item, index) => {
          const id = getOutputId(item, index);
          if (!next[id]) {
            next[id] = { ...defaultDraft, ratings: { ...defaultDraft.ratings } };
          }
        });
        return next;
      });
    } catch (error) {
      console.error("Failed to load expert feedback data:", error);
      toast.error("Unable to load expert feedback data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const orderedUnreviewed = useMemo(() => {
    return [...outputs].sort((a, b) => {
      const ta = a.timestamp ? new Date(a.timestamp).getTime() : 0;
      const tb = b.timestamp ? new Date(b.timestamp).getTime() : 0;
      return tb - ta;
    });
  }, [outputs]);

  const toggleExpanded = (outputId: string) => {
    ensureDraft(outputId);
    setExpandedIds((prev) => ({ ...prev, [outputId]: !prev[outputId] }));
  };

  const updateDraft = (outputId: string, patch: Partial<FeedbackDraft>) => {
    setDrafts((prev) => ({
      ...prev,
      [outputId]: {
        ...(prev[outputId] || { ...defaultDraft, ratings: { ...defaultDraft.ratings } }),
        ...patch,
        ratings: {
          ...((prev[outputId] || defaultDraft).ratings || defaultDraft.ratings),
          ...(patch.ratings || {}),
        },
      },
    }));
  };

  const submitFeedback = async (item: UnreviewedOutput, outputId: string) => {
    const draft = drafts[outputId] || defaultDraft;
    if (!draft.free_text_comments.trim()) {
      toast.error("Please add feedback comments before submitting");
      return;
    }

    setSubmittingId(outputId);
    try {
      const payload = {
        model_input: item.model_input || {},
        model_output: item.model_output || "",
        model_provider: item.model_provider || "ollama",
        ratings: draft.ratings,
        free_text_comments: draft.free_text_comments.trim(),
        reviewer_id: draft.reviewer_id.trim() || null,
        prompt_version: item.prompt_version || "v2_base",
      };

      const response = await fetch(`${EXPERT_API_URL}/submit-feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to submit feedback");
      }

      toast.success("Feedback submitted successfully");
      await loadData();
    } catch (error: any) {
      console.error("Failed to submit feedback:", error);
      toast.error(error.message || "Unable to submit feedback");
    } finally {
      setSubmittingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Button
            variant="outline"
            onClick={() => navigate("/admin/dashboard")}
            className="border-slate-700 hover:bg-slate-800 text-slate-300"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>

          <Button
            variant="outline"
            onClick={loadData}
            className="border-slate-700 hover:bg-slate-800 text-slate-300"
          >
            <RefreshCcw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <ClipboardCheck className="w-5 h-5 text-cyan-400" />
              Expert Feedback Queue
            </CardTitle>
            <CardDescription className="text-slate-400">
              Review coverage and pending model outputs from the expert workflow.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="py-8 flex justify-center">
                <Loader2 className="w-7 h-7 text-cyan-400 animate-spin" />
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="bg-slate-950/70 border-slate-800">
                  <CardContent className="pt-5">
                    <p className="text-xs text-slate-400">Total Outputs</p>
                    <p className="text-2xl font-bold text-white">{status.total_outputs}</p>
                  </CardContent>
                </Card>
                <Card className="bg-slate-950/70 border-slate-800">
                  <CardContent className="pt-5">
                    <p className="text-xs text-slate-400">Reviewed</p>
                    <p className="text-2xl font-bold text-emerald-400">{status.reviewed_outputs}</p>
                  </CardContent>
                </Card>
                <Card className="bg-slate-950/70 border-slate-800">
                  <CardContent className="pt-5">
                    <p className="text-xs text-slate-400">Awaiting Review</p>
                    <p className="text-2xl font-bold text-amber-400">{status.unreviewed_outputs}</p>
                  </CardContent>
                </Card>
                <Card className="bg-slate-950/70 border-slate-800">
                  <CardContent className="pt-5">
                    <p className="text-xs text-slate-400">Coverage</p>
                    <p className="text-2xl font-bold text-cyan-400">{status.review_coverage_percent.toFixed(1)}%</p>
                  </CardContent>
                </Card>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white">Unreviewed Analysis Queue</CardTitle>
            <CardDescription className="text-slate-400">
              Analysis is shown partially by default. Open each card to inspect full output and submit feedback.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <div className="py-6 flex justify-center">
                <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
              </div>
            ) : orderedUnreviewed.length === 0 ? (
              <p className="text-slate-400">No pending outputs. Everything is reviewed.</p>
            ) : (
              orderedUnreviewed.map((item, index) => {
                const outputId = getOutputId(item, index);
                const parsed = parseResponse(item.model_output || "");
                const analysisPreview = (parsed.gap_analysis.analysis_summary || item.model_output || "")
                  .replace(/\s+/g, " ")
                  .trim();
                const draft = drafts[outputId] || defaultDraft;
                const isExpanded = !!expandedIds[outputId];

                return (
                  <div key={outputId} className="rounded-lg border border-slate-800 bg-slate-950/60 p-4 space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="text-white font-semibold">{resolveTargetRole(item)}</p>
                        <p className="text-xs text-slate-400">{resolveStudentName(item)}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="border-slate-700 text-slate-300">
                          {item.model_provider || "unknown"}
                        </Badge>
                        {item.prompt_version && (
                          <Badge variant="secondary" className="bg-slate-800 text-slate-200">
                            {item.prompt_version}
                          </Badge>
                        )}
                        <Badge className="bg-cyan-500/20 text-cyan-300 border-cyan-500/30">
                          Match: {parsed.gap_analysis.match_percentage || 0}%
                        </Badge>
                      </div>
                    </div>

                    <p className="text-xs text-slate-400">{formatDate(item.timestamp)}</p>

                    {!isExpanded ? (
                      <p className="text-sm text-slate-300 line-clamp-3">
                        {analysisPreview || "No output text available"}
                      </p>
                    ) : (
                      <div className="rounded-md border border-slate-800 bg-slate-900/50 p-4 space-y-4">
                        <div>
                          <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Full Analysis</p>
                          <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
                            {parsed.gap_analysis.analysis_summary || "No analysis summary found"}
                          </p>
                        </div>

                        {parsed.gap_analysis.missing_skills.length > 0 && (
                          <div>
                            <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Missing Skills</p>
                            <div className="flex flex-wrap gap-2">
                              {parsed.gap_analysis.missing_skills.map((skill, skillIdx) => (
                                <Badge key={`${outputId}-skill-${skillIdx}`} variant="outline" className="border-amber-600/40 text-amber-300">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        <div>
                          <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">Project Recommendation</p>
                          <p className="text-white font-medium mb-1">{parsed.project_recommendation.project_title || "N/A"}</p>
                          <p className="text-sm text-slate-300 mb-2">{parsed.project_recommendation.objective || "N/A"}</p>
                          {parsed.project_recommendation.implementation_steps.length > 0 && (
                            <ol className="list-decimal list-inside text-sm text-slate-300 space-y-1">
                              {parsed.project_recommendation.implementation_steps.map((step, stepIdx) => (
                                <li key={`${outputId}-step-${stepIdx}`}>{step}</li>
                              ))}
                            </ol>
                          )}
                        </div>

                        <details className="rounded-md border border-slate-800 bg-slate-950/50 p-3">
                          <summary className="cursor-pointer text-xs text-slate-300">View raw model output</summary>
                          <pre className="text-xs whitespace-pre-wrap text-slate-400 mt-3 max-h-64 overflow-auto">
                            {item.model_output || "No output text available"}
                          </pre>
                        </details>

                        <div className="rounded-md border border-emerald-700/40 bg-emerald-950/20 p-4 space-y-4">
                          <div className="flex items-center gap-2 text-emerald-300">
                            <CheckCircle2 className="w-4 h-4" />
                            <p className="text-sm font-medium">Submit Expert Feedback</p>
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {ratingFields.map((field) => (
                              <label key={`${outputId}-${field.key}`} className="text-sm text-slate-200 space-y-1 block">
                                <span>{field.label} ({draft.ratings[field.key]}/5)</span>
                                <input
                                  type="range"
                                  min={1}
                                  max={5}
                                  step={1}
                                  value={draft.ratings[field.key]}
                                  onChange={(e) =>
                                    updateDraft(outputId, {
                                      ratings: {
                                        ...draft.ratings,
                                        [field.key]: Number(e.target.value),
                                      },
                                    })
                                  }
                                  className="w-full accent-cyan-400"
                                />
                              </label>
                            ))}
                          </div>

                          <div className="space-y-1">
                            <p className="text-xs text-slate-400">Reviewer ID (optional)</p>
                            <Input
                              value={draft.reviewer_id}
                              onChange={(e) => updateDraft(outputId, { reviewer_id: e.target.value })}
                              placeholder="e.g. expert_01"
                              className="bg-slate-900/70 border-slate-700 text-slate-200"
                            />
                          </div>

                          <div className="space-y-1">
                            <p className="text-xs text-slate-400">Feedback Comments</p>
                            <Textarea
                              value={draft.free_text_comments}
                              onChange={(e) => updateDraft(outputId, { free_text_comments: e.target.value })}
                              placeholder="Write qualitative feedback on the output quality, gaps, and recommendations"
                              className="min-h-24 bg-slate-900/70 border-slate-700 text-slate-200"
                            />
                          </div>

                          <div className="flex justify-end">
                            <Button
                              onClick={() => submitFeedback(item, outputId)}
                              disabled={submittingId === outputId}
                              className="bg-emerald-600 hover:bg-emerald-700"
                            >
                              {submittingId === outputId ? "Submitting..." : "Submit Feedback"}
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}

                    <Button
                      variant="outline"
                      onClick={() => toggleExpanded(outputId)}
                      className="border-slate-700 text-slate-300 hover:bg-slate-800"
                    >
                      {isExpanded ? "Hide Full Analysis" : "View Full Analysis + Add Feedback"}
                    </Button>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
