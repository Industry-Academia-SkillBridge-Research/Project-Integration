import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { User, Briefcase, MapPin, Building2, Loader2, ChevronLeft } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import PageHeader from '@/components/industryConnect/PageHeader';
import SourceModeForm from '@/components/industryConnect/SourceModeForm';
import StreamingOutput from '@/components/industryConnect/StreamingOutput';
import ResultsDashboard from '@/components/industryConnect/ResultsDashboard';
import { useStreaming } from '@/hooks/use-streaming-ic';
import { useModelSettings } from '@/hooks/use-model-settings-ic';
import { useRoles } from '@/hooks/use-roles-ic';
import { useJobsByRole } from '@/hooks/use-jobs-by-role-ic';
import { TEST_PROFILE } from '@/config/testProfiles';
import { generateProject, generateProjectFromSources } from '@/services/industryConnectService';
import type { ProjectRequest, CombinedSourceRequest, LinkedInJobResult } from '@/types/industryConnect';

export interface AnalysisFormValues {
  target_role: string;
  job_desc: string;
}

const IndustryConnect = () => {
  const [mode, setMode] = useState<'manual' | 'source'>('manual');
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
      job_desc: '',
    },
  });

  const loadTestProfile = () => {
    form.setValue('target_role', TEST_PROFILE.target_role);
    form.setValue('job_desc', TEST_PROFILE.job_desc);
    setRoleSelectValue('__other__');
    setSelectedJob(null);
  };

  const { streamingText, parsedResult, isStreaming, error, startStream } = useStreaming();

  const onSubmit = (data: AnalysisFormValues) => {
    const request: ProjectRequest = {
      student_data: {
        name: user?.name ?? 'Unknown',
        current_role: user?.current_role ?? 'Student',
        major: user?.major ?? '',
        interests: (user?.interests ?? '').split(',').map((s) => s.trim()).filter(Boolean),
        personality: user?.personality ?? '',
        skills: (user?.skills ?? '').split(',').map((s) => s.trim()).filter(Boolean),
        experience_summary: `Studying ${user?.major || 'Computer Science'}. Interested in ${user?.interests || 'various fields'}.`,
      },
      job_data: {
        role: data.target_role,
        required_skills: selectedJob?.skills ?? [],
        description_summary: data.job_desc,
      },
      target_role: data.target_role,
      model_provider: modelSettings.model_provider,
      ollama_model: modelSettings.ollama_model || null,
    };
    startStream((signal) => generateProject(request, signal));
  };

  const onSourceSubmit = (request: CombinedSourceRequest) => {
    startStream((signal) => generateProjectFromSources(request, signal));
  };

  const showStream = isStreaming || (streamingText && !parsedResult);
  const showResults = parsedResult && !isStreaming;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/50 backdrop-blur-sm bg-background/80 sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/">
              <h2 className="text-2xl font-bold text-gradient-primary">
                SkillScope
              </h2>
            </Link>
            <Link to="/modules">
              <Button variant="ghost" size="sm">
                <ChevronLeft className="w-4 h-4 mr-2" />
                Back to Modules
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <PageHeader
          title="Skill Gap & Project Generator"
          subtitle="Analyze skill gaps and get capstone project recommendations"
        />

        <Tabs value={mode} onValueChange={(v) => setMode(v as 'manual' | 'source')} className="mt-2">
          <TabsList className="mb-4">
            <TabsTrigger value="manual">Manual</TabsTrigger>
            <TabsTrigger value="source">From Sources</TabsTrigger>
          </TabsList>

          {/* ── MANUAL MODE ── */}
          <TabsContent value="manual">
            <div className="text-sm text-muted-foreground bg-muted/50 rounded-md px-3 py-2 mb-4">
              Your profile data is loaded from your account. Click "Edit profile" to update your skills and interests.
            </div>

            <div>
              <div className="flex justify-end mb-4">
                <Button type="button" variant="outline" size="sm" onClick={loadTestProfile}>
                  Load Test Profile
                </Button>
              </div>

              {/* Profile summary banner */}
              <div className="flex items-start gap-3 rounded-md border bg-muted/40 px-4 py-3 mb-5">
                <User className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
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
                  to="/analysis"
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
                              form.setValue('job_desc', '');
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
                    <div className="space-y-1">
                      <Label className="text-xs">Job Summary</Label>
                      <Textarea {...form.register('job_desc')} rows={5} />
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
                                  onClick={() => {
                                    setSelectedJob(job);
                                    const desc =
                                      job.description_summary ??
                                      job.description ??
                                      [
                                        job.title,
                                        job.company && `Company: ${job.company}`,
                                        job.location && `Location: ${job.location}`,
                                        job.skills?.length
                                          ? `Required skills: ${job.skills.join(', ')}`
                                          : null,
                                      ]
                                        .filter(Boolean)
                                        .join('\n');
                                    form.setValue('job_desc', desc);
                                  }}
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
                                  {job.skills && job.skills.length > 0 && (
                                    <div className="mt-1.5 flex flex-wrap gap-1">
                                      {job.skills.slice(0, 6).map((s) => (
                                        <span
                                          key={s}
                                          className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground"
                                        >
                                          {s}
                                        </span>
                                      ))}
                                      {job.skills.length > 6 && (
                                        <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                                          +{job.skills.length - 6} more
                                        </span>
                                      )}
                                    </div>
                                  )}
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
          </TabsContent>

          {/* ── SOURCE MODE ── */}
          <TabsContent value="source">
            <div className="text-sm text-muted-foreground bg-muted/50 rounded-md px-3 py-2 mb-4">
              Fetch candidate and job data from companion services instead of entering it manually.
              Requires LinkedIn Scraper (8000), Agent-Runtime (8002), and optionally Role-Skill-API (8181) to be running.
            </div>
            <div className="max-w-2xl">
              <SourceModeForm onSubmit={onSourceSubmit} isStreaming={isStreaming} />
            </div>
          </TabsContent>
        </Tabs>

        {/* ── Shared output (both modes) ── */}
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
          <div className="mt-6">
            <ResultsDashboard result={parsedResult} />
          </div>
        )}
      </div>
    </div>
  );
};

export default IndustryConnect;
