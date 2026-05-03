import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
  Award, TrendingUp, Calendar, ArrowLeft, Target, CheckCircle, Mail, 
  User, Edit2, Camera, Download, Briefcase, AlertCircle, Sparkles, Trash2 
} from "lucide-react";
import { 
  getStudentProfile, updateStudentProfile, uploadProfilePhoto, 
  getMLJobRecommendations, clearStudentPortfolio 
} from "@/services/nipuniService";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ErrorAlert } from "@/components/ui/error-alert";
import { Spinner } from "@/components/ui/spinner";

interface PortfolioSkill {
  skill_name: string;
  correct_count: number;
  total_questions: number;
  verified_score: number;
  claimed_score: number;
  final_score: number;
  final_level: string;
  updated_at: string;
}

interface StudentProfile {
  student_id: string;
  name?: string;
  email?: string;
  program?: string;
  specialization?: string;
  intake?: string;
  bio?: string;
  photo_url?: string;
  portfolio: PortfolioSkill[];
}

interface JobRecommendation {
  job_id: string;
  title: string;
  company: string;
  role_key: string;
  match_score: number;
  total_required_skills: number;
  proficient_skills_count: number;
  missing_skills_count: number;
  proficient_skills: Array<{ skill: string; score: number }>;
  missing_skills: Array<{ skill: string; score: number; gap: number }>;
  description?: string;
}

export default function PortfolioPage() {
  const { studentId } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<any>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    name: "",
    email: "",
    program: "",
    specialization: "",
    bio: ""
  });
  const [uploading, setUploading] = useState(false);
  const [jobs, setJobs] = useState<JobRecommendation[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [expandedJobs, setExpandedJobs] = useState(new Set<string>());

  useEffect(() => {
    fetchProfile();
    fetchJobRecommendations();
  }, [studentId]);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getStudentProfile(studentId!) as any;
      setProfile(data);
      setEditForm({
        name: data.name || "",
        email: data.email || "",
        program: data.program || "",
        specialization: data.specialization || "",
        bio: data.bio || ""
      });
    } catch (err: any) {
      setError(err.response?.data || { message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      const result = await uploadProfilePhoto(studentId!, file) as any;
      if (profile) {
        setProfile({ ...profile, photo_url: result.photo_url });
      }
    } catch (err: any) {
      alert("Failed to upload photo: " + err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleSaveProfile = async () => {
    try {
      await updateStudentProfile(studentId!, editForm);
      setIsEditing(false);
      fetchProfile();
    } catch (err: any) {
      alert("Failed to update profile: " + err.message);
    }
  };

  const handleDownloadCV = () => {
    window.print();
  };

  const handleClearPortfolio = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to clear all portfolio records? This will remove all validated skills from quiz results. This action cannot be undone."
    );
    
    if (!confirmed) return;
    
    try {
      setLoading(true);
      const result = await clearStudentPortfolio(studentId!) as any;
      alert(`Successfully cleared ${result.deleted_count} portfolio records.`);
      await fetchProfile();
    } catch (err: any) {
      alert("Failed to clear portfolio: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const fetchJobRecommendations = async () => {
    try {
      setLoadingJobs(true);
      const data = await getMLJobRecommendations(studentId!, { topK: 5, threshold: 70, useVerified: true }) as any;
      setJobs(data.recommendations || []);
    } catch (err) {
      console.error('Failed to fetch ML job recommendations:', err);
      setJobs([]);
    } finally {
      setLoadingJobs(false);
    }
  };

  const getMatchColor = (score: number) => {
    if (score >= 80) return "text-green-600 bg-green-50 border-green-200";
    if (score >= 60) return "text-blue-600 bg-blue-50 border-blue-200";
    if (score >= 40) return "text-yellow-600 bg-yellow-50 border-yellow-200";
    return "text-red-600 bg-red-50 border-red-200";
  };

  const toggleJobExpansion = (jobId: string) => {
    setExpandedJobs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(jobId)) {
        newSet.delete(jobId);
      } else {
        newSet.add(jobId);
      }
      return newSet;
    });
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case "Advanced": return "bg-green-100 text-green-700 border-green-200";
      case "Intermediate": return "bg-blue-100 text-blue-700 border-blue-200";
      case "Beginner": return "bg-yellow-100 text-yellow-700 border-yellow-200";
      default: return "bg-gray-100 text-gray-700 border-gray-200";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      year: 'numeric'
    });
  };

  if (loading) return <Spinner />;
  if (!profile) return <ErrorAlert error={{ message: "Profile not found" }} />;

  return (
    <div className="container mx-auto max-w-6xl p-6 space-y-6">
      {/* Header with Actions */}
      <div className="flex justify-between items-center print:hidden">
        <Button 
          variant="ghost" 
          onClick={() => navigate(`/skill-gap-analysis/${studentId}/skills`)}
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleDownloadCV}>
            <Download className="w-4 h-4 mr-2" />
            Download CV
          </Button>
          {!isEditing ? (
            <Button onClick={() => setIsEditing(true)}>
              <Edit2 className="w-4 h-4 mr-2" />
              Edit Profile
            </Button>
          ) : (
            <>
              <Button variant="outline" onClick={() => setIsEditing(false)}>
                Cancel
              </Button>
              <Button onClick={handleSaveProfile}>
                Save Changes
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && <ErrorAlert error={error} />}

      {/* CV Header - Professional Profile Card */}
      <Card className="border-2 border-primary/20">
        <CardContent className="p-8">
          <div className="flex gap-8">
            {/* Profile Photo */}
            <div className="flex-shrink-0">
              <div className="relative group">
                <div className="w-40 h-40 rounded-full bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center overflow-hidden border-4 border-white shadow-lg">
                  {profile.photo_url ? (
                    <img src={profile.photo_url} alt="Profile" className="w-full h-full object-cover" />
                  ) : (
                    <User className="w-20 h-20 text-white" />
                  )}
                </div>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="absolute bottom-0 right-0 bg-primary text-white p-2 rounded-full shadow-lg hover:bg-primary-dark transition-colors print:hidden"
                  disabled={uploading}
                >
                  <Camera className="w-4 h-4" />
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handlePhotoUpload}
                />
              </div>
            </div>

            {/* Profile Info */}
            <div className="flex-1">
              {isEditing ? (
                <div className="space-y-4">
                  <input
                    type="text"
                    value={editForm.name}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    placeholder="Full Name"
                    className="w-full text-3xl font-bold border-b-2 border-primary/30 focus:border-primary outline-none"
                  />
                  <input
                    type="email"
                    value={editForm.email}
                    onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                    placeholder="Email Address"
                    className="w-full border-b border-gray-300 focus:border-primary outline-none"
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <input
                      type="text"
                      value={editForm.program}
                      onChange={(e) => setEditForm({ ...editForm, program: e.target.value })}
                      placeholder="Program"
                      className="border-b border-gray-300 focus:border-primary outline-none"
                    />
                    <input
                      type="text"
                      value={editForm.specialization}
                      onChange={(e) => setEditForm({ ...editForm, specialization: e.target.value })}
                      placeholder="Specialization"
                      className="border-b border-gray-300 focus:border-primary outline-none"
                    />
                  </div>
                  <textarea
                    value={editForm.bio}
                    onChange={(e) => setEditForm({ ...editForm, bio: e.target.value })}
                    placeholder="Professional Bio"
                    rows={3}
                    className="w-full border border-gray-300 rounded p-2 focus:border-primary outline-none resize-none"
                  />
                </div>
              ) : (
                <div className="space-y-3">
                  <h1 className="text-4xl font-bold text-foreground">
                    {profile.name || studentId}
                  </h1>
                  <div className="text-lg text-muted-foreground space-y-1">
                    {profile.email && (
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4" />
                        {profile.email}
                      </div>
                    )}
                    {profile.program && (
                      <div className="flex items-center gap-2">
                        <Award className="w-4 h-4" />
                        {profile.program} {profile.specialization && `- ${profile.specialization}`}
                      </div>
                    )}
                    {profile.intake && (
                      <div className="text-sm">Intake: {profile.intake}</div>
                    )}
                  </div>
                  {profile.bio && (
                    <p className="text-muted-foreground mt-4 leading-relaxed">
                      {profile.bio}
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Skills Portfolio Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-6 w-6 text-primary" />
                Validated Skills Portfolio
              </CardTitle>
              <CardDescription>
                Comprehensive skill assessment results from quiz validations
              </CardDescription>
            </div>
            {profile.portfolio.length > 0 && (
              <Button 
                variant="outline" 
                size="sm"
                className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200 print:hidden"
                onClick={handleClearPortfolio}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Clear Portfolio
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {profile.portfolio.length === 0 ? (
            <div className="text-center p-12">
              <Award className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
              <p className="text-muted-foreground mb-4">
                No validated skills yet. Take a quiz to build your portfolio!
              </p>
              <Button onClick={() => navigate(`/skill-gap-analysis/${studentId}/skills`)}>
                Start Skill Validation
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {profile.portfolio
                .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
                .map((skill, index) => (
                <div
                  key={index}
                  className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">{skill.skill_name}</h3>
                      <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <CheckCircle className="w-4 h-4 text-green-600" />
                          {skill.correct_count}/{skill.total_questions} correct
                        </span>
                        <span>Quiz: {skill.verified_score}%</span>
                        <span>Claimed: {skill.claimed_score}%</span>
                        <span>Final Score: {skill.final_score}%</span>
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formatDate(skill.updated_at)}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className={`px-4 py-2 rounded-full text-sm font-medium border ${getLevelColor(skill.final_level)}`}>
                        {skill.final_level}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recommended Jobs Section */}
      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Briefcase className="h-6 w-6 text-primary" />
            AI-Powered Job Recommendations
          </CardTitle>
          <CardDescription>
            Jobs matched to your <strong>validated skills</strong> from quiz results (ML-powered)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loadingJobs ? (
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <span className="ml-3 text-muted-foreground">Finding matching jobs...</span>
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-center p-8 text-muted-foreground">
              <Briefcase className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No job recommendations available yet.</p>
              <p className="text-sm mt-2">Complete more quizzes to build your skill portfolio!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {jobs.map((job, index) => (
                <div
                  key={job.job_id}
                  className="border-l-4 rounded-lg p-5 hover:shadow-lg transition-shadow bg-card"
                  style={{
                    borderLeftColor: job.match_score >= 80 ? '#16a34a' : 
                                    job.match_score >= 60 ? '#2563eb' : 
                                    job.match_score >= 40 ? '#eab308' : '#dc2626'
                  }}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-medium text-muted-foreground">#{index + 1}</span>
                        <span className="text-xs px-2 py-1 bg-secondary rounded-full">{job.role_key}</span>
                      </div>
                      <h3 
                        className="font-bold text-xl mb-1 text-primary hover:underline cursor-pointer"
                        onClick={() => navigate(`/skill-gap-analysis/jobs/${job.job_id}`)}
                      >
                        {job.title}
                      </h3>
                      <p className="text-sm text-muted-foreground mb-2">{job.company}</p>
                      
                      {/* Job Description */}
                      {job.description && (
                        <div className="mb-4">
                          <div 
                            className={`text-sm text-muted-foreground overflow-hidden transition-all ${
                              expandedJobs.has(job.job_id) ? 'max-h-96' : 'max-h-20'
                            }`}
                          >
                            <p className="whitespace-pre-line">
                              {expandedJobs.has(job.job_id) 
                                ? job.description 
                                : job.description.slice(0, 200) + (job.description.length > 200 ? '...' : '')
                              }
                            </p>
                          </div>
                          {job.description.length > 200 && (
                            <button
                              onClick={() => toggleJobExpansion(job.job_id)}
                              className="text-xs text-primary hover:underline mt-1 font-medium"
                            >
                              {expandedJobs.has(job.job_id) ? 'Show Less' : 'Read More'}
                            </button>
                          )}
                        </div>
                      )}
                      
                      <div className="grid grid-cols-3 gap-4 mb-4 p-3 bg-secondary/30 rounded-lg">
                        <div className="text-center">
                          <div className="text-lg font-bold text-foreground">{job.total_required_skills}</div>
                          <div className="text-xs text-muted-foreground">Required Skills</div>
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-bold text-green-600">{job.proficient_skills_count}</div>
                          <div className="text-xs text-muted-foreground">You Have</div>
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-bold text-red-600">{job.missing_skills_count}</div>
                          <div className="text-xs text-muted-foreground">Need to Learn</div>
                        </div>
                      </div>

                      {/* Matched Skills */}
                      {job.proficient_skills?.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                            <CheckCircle className="w-4 h-4 text-green-600" />
                            Your Validated Skills for This Role ({job.proficient_skills_count})
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

                      {/* Missing Skills */}
                      {job.missing_skills?.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-orange-600" />
                            Skills You Need to Develop ({job.missing_skills_count})
                          </h4>
                          <div className="flex flex-wrap gap-2">
                            {job.missing_skills.map((skill, idx) => (
                              <span 
                                key={idx}
                                className="px-3 py-1.5 bg-orange-50 text-orange-700 rounded-full text-sm font-medium border border-orange-200"
                              >
                                {skill.skill} (Need: {skill.gap}% more)
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div className={`px-4 py-3 rounded-lg border-2 text-center flex-shrink-0 ${getMatchColor(job.match_score)}`}>
                      <div className="text-3xl font-bold">{job.match_score}%</div>
                      <div className="text-xs font-medium mt-1">Match</div>
                    </div>
                  </div>
                </div>
              ))}
              
              <Button
                onClick={() => navigate(`/skill-gap-analysis/${studentId}/jobs`)}
                className="w-full gap-2"
                variant="outline"
              >
                <Sparkles className="h-4 w-4" />
                View All AI-Powered Recommendations
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="flex justify-between print:hidden">
        <Button
          variant="outline"
          onClick={() => navigate(`/skill-gap-analysis/${studentId}/transcript`)}
        >
          Back to Dashboard
        </Button>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => navigate(`/skill-gap-analysis/${studentId}/jobs`)}
          >
            <Briefcase className="w-4 h-4 mr-2" />
            View Job Matches
          </Button>
          <Button
            onClick={() => navigate(`/skill-gap-analysis/${studentId}/skills`)}
          >
            Take Quiz
          </Button>
        </div>
      </div>
    </div>
  );
}
