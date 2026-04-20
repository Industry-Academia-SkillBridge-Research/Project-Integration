import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Briefcase, TrendingUp, CheckCircle, AlertCircle, ArrowLeft, Filter, Target, BookOpen } from "lucide-react";
import { getMLJobRecommendations } from "@/services/nipuniService";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ErrorAlert } from "@/components/ui/error-alert";
import { Spinner } from "@/components/ui/spinner";

interface SkillDetail {
  skill: string;
  score: number;
  level?: string;
  gap?: number;
  recommendation?: string;
}

interface ReadinessInfo {
  level: string;
  message: string;
}

interface JobRecommendation {
  job_id: string;
  title: string;
  company: string;
  role_key: string;
  match_score: number;
  skill_match_percentage: number;
  proficient_skills_count: number;
  needs_improvement_count: number;
  missing_skills_count: number;
  proficient_skills: SkillDetail[];
  needs_improvement: SkillDetail[];
  missing_skills: SkillDetail[];
  readiness: ReadinessInfo;
  next_steps?: string[];
}

export default function BrowseJobsPage() {
  const { studentId } = useParams();
  const navigate = useNavigate();
  
  const [jobs, setJobs] = useState<JobRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [topK, setTopK] = useState(10);
  const [threshold, setThreshold] = useState(70);
  const [roleKey, setRoleKey] = useState("");

  useEffect(() => {
    fetchRecommendations();
  }, [studentId]);

  const fetchRecommendations = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await getMLJobRecommendations(studentId!, {
        topK,
        threshold,
        roleKey: roleKey || undefined
      });
      setJobs(response.recommendations || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch recommendations";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const getMatchColor = (score: number) => {
    if (score >= 80) return "text-green-600 bg-green-50 border-green-200";
    if (score >= 60) return "text-blue-600 bg-blue-50 border-blue-200";
    if (score >= 40) return "text-yellow-600 bg-yellow-50 border-yellow-200";
    return "text-red-600 bg-red-50 border-red-200";
  };

  const getMatchLabel = (score: number) => {
    if (score >= 80) return "Excellent Match";
    if (score >= 60) return "Good Match";
    if (score >= 40) return "Fair Match";
    return "Needs Development";
  };

  const getReadinessColor = (level: string) => {
    const colors: Record<string, string> = {
      "Ready to Apply": "text-green-700 bg-green-50 border-green-200",
      "Almost Ready": "text-yellow-700 bg-yellow-50 border-yellow-200",
      "Developing": "text-orange-700 bg-orange-50 border-orange-200",
      "Early Stage": "text-red-700 bg-red-50 border-red-200"
    };
    return colors[level] || "text-gray-700 bg-gray-50 border-gray-200";
  };

  if (loading) return <Spinner />;

  return (
    <div className="container mx-auto max-w-7xl p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Button 
            variant="ghost" 
            onClick={() => navigate(`/skill-gap-analysis/${studentId}/skills`)}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Skills
          </Button>
          <h1 className="text-3xl font-bold text-foreground mb-2">Browse Job Opportunities</h1>
          <p className="text-muted-foreground">
            Explore job openings matched to your skill profile
          </p>
        </div>
      </div>

      {/* Filters */}
      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Number of Jobs</label>
              <input
                type="number"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value))}
                min="1"
                max="50"
                className="w-full px-3 py-2 border border-input rounded-md"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Match Threshold (%)</label>
              <input
                type="number"
                value={threshold}
                onChange={(e) => setThreshold(parseInt(e.target.value))}
                min="0"
                max="100"
                className="w-full px-3 py-2 border border-input rounded-md"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Role Category</label>
              <select
                value={roleKey}
                onChange={(e) => setRoleKey(e.target.value)}
                className="w-full px-3 py-2 border border-input rounded-md"
              >
                <option value="">All Roles</option>
                <option value="AIML">AI/ML</option>
                <option value="FULLSTACK">Full Stack</option>
                <option value="DEVOPS">DevOps</option>
                <option value="DATA">Data Engineering</option>
              </select>
            </div>
            <div className="flex items-end">
              <Button onClick={fetchRecommendations} className="w-full">
                Apply Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && <ErrorAlert error={error} />}

      {/* Results Summary */}
      {jobs.length > 0 && (
        <div className="bg-gradient-to-r from-primary/10 to-primary/5 p-4 rounded-xl border border-primary/20">
          <p className="text-sm font-semibold text-foreground">
            Found <span className="text-primary text-lg">{jobs.length}</span> job recommendations
          </p>
        </div>
      )}

      {/* Job Cards */}
      <div className="space-y-4">
        {jobs.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Briefcase className="w-16 h-16 mx-auto mb-4 text-muted-foreground opacity-50" />
              <p className="text-muted-foreground">
                No job recommendations found. Try adjusting your filters or building more skills.
              </p>
            </CardContent>
          </Card>
        ) : (
          jobs.map((job, index) => (
            <Card key={job.job_id} className="hover:shadow-lg transition-shadow border-l-4" style={{
              borderLeftColor: job.match_score >= 80 ? '#16a34a' : 
                              job.match_score >= 60 ? '#2563eb' : 
                              job.match_score >= 40 ? '#eab308' : '#dc2626'
            }}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-medium text-muted-foreground">#{index + 1}</span>
                      <span className="text-xs px-2 py-1 bg-secondary rounded-full">{job.role_key}</span>
                    </div>
                    <CardTitle 
                      className="text-xl mb-1 text-primary hover:underline cursor-pointer"
                      onClick={() => navigate(`/skill-gap-analysis/jobs/${job.job_id}`)}
                    >
                      {job.title}
                    </CardTitle>
                    <CardDescription className="text-base">{job.company}</CardDescription>
                  </div>
                  <div className={`px-4 py-3 rounded-lg border-2 ${getMatchColor(job.match_score)}`}>
                    <div className="text-3xl font-bold">{job.match_score}%</div>
                    <div className="text-xs font-medium mt-1">{getMatchLabel(job.match_score)}</div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Match Summary */}
                <div className="grid grid-cols-3 gap-4 p-3 bg-secondary/50 rounded-lg">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-primary">{job.skill_match_percentage}%</div>
                    <div className="text-xs text-muted-foreground">Match Score</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{job.proficient_skills_count}</div>
                    <div className="text-xs text-muted-foreground">Proficient</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">{job.missing_skills_count}</div>
                    <div className="text-xs text-muted-foreground">To Develop</div>
                  </div>
                </div>

                {/* Readiness Assessment */}
                <div className={`p-4 rounded-lg border-2 ${getReadinessColor(job.readiness.level)}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <Target className="h-4 w-4" />
                    <h4 className="font-semibold">{job.readiness.level}</h4>
                  </div>
                  <p className="text-sm">{job.readiness.message}</p>
                </div>

                {/* Proficient Skills */}
                {job.proficient_skills.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      Your Proficient Skills ({job.proficient_skills_count})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {job.proficient_skills.map((skill, idx) => (
                        <span 
                          key={idx}
                          className="px-3 py-1.5 bg-green-50 text-green-700 rounded-full text-sm font-medium border border-green-200"
                        >
                          {skill.skill} ({skill.score}%)
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Skills Needing Improvement */}
                {job.needs_improvement.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-yellow-600" />
                      Skills to Improve ({job.needs_improvement_count})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {job.needs_improvement.map((skill, idx) => (
                        <span 
                          key={idx}
                          className="px-2 py-1 bg-yellow-50 text-yellow-700 rounded text-sm"
                        >
                          {skill.skill} ({skill.score}% - Gap: {skill.gap}%)
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Missing Skills */}
                {job.missing_skills.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-orange-600" />
                      Skills to Develop ({job.missing_skills_count})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {job.missing_skills.map((skill, idx) => (
                        <span 
                          key={idx}
                          className="px-2 py-1 bg-orange-50 text-orange-700 rounded text-sm"
                        >
                          {skill.skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Next Steps */}
                {job.next_steps && job.next_steps.length > 0 && (
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <h4 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
                      <BookOpen className="h-4 w-4" />
                      Recommended Next Steps
                    </h4>
                    <ul className="space-y-2">
                      {job.next_steps.map((step, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm text-blue-800">
                          <span className="font-bold text-blue-600">{idx + 1}.</span>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
