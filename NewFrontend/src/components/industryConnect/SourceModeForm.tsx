import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { useModelSettings } from '@/hooks/use-model-settings-ic';
import { fetchRoles, searchJobs, fetchCandidates } from '@/services/industryConnectService';
import type {
  CombinedSourceRequest,
  RoleInfo,
  LinkedInJobResult,
  CandidateSummary,
} from '@/types/industryConnect';
import { Building2, MapPin } from 'lucide-react';

interface SourceModeFormProps {
  onSubmit: (request: CombinedSourceRequest) => void;
  isStreaming: boolean;
}

export default function SourceModeForm({ onSubmit, isStreaming }: SourceModeFormProps) {
  const { settings: modelSettings } = useModelSettings();

  // Job search state
  const [jobQuery, setJobQuery] = useState('');
  const [jobResults, setJobResults] = useState<LinkedInJobResult[]>([]);
  const [jobSearchLoading, setJobSearchLoading] = useState(false);
  const [jobSearchError, setJobSearchError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<LinkedInJobResult | null>(null);

  // Candidate state
  const [candidates, setCandidates] = useState<CandidateSummary[]>([]);
  const [candidatesLoading, setCandidatesLoading] = useState(false);
  const [candidatesError, setCandidatesError] = useState<string | null>(null);
  const [selectedCandidateId, setSelectedCandidateId] = useState('');

  // Role key state
  const [roles, setRoles] = useState<RoleInfo[]>([]);
  const [rolesLoading, setRolesLoading] = useState(false);
  const [selectedRoleKey, setSelectedRoleKey] = useState('');

  // Load candidates and roles on mount
  useEffect(() => {
    setCandidatesLoading(true);
    fetchCandidates()
      .then(setCandidates)
      .catch((e) => setCandidatesError(e.message))
      .finally(() => setCandidatesLoading(false));

    setRolesLoading(true);
    fetchRoles()
      .then(setRoles)
      .catch(() => {/* Role-Skill-API optional — silently ignore */})
      .finally(() => setRolesLoading(false));
  }, []);

  const handleJobSearch = async () => {
    if (!jobQuery.trim()) return;
    setJobSearchLoading(true);
    setJobSearchError(null);
    setJobResults([]);
    setSelectedJob(null);
    try {
      const results = await searchJobs(jobQuery.trim());
      setJobResults(results);
      if (results.length === 0) setJobSearchError('No jobs found for that query.');
    } catch (e) {
      setJobSearchError(e instanceof Error ? e.message : 'Job search failed');
    } finally {
      setJobSearchLoading(false);
    }
  };

  const handleSubmit = () => {
    const request: CombinedSourceRequest = {
      model_provider: modelSettings.model_provider,
    };
    if (selectedJob) request.job_id = selectedJob.job_id;
    if (selectedCandidateId) request.candidate_id = selectedCandidateId;
    if (selectedRoleKey) request.role_key = selectedRoleKey;
    onSubmit(request);
  };

  const canSubmit = !isStreaming && (!!selectedJob || !!selectedCandidateId);

  return (
    <div className="space-y-6">
      {/* Job Search */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Job (LinkedIn Scraper)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              placeholder="e.g. Data Engineer, Remote"
              value={jobQuery}
              onChange={(e) => setJobQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleJobSearch()}
              className="h-9"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleJobSearch}
              disabled={jobSearchLoading || !jobQuery.trim()}
            >
              {jobSearchLoading ? 'Searching…' : 'Search'}
            </Button>
          </div>

          {jobSearchError && (
            <p className="text-xs text-destructive">{jobSearchError}</p>
          )}

          {jobResults.length > 0 && (
            <div className="border rounded-md divide-y max-h-48 overflow-y-auto">
              {jobResults.map((job) => (
                <button
                  key={job.job_id}
                  type="button"
                  onClick={() => setSelectedJob(job)}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-muted transition-colors ${
                    selectedJob?.job_id === job.job_id ? 'bg-primary/10 font-medium' : ''
                  }`}
                >
                  <div className="font-medium">{job.title}</div>
                  {(job.company || job.location) && (
                    <div className="text-xs text-muted-foreground flex gap-2">
                      {job.company && (
                        <span className="flex items-center gap-1">
                          <Building2 className="h-3 w-3" />
                          {job.company}
                        </span>
                      )}
                      {job.location && (
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {job.location}
                        </span>
                      )}
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}

          {selectedJob && (
            <div className="rounded-md bg-primary/10 border border-primary/20 px-3 py-2 text-sm">
              <span className="font-medium">Selected:</span> {selectedJob.title}
              <span className="ml-1 text-xs text-muted-foreground">({selectedJob.job_id})</span>
              <button
                type="button"
                className="ml-2 text-xs text-destructive underline"
                onClick={() => { setSelectedJob(null); setJobResults([]); setJobQuery(''); }}
              >
                clear
              </button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Candidate Picker */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Candidate (Agent-Runtime)</CardTitle>
        </CardHeader>
        <CardContent>
          {candidatesError && (
            <p className="text-xs text-destructive mb-2">{candidatesError}</p>
          )}
          {candidatesLoading ? (
            <p className="text-xs text-muted-foreground">Loading candidates…</p>
          ) : (
            <Select value={selectedCandidateId} onValueChange={setSelectedCandidateId}>
              <SelectTrigger className="h-9">
                <SelectValue placeholder={candidates.length === 0 ? 'No candidates found' : 'Select candidate…'} />
              </SelectTrigger>
              <SelectContent>
                {candidates.map((c) => (
                  <SelectItem key={c.candidate_id} value={c.candidate_id}>
                    {c.name} — {c.current_role}
                    <span className="ml-1 text-xs text-muted-foreground">({c.candidate_id})</span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </CardContent>
      </Card>

      {/* Role Key (optional) */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">
            Role Key{' '}
            <span className="text-xs font-normal text-muted-foreground">(optional — enriches required skills)</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {rolesLoading ? (
            <p className="text-xs text-muted-foreground">Loading roles…</p>
          ) : (
            <Select value={selectedRoleKey} onValueChange={setSelectedRoleKey}>
              <SelectTrigger className="h-9">
                <SelectValue placeholder="None (skip skill enrichment)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">None</SelectItem>
                {roles.map((r) => (
                  <SelectItem key={r.role_key} value={r.role_key}>
                    {r.name ?? r.role_key}
                    {r.job_count != null && (
                      <span className="ml-1 text-xs text-muted-foreground">({r.job_count} jobs)</span>
                    )}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </CardContent>
      </Card>

      <Separator />

      <Button
        type="button"
        className="w-full"
        disabled={!canSubmit}
        onClick={handleSubmit}
      >
        {isStreaming ? 'Generating…' : 'Generate from Sources'}
      </Button>

      {!selectedJob && !selectedCandidateId && (
        <p className="text-xs text-muted-foreground text-center">
          Select at least a job or a candidate to continue.
        </p>
      )}
    </div>
  );
}
