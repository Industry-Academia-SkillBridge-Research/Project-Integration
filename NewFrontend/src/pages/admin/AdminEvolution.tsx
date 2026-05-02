import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Bot, Loader2, RefreshCcw, Sparkles, UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";

const EXPERT_API_URL = import.meta.env.VITE_THISARAVI_API_URL || "http://localhost:8010";

type Provider = "ollama" | "gemini";

type GenerationMode = "v1" | "v2";

interface FeedbackStatus {
  total_outputs: number;
  reviewed_outputs: number;
  unreviewed_outputs: number;
  review_coverage_percent: number;
}

interface CurrentPrompt {
  prompt: string;
  version: string;
}

interface PatternReport {
  report_id: string;
  timestamp?: string;
  total_feedback_analyzed?: number;
  low_scoring_dimensions?: string[];
  actionable_insights?: string[];
}

interface PromptEvolution {
  evolution_id: string;
  timestamp?: string;
  parent_prompt_version?: string;
  new_prompt_version?: string;
  pattern_report_id?: string;
  change_summary?: string;
}

interface DatasetItem {
  filename: string;
  entry_count: number;
  upload_failed?: boolean;
  upload_failure_reason?: string | null;
}

const emptyStatus: FeedbackStatus = {
  total_outputs: 0,
  reviewed_outputs: 0,
  unreviewed_outputs: 0,
  review_coverage_percent: 0,
};

function formatDate(value?: string) {
  if (!value) return "N/A";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export default function AdminEvolution() {
  const navigate = useNavigate();

  const [provider, setProvider] = useState<Provider>("ollama");
  const [status, setStatus] = useState<FeedbackStatus>(emptyStatus);
  const [promptData, setPromptData] = useState<CurrentPrompt | null>(null);
  const [reports, setReports] = useState<PatternReport[]>([]);
  const [evolutions, setEvolutions] = useState<PromptEvolution[]>([]);
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);

  const [selectedReportId, setSelectedReportId] = useState<string>("");
  const [selectedEvolutionId, setSelectedEvolutionId] = useState<string>("");
  const [previewDiff, setPreviewDiff] = useState<string>("");

  const [targetCount, setTargetCount] = useState<number>(200);
  const [generationMode, setGenerationMode] = useState<GenerationMode>("v2");
  const [repoId, setRepoId] = useState<string>("");

  const [loading, setLoading] = useState(true);
  const [analysisRunning, setAnalysisRunning] = useState(false);
  const [previewRunning, setPreviewRunning] = useState(false);
  const [applyRunning, setApplyRunning] = useState(false);
  const [regenRunning, setRegenRunning] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [uploadingDataset, setUploadingDataset] = useState<string | null>(null);

  const loadData = async (softRefresh = false) => {
    if (softRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [statusRes, unreviewedRes, promptRes, reportRes, evolutionRes, datasetRes] = await Promise.all([
        fetch(`${EXPERT_API_URL}/feedback-status`),
        fetch(`${EXPERT_API_URL}/unreviewed-outputs`),
        fetch(`${EXPERT_API_URL}/current-prompt`),
        fetch(`${EXPERT_API_URL}/pattern-reports`),
        fetch(`${EXPERT_API_URL}/prompt-evolutions`),
        fetch(`${EXPERT_API_URL}/list-datasets`),
      ]);

      if (!statusRes.ok || !unreviewedRes.ok || !promptRes.ok || !reportRes.ok || !evolutionRes.ok || !datasetRes.ok) {
        throw new Error("Failed to fetch evolution data");
      }

      const statusJson = await statusRes.json();
      const unreviewedJson = await unreviewedRes.json();
      const promptJson = await promptRes.json();
      const reportJson = await reportRes.json();
      const evolutionJson = await evolutionRes.json();
      const datasetJson = await datasetRes.json();

      const reportList: PatternReport[] = Array.isArray(reportJson) ? reportJson : [];
      const evolutionList: PromptEvolution[] = Array.isArray(evolutionJson) ? evolutionJson : [];
      const datasetList: DatasetItem[] = Array.isArray(datasetJson?.datasets) ? datasetJson.datasets : [];
      const unreviewedOutputs = Array.isArray(unreviewedJson) ? unreviewedJson.length : 0;
      const reviewedOutputs = Number(statusJson.reviewed_outputs ?? statusJson.total_feedback ?? 0);
      const totalOutputs = Number(statusJson.total_outputs ?? (reviewedOutputs + unreviewedOutputs));
      const coveragePercent =
        Number(statusJson.review_coverage_percent) ||
        (totalOutputs > 0 ? (reviewedOutputs / totalOutputs) * 100 : 0);

      setStatus({
        total_outputs: totalOutputs,
        reviewed_outputs: reviewedOutputs,
        unreviewed_outputs: unreviewedOutputs,
        review_coverage_percent: coveragePercent,
      });
      setPromptData({
        prompt: promptJson.prompt || "",
        version: promptJson.version || "unknown",
      });
      setReports(reportList);
      setEvolutions(evolutionList);
      setDatasets(datasetList);

      if (!selectedReportId && reportList.length > 0) {
        setSelectedReportId(reportList[0].report_id);
      }

      if (!selectedEvolutionId && evolutionList.length > 0) {
        setSelectedEvolutionId(evolutionList[evolutionList.length - 1].evolution_id);
      }
    } catch (error) {
      console.error("Failed to load evolution data:", error);
      toast.error("Unable to load evolution data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const runAnalysis = async () => {
    setAnalysisRunning(true);
    try {
      const response = await fetch(`${EXPERT_API_URL}/run-analysis`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Analysis failed");
      }

      toast.success("Pattern analysis completed");
      await loadData(true);
    } catch (error: any) {
      console.error("Failed to run analysis:", error);
      toast.error(error.message || "Unable to run analysis");
    } finally {
      setAnalysisRunning(false);
    }
  };

  const previewEvolution = async () => {
    if (!selectedReportId) {
      toast.error("Select a pattern report first");
      return;
    }

    setPreviewRunning(true);
    try {
      const response = await fetch(`${EXPERT_API_URL}/preview-evolution`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: selectedReportId, provider }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Preview failed");
      }

      const data = await response.json();
      setPreviewDiff(data.diff || "No diff returned");
      toast.success("Evolution preview generated");
    } catch (error: any) {
      console.error("Failed to preview evolution:", error);
      toast.error(error.message || "Unable to preview evolution");
    } finally {
      setPreviewRunning(false);
    }
  };

  const applyEvolution = async () => {
    if (!selectedReportId) {
      toast.error("Select a pattern report first");
      return;
    }

    setApplyRunning(true);
    try {
      const response = await fetch(`${EXPERT_API_URL}/apply-evolution`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: selectedReportId, provider }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Apply evolution failed");
      }

      const data = await response.json();
      toast.success(`Evolution applied: ${data.new_prompt_version || "new prompt"}`);
      await loadData(true);
    } catch (error: any) {
      console.error("Failed to apply evolution:", error);
      toast.error(error.message || "Unable to apply evolution");
    } finally {
      setApplyRunning(false);
    }
  };

  const runRegeneration = async () => {
    if (!selectedEvolutionId) {
      toast.error("Select an evolution first");
      return;
    }

    setRegenRunning(true);
    try {
      const response = await fetch(`${EXPERT_API_URL}/run-regeneration`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          evolution_id: selectedEvolutionId,
          provider,
          target_count: targetCount,
          generation_mode: generationMode,
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Regeneration failed");
      }

      const data = await response.json();
      toast.success(`Dataset regenerated: ${data.output_path || "completed"}`);
      await loadData(true);
    } catch (error: any) {
      console.error("Failed to run regeneration:", error);
      toast.error(error.message || "Unable to run regeneration");
    } finally {
      setRegenRunning(false);
    }
  };

  const uploadToHuggingFace = async (filename: string) => {
    setUploadingDataset(filename);
    try {
      const response = await fetch(`${EXPERT_API_URL}/upload-to-hf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename, repo_id: repoId.trim() || null }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Upload failed");
      }

      toast.success(`Uploaded ${filename} to Hugging Face`);
    } catch (error: any) {
      console.error("Failed to upload dataset:", error);
      toast.error(error.message || "Unable to upload dataset");
    } finally {
      setUploadingDataset(null);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const selectedReport = useMemo(
    () => reports.find((r) => r.report_id === selectedReportId) || null,
    [reports, selectedReportId],
  );

  const failedDatasets = useMemo(
    () => datasets.filter((dataset) => dataset.upload_failed),
    [datasets],
  );

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

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => loadData(true)}
              disabled={refreshing}
              className="border-slate-700 text-slate-300 hover:bg-slate-800"
            >
              {refreshing ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCcw className="w-4 h-4 mr-2" />}
              Refresh
            </Button>
          </div>
        </div>

        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Bot className="w-5 h-5 text-cyan-400" />
              Evolution Overview
            </CardTitle>
            <CardDescription className="text-slate-400">
              End-to-end controls for expert feedback analysis, prompt evolution, and dataset regeneration.
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
                    <p className="text-xs text-slate-400">Awaiting</p>
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
            <CardTitle className="text-white">Analysis + Evolution Actions</CardTitle>
            <CardDescription className="text-slate-400">
              Run pattern analysis, preview evolution diff, then apply it.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant={provider === "ollama" ? "default" : "outline"}
                onClick={() => setProvider("ollama")}
                className={provider === "ollama" ? "bg-cyan-600 hover:bg-cyan-700" : "border-slate-700 text-slate-300"}
              >
                Ollama
              </Button>
              <Button
                variant={provider === "gemini" ? "default" : "outline"}
                onClick={() => setProvider("gemini")}
                className={provider === "gemini" ? "bg-cyan-600 hover:bg-cyan-700" : "border-slate-700 text-slate-300"}
              >
                Gemini
              </Button>
              <Button
                onClick={runAnalysis}
                disabled={analysisRunning}
                className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700"
              >
                {analysisRunning ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Sparkles className="w-4 h-4 mr-2" />}
                Run Analysis
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
              <div className="space-y-1 md:col-span-2">
                <Label className="text-slate-300">Pattern Report</Label>
                <Select value={selectedReportId} onValueChange={setSelectedReportId}>
                  <SelectTrigger className="bg-slate-900/70 border-slate-700 text-slate-200">
                    <SelectValue placeholder="Select report" />
                  </SelectTrigger>
                  <SelectContent>
                    {reports.map((report) => (
                      <SelectItem key={report.report_id} value={report.report_id}>
                        {report.report_id} • {formatDate(report.timestamp)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={previewEvolution} disabled={previewRunning} className="border-slate-700 text-slate-300 hover:bg-slate-800">
                  {previewRunning ? "Previewing..." : "Preview"}
                </Button>
                <Button onClick={applyEvolution} disabled={applyRunning} className="bg-emerald-600 hover:bg-emerald-700">
                  {applyRunning ? "Applying..." : "Apply"}
                </Button>
              </div>
            </div>

            {selectedReport && (
              <div className="rounded-md border border-slate-800 bg-slate-950/60 p-3 text-xs text-slate-300 space-y-2">
                <p className="font-semibold text-slate-200">Selected report snapshot</p>
                <p>Total feedback analyzed: {selectedReport.total_feedback_analyzed ?? "N/A"}</p>
                {selectedReport.low_scoring_dimensions && selectedReport.low_scoring_dimensions.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {selectedReport.low_scoring_dimensions.map((dimension) => (
                      <Badge key={dimension} variant="outline" className="border-amber-700/40 text-amber-300">{dimension}</Badge>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="space-y-1">
              <Label className="text-slate-300">Evolution Diff Preview</Label>
              <Textarea
                value={previewDiff}
                onChange={(e) => setPreviewDiff(e.target.value)}
                placeholder="Preview diff will appear here"
                className="min-h-40 bg-slate-900/70 border-slate-700 text-slate-200"
              />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white">Current Prompt</CardTitle>
            <CardDescription className="text-slate-400">
              Active prompt version currently used by the expert pipeline.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Badge variant="secondary" className="bg-slate-800 text-slate-200">
              Version: {promptData?.version || "N/A"}
            </Badge>
            <div className="rounded-md border border-slate-800 bg-slate-950/70 p-4 max-h-64 overflow-auto">
              <p className="text-sm text-slate-300 whitespace-pre-wrap">
                {promptData?.prompt || "Prompt not available"}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white">Regeneration + Datasets</CardTitle>
            <CardDescription className="text-slate-400">
              Regenerate datasets from an evolution and upload generated files to Hugging Face.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
              <div className="space-y-1 md:col-span-2">
                <Label className="text-slate-300">Evolution</Label>
                <Select value={selectedEvolutionId} onValueChange={setSelectedEvolutionId}>
                  <SelectTrigger className="bg-slate-900/70 border-slate-700 text-slate-200">
                    <SelectValue placeholder="Select evolution" />
                  </SelectTrigger>
                  <SelectContent>
                    {evolutions.map((evo) => (
                      <SelectItem key={evo.evolution_id} value={evo.evolution_id}>
                        {evo.evolution_id} • {evo.new_prompt_version || "N/A"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-slate-300">Target Count</Label>
                <Input
                  type="number"
                  min={1}
                  value={targetCount}
                  onChange={(e) => setTargetCount(Number(e.target.value) || 1)}
                  className="bg-slate-900/70 border-slate-700 text-slate-200"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-slate-300">Generation Mode</Label>
                <Select value={generationMode} onValueChange={(value: GenerationMode) => setGenerationMode(value)}>
                  <SelectTrigger className="bg-slate-900/70 border-slate-700 text-slate-200">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="v1">v1</SelectItem>
                    <SelectItem value="v2">v2</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex justify-end">
              <Button onClick={runRegeneration} disabled={regenRunning} className="bg-indigo-600 hover:bg-indigo-700">
                {regenRunning ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                Run Regeneration
              </Button>
            </div>

            <div className="space-y-1">
              <Label className="text-slate-300">Hugging Face Repo ID (optional)</Label>
              <Input
                value={repoId}
                onChange={(e) => setRepoId(e.target.value)}
                placeholder="e.g. your-username/your-dataset"
                className="bg-slate-900/70 border-slate-700 text-slate-200"
              />
            </div>

            <div className="space-y-2">
              {failedDatasets.length === 0 ? (
                <p className="text-slate-400 text-sm">No failed dataset uploads found.</p>
              ) : (
                failedDatasets.map((dataset) => (
                  <div key={dataset.filename} className="rounded-md border border-slate-800 bg-slate-950/60 p-3 flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-sm text-white">{dataset.filename}</p>
                      <p className="text-xs text-slate-400">Entries: {dataset.entry_count}</p>
                      <p className="text-xs text-amber-300 mt-1">
                        Upload failed: {dataset.upload_failure_reason || "retry available"}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => uploadToHuggingFace(dataset.filename)}
                      disabled={uploadingDataset === dataset.filename}
                      className="border-slate-700 text-slate-300 hover:bg-slate-800"
                    >
                      {uploadingDataset === dataset.filename ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <UploadCloud className="w-4 h-4 mr-2" />
                      )}
                      Upload to HF
                    </Button>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
