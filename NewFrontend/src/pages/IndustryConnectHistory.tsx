import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown, Clock, CheckCircle2, Star, BookOpen } from 'lucide-react';
import { cn } from '@/lib/utils';
import PageHeader from '@/components/industryConnect/PageHeader';
import { fetchMyHistory } from '@/services/industryConnectService';
import { parseResponse } from '@/lib/parsers';
import { useAuth } from '@/contexts/AuthContext';
import type { HistoryEntry, FeedbackEntry } from '@/types/industryConnect';

/* ─── Helpers ───────────────────────────────────────────────────────────── */

function formatTimestamp(ts?: string): string {
  if (!ts) return '';
  try {
    return new Date(ts).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return ts;
  }
}

function ratingColor(value: number): string {
  if (value >= 4) return 'text-green-600';
  if (value >= 3) return 'text-yellow-600';
  return 'text-red-500';
}

/* ─── Sub-components ────────────────────────────────────────────────────── */

function ModelOutputDisplay({ rawOutput }: { rawOutput: string }) {
  const parsed = rawOutput ? parseResponse(rawOutput) : null;

  if (parsed && !parsed.error) {
    return (
      <div className="space-y-3 text-sm">
        <div className="flex items-center gap-3">
          <span className="text-muted-foreground text-xs uppercase tracking-wide">Match Score</span>
          <span className="text-2xl font-bold">{parsed.gap_analysis.match_percentage}%</span>
        </div>

        {parsed.gap_analysis.analysis_summary && (
          <p className="text-sm text-muted-foreground leading-relaxed">
            {parsed.gap_analysis.analysis_summary}
          </p>
        )}

        {parsed.gap_analysis.missing_skills.length > 0 && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1.5">Missing Skills</p>
            <div className="flex flex-wrap gap-1">
              {parsed.gap_analysis.missing_skills.map((s, i) => (
                <Badge key={i} variant="outline" className="text-xs">
                  {s}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <Separator />

        <div className="space-y-2">
          <p className="font-semibold">{parsed.project_recommendation.project_title}</p>
          {parsed.project_recommendation.objective && (
            <p className="text-muted-foreground italic text-xs">
              {parsed.project_recommendation.objective}
            </p>
          )}
          {parsed.project_recommendation.tech_stack.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Tech Stack</p>
              <div className="flex flex-wrap gap-1">
                {parsed.project_recommendation.tech_stack.map((t, i) => (
                  <Badge key={i} variant="secondary" className="text-xs">
                    {t}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          {parsed.project_recommendation.implementation_steps.length > 0 && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Implementation Steps</p>
              <ol className="list-decimal list-inside space-y-1 text-sm">
                {parsed.project_recommendation.implementation_steps.map((s, i) => (
                  <li key={i} className="leading-relaxed">{s}</li>
                ))}
              </ol>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <pre className="text-xs font-mono bg-muted/50 p-3 rounded-md overflow-auto max-h-64 whitespace-pre-wrap">
      {rawOutput.slice(0, 3000)}
    </pre>
  );
}

function FeedbackDisplay({ feedback }: { feedback: FeedbackEntry }) {
  const ratingLabels: [keyof typeof feedback.ratings, string][] = [
    ['skill_gap_accuracy', 'Skill Gap Accuracy'],
    ['project_relevance', 'Project Relevance'],
    ['tech_stack_appropriateness', 'Tech Stack'],
    ['implementation_step_quality', 'Implementation Steps'],
    ['overall_quality', 'Overall Quality'],
  ];

  return (
    <div className="rounded-md border border-green-200 bg-green-50 dark:bg-green-950/20 dark:border-green-800 p-4 space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-green-700 dark:text-green-400">
        <CheckCircle2 className="h-4 w-4" />
        Expert Feedback
        {feedback.timestamp && (
          <span className="text-xs font-normal text-muted-foreground ml-auto">
            {formatTimestamp(feedback.timestamp)}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {ratingLabels.map(([key, label]) => {
          const value = feedback.ratings?.[key] ?? 0;
          return (
            <div key={key} className="flex flex-col">
              <span className="text-[10px] text-muted-foreground">{label}</span>
              <div className="flex items-center gap-1 mt-0.5">
                <Star className={cn('h-3 w-3 fill-current', ratingColor(value))} />
                <span className={cn('text-sm font-semibold', ratingColor(value))}>
                  {value}/5
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {feedback.free_text_comments && (
        <>
          <Separator className="bg-green-200 dark:bg-green-800" />
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Expert Comments</p>
            <p className="text-sm leading-relaxed">{feedback.free_text_comments}</p>
          </div>
        </>
      )}

      {feedback.reviewer_id && (
        <p className="text-[10px] text-muted-foreground">
          Reviewed by: {feedback.reviewer_id}
          {feedback.prompt_version && ` · Prompt: ${feedback.prompt_version}`}
        </p>
      )}
    </div>
  );
}

function HistoryCard({ entry, index }: { entry: HistoryEntry; index: number }) {
  const [open, setOpen] = useState(false);
  const { output, feedback } = entry;

  const inp = output.model_input || {};
  const jobData = (inp.job_data || {}) as Record<string, unknown>;
  const targetRole = (jobData.target_job_role as string) || 'Unknown Role';

  let matchPct: number | null = null;
  try {
    const parsed = parseResponse(output.model_output);
    if (!parsed.error) matchPct = parsed.gap_analysis.match_percentage;
  } catch { /* ignore */ }

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card className={cn('transition-all', open && 'ring-1 ring-primary/30')}>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer select-none pb-3 hover:bg-muted/30 rounded-t-xl transition-colors">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-sm font-bold">
                  {index + 1}
                </div>
                <div className="space-y-0.5">
                  <CardTitle className="text-base leading-tight">{targetRole}</CardTitle>
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatTimestamp(output.timestamp)}
                    </span>
                    {output.model_provider && (
                      <span className="capitalize">{output.model_provider}</span>
                    )}
                    {output.prompt_version && (
                      <span className="font-mono">{output.prompt_version}</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {matchPct !== null && (
                  <Badge
                    variant="secondary"
                    className={cn(
                      'text-xs',
                      matchPct >= 70 ? 'bg-green-100 text-green-700' :
                      matchPct >= 40 ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700',
                    )}
                  >
                    {matchPct}% match
                  </Badge>
                )}
                {feedback ? (
                  <Badge variant="outline" className="text-green-600 border-green-300 text-xs">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    Reviewed
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-muted-foreground text-xs">
                    No feedback yet
                  </Badge>
                )}
                <ChevronDown
                  className={cn(
                    'h-4 w-4 text-muted-foreground transition-transform',
                    open && 'rotate-180',
                  )}
                />
              </div>
            </div>
          </CardHeader>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <CardContent className="pt-0 pb-5 space-y-4">
            <Separator />
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
                Model Output
              </p>
              <ModelOutputDisplay rawOutput={output.model_output} />
            </div>
            {feedback && <FeedbackDisplay feedback={feedback} />}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

/* ─── Page ──────────────────────────────────────────────────────────────── */

export default function IndustryConnectHistory() {
  const { user } = useAuth();

  const {
    data: history = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['ic-history', user?.name],
    queryFn: () => fetchMyHistory(user?.name ?? ''),
    enabled: !!user?.name,
  });

  const reviewedCount = history.filter((h) => h.feedback !== null).length;

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <PageHeader
        title="My History"
        subtitle="View your past skill gap analyses and any expert feedback on them"
      />

      {history.length > 0 && (
        <div className="flex gap-6 mb-6 rounded-md border bg-muted/30 px-5 py-3 text-sm">
          <div>
            <span className="text-muted-foreground">Total analyses</span>
            <p className="text-xl font-bold leading-tight">{history.length}</p>
          </div>
          <Separator orientation="vertical" className="h-10 self-center" />
          <div>
            <span className="text-muted-foreground">With expert feedback</span>
            <p className="text-xl font-bold leading-tight text-green-600">{reviewedCount}</p>
          </div>
          <Separator orientation="vertical" className="h-10 self-center" />
          <div>
            <span className="text-muted-foreground">Awaiting review</span>
            <p className="text-xl font-bold leading-tight text-amber-600">
              {history.length - reviewedCount}
            </p>
          </div>
        </div>
      )}

      {isLoading && (
        <Card>
          <CardContent className="py-10 text-center text-muted-foreground">
            Loading your history…
          </CardContent>
        </Card>
      )}

      {error && (
        <div className="rounded-md bg-destructive/10 border border-destructive/20 p-4 text-sm text-destructive">
          {error instanceof Error ? error.message : 'Failed to load history.'}
        </div>
      )}

      {!isLoading && !error && history.length === 0 && (
        <Card>
          <CardContent className="py-14 flex flex-col items-center gap-3 text-center text-muted-foreground">
            <BookOpen className="h-10 w-10 opacity-30" />
            <p className="text-base font-medium">No analyses yet</p>
            <p className="text-sm">
              Run your first skill gap analysis from the <strong>Industry Connect</strong> page and
              it will appear here.
            </p>
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && history.length > 0 && (
        <div className="space-y-3">
          {history.map((entry, i) => (
            <HistoryCard key={entry.output.output_id ?? i} entry={entry} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}
