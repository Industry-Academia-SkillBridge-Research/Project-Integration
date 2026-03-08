import { useState, useState as useCollapseState } from 'react';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useStreaming } from '@/hooks/use-streaming';
import { useModelSettings } from '@/hooks/use-model-settings';
import { useRoles } from '@/hooks/use-roles';
import { useJobsByRole } from '@/hooks/use-jobs-by-role';
import { TEST_PROFILE } from '@/config/test-profiles';
import { generateProject } from '@/services/analysisService';
import type { CombinedSourceRequest, LinkedInJobResult } from '@/types/api';
import PageHeader from '@/components/layout/PageHeader';
import StreamingOutput from '@/components/analysis/StreamingOutput';
import ResultsDashboard from '@/components/analysis/ResultsDashboard';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { useAuth } from '@/context/AuthContext';
import { UserCircle, Briefcase, MapPin, Building2, Loader2, ChevronDown } from 'lucide-react';

export interface AnalysisFormValues {
  target_role: string;
}

export default function AnalysisPage() {
  const [roleSelectValue, setRoleSelectValue] = useState<string>('');
  const [selectedJob, setSelectedJob] = useState<LinkedInJobResult | null>(null);
  const { settings: modelSettings } = useModelSettings();
  const { user } = useAuth();
  const { roles, isLoading: rolesLoading, error: rolesError } = useRoles();

  // Derive the role_key for the selected role (null when "other" or nothing selected)
  const activeRoleKey = roleSelectValue && roleSelectValue !== '__other__' ? roleSelectValue : null;
  const { jobs, isLoading: jobsLoading, error: jobsError } = useJobsByRole(activeRoleKey);

  const form = useForm<AnalysisFormValues>({
    defaultValues: {
      target_role: '',
    },
  });

  const loadTestProfile = () => {
    form.setValue('target_role', TEST_PROFILE.target_role);
    setRoleSelectValue('__other__');
    setSelectedJob(null);
  };

  const { streamingText, parsedResult, isStreaming, error, startStream } = useStreaming();

  const onSubmit = (data: AnalysisFormValues) => {
    const jobDescription =
      selectedJob?.description_summary ??
      selectedJob?.description?.substring(0, 500) ??
      `Targeting a role as ${data.target_role}`;

    const request: CombinedSourceRequest = {
      inline_student_data: {
        name: user?.name ?? 'Unknown',
        current_role: user?.current_role ?? '',
        major: user?.major ?? '',
        interests: (user?.interests ?? '').split(',').map((s) => s.trim()).filter(Boolean),
        personality: user?.personality ?? '',
        skills: (user?.skills ?? '').split(',').map((s) => s.trim()).filter(Boolean),
        experience_summary: 'N/A',
      },
      inline_job_data: {
        role: data.target_role,
        required_skills: selectedJob?.skills ?? [],
        description_summary: jobDescription,
      },
      target_role: data.target_role,
      role_key: activeRoleKey ?? undefined,
      model_provider: modelSettings.model_provider,
    };
    startStream((signal) => generateProject(request, signal));
  };

  const showStream = isStreaming || (!!streamingText && !parsedResult);
  const showResults = !!parsedResult && !isStreaming;

  return (
    <div>
      <PageHeader
        title="Skill Gap & Project Generator"
        subtitle="Analyze skill gaps and get capstone project recommendations"
      />

      <div className="mt-2">
        <div className="text-sm text-muted-foreground bg-muted/50 rounded-md px-3 py-2 mb-4">
          The fields below (Major, Interests, Personality) are critical for the fine-tuned model.
        </div>

        <div>
          <div className="flex justify-end mb-4">
            <Button type="button" variant="outline" size="sm" onClick={loadTestProfile}>
              Load Test Profile
            </Button>
          </div>

          {/* Profile summary banner */}
          <div className="flex items-start gap-3 rounded-md border bg-muted/40 px-4 py-3 mb-5">
            <UserCircle className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
            <div className="flex-1 min-w-0 text-sm">
              <span className="font-medium">{user?.name ?? 'You'}</span>
              {(user?.current_role || user?.major) && (
                <span className="text-muted-foreground">
                  {' · '}
                  {[user.current_role, user.major].filter(Boolean).join(' — ')}
                </span>
              )}
              {user?.skills && (
                <p className="text-muted-foreground text-xs mt-0.5 truncate">
                  Skills: {user.skills}
                </p>
              )}
            </div>
            <Link
              to="/profile"
              className="text-xs text-primary hover:underline shrink-0"
            >
              Edit profile
            </Link>
          </div>

          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Job Description</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Target Role</Label>
                    {rolesError ? (
                      <Input
                        {...form.register('target_role')}
                        placeholder="e.g. Software Engineer"
                        className="h-9"
                      />
                    ) : (
                      <>
                        <Select
                          value={roleSelectValue}
                          onValueChange={(val) => {
                            setRoleSelectValue(val);
                            setSelectedJob(null);
                            if (val !== '__other__') {
                              const role = roles.find((r) => r.role_key === val);
                              form.setValue('target_role', role?.name ?? val);
                            } else {
                              form.setValue('target_role', '');
                            }
                          }}
                          disabled={rolesLoading}
                        >
                          <SelectTrigger className="h-9 w-full">
                            <SelectValue
                              placeholder={
                                rolesLoading ? 'Loading roles…' : 'Select a role'
                              }
                            />
                          </SelectTrigger>
                          <SelectContent>
                            {roles.map((role) => (
                              <SelectItem key={role.role_key} value={role.role_key}>
                                {role.name}
                                {role.tag && (
                                  <span className="ml-2 text-xs text-muted-foreground">
                                    {role.tag}
                                  </span>
                                )}
                              </SelectItem>
                            ))}
                            <SelectItem value="__other__">Other (enter manually)</SelectItem>
                          </SelectContent>
                        </Select>
                        {roleSelectValue === '__other__' && (
                          <Input
                            {...form.register('target_role')}
                            placeholder="e.g. Software Engineer"
                            className="h-9 mt-2"
                          />
                        )}
                      </>
                    )}
                  </div>

                  {/* ── Required Skills (populated from selected job) ── */}
                  <div className="space-y-1">
                    <Label className="text-xs">Required Skills</Label>
                    {selectedJob?.skills && selectedJob.skills.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5 rounded-md border bg-muted/30 px-3 py-2.5">
                        {selectedJob.skills.map((s) => (
                          <span
                            key={s}
                            className="rounded-full bg-primary/10 text-primary px-2.5 py-0.5 text-xs font-medium"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground rounded-md border border-dashed px-3 py-3 text-center">
                        {activeRoleKey
                          ? 'Select a job below to see required skills'
                          : 'Select a role to see required skills'}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* ── Available Jobs for selected role ── */}
              {activeRoleKey && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Briefcase className="h-4 w-4 text-muted-foreground" />
                      Available Jobs
                      {!jobsLoading && jobs.length > 0 && (
                        <span className="ml-auto text-xs font-normal text-muted-foreground">
                          {jobs.length} listing{jobs.length !== 1 ? 's' : ''}
                        </span>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {jobsLoading && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground py-4 justify-center">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Loading jobs…
                      </div>
                    )}
                    {jobsError && (
                      <p className="text-sm text-destructive">{jobsError}</p>
                    )}
                    {!jobsLoading && !jobsError && jobs.length === 0 && (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        No job listings found for this role.
                      </p>
                    )}
                    {!jobsLoading && jobs.length > 0 && (
                      <ul className="space-y-2 max-h-64 overflow-y-auto pr-1">
                        {jobs.map((job) => {
                          const isSelected = selectedJob?.job_id === job.job_id;
                          return (
                            <li key={job.job_id}>
                              <button
                                type="button"
                                onClick={() => setSelectedJob(job)}
                                className={`w-full text-left rounded-md border px-3 py-2.5 text-sm transition-colors ${
                                  isSelected
                                    ? 'border-primary bg-primary/5'
                                    : 'border-border hover:border-primary/50 hover:bg-muted/40'
                                }`}
                              >
                                <p className="font-medium leading-tight">{job.title}</p>
                                <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
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
                              </button>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </CardContent>
                </Card>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={isStreaming}
              >
                {isStreaming ? 'Generating...' : 'Generate Plan'}
              </Button>
            </form>
        </div>
      </div>

      {/* ── Output ── */}
      {error && !parsedResult && (
        <div className="mt-4 rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {showStream && (
        <div className="mt-6">
          <StreamingOutput text={streamingText} isStreaming={isStreaming} />
        </div>
      )}

      {showResults && (
        <div className="mt-6 space-y-4">
          <ResultsDashboard result={parsedResult!} />

          {/* Collapsible raw output so users can always inspect the full model response */}
          {streamingText && (
            <RawOutputCollapsible text={streamingText} />
          )}
        </div>
      )}
    </div>
  );
}

function RawOutputCollapsible({ text }: { text: string }) {
  const [open, setOpen] = useCollapseState(false);
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger asChild>
        <button className="flex w-full items-center justify-between rounded-md border bg-muted/30 px-4 py-2.5 text-sm font-medium hover:bg-muted/50 transition-colors">
          Full Model Output
          <ChevronDown
            className={`h-4 w-4 text-muted-foreground transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          />
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-1">
          <StreamingOutput text={text} isStreaming={false} />
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
