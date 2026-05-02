import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { Link, useNavigate } from "react-router-dom";
import { 
  ChevronLeft, 
  User, 
  Mail, 
  Calendar, 
  Briefcase, 
  GraduationCap, 
  Heart, 
  Target,
  Code,
  Shield,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  Brain,
  BookOpen,
  ExternalLink,
  Star,
  Loader2
} from "lucide-react";
import { useState, useEffect } from "react";

const Profile = () => {
  const { user, logout, checkAuth } = useAuth();
  const navigate = useNavigate();
  const [skills, setSkills] = useState<string[]>([]);
  const [interests, setInterests] = useState<string[]>([]);

  const normalizeList = (value: string | string[] | undefined | null) => {
    if (Array.isArray(value)) {
      return value.map(item => String(item).trim()).filter(Boolean);
    }

    if (typeof value === 'string') {
      return value.split(',').map(item => item.trim()).filter(Boolean);
    }

    return [];
  };

  useEffect(() => {
    setSkills(normalizeList(user?.skills));
    setInterests(normalizeList(user?.interests));
  }, [user]);

  // Refresh user data when profile page mounts to ensure latest analysis is shown
  useEffect(() => {
    checkAuth();
  }, []);

  if (!user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-muted-foreground mb-4">Please log in to view your profile</p>
          <Button onClick={() => navigate('/auth')}>Go to Login</Button>
        </div>
      </div>
    );
  }

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
            <div className="flex items-center gap-3">
              <Link to="/modules">
                <Button variant="ghost" size="sm">
                  <ChevronLeft className="w-4 h-4 mr-2" />
                  Back to Modules
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Profile Header Card */}
        <Card className="mb-6 bg-gradient-card border-border shadow-elevated">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row items-center md:items-start gap-6">
              {/* Avatar */}
              <Avatar className="h-24 w-24 border-4 border-primary/20">
                <AvatarImage src={user.picture} alt={user.name} />
                <AvatarFallback className="bg-primary text-primary-foreground text-2xl">
                  {(user.name || 'U').split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                </AvatarFallback>
              </Avatar>

              {/* User Info */}
              <div className="flex-1 text-center md:text-left">
                <h1 className="text-3xl font-bold text-foreground mb-2">{user.name}</h1>
                <div className="flex flex-col md:flex-row gap-3 text-muted-foreground mb-4">
                  <div className="flex items-center justify-center md:justify-start gap-2">
                    <Mail className="w-4 h-4" />
                    <span className="text-sm">{user.email}</span>
                  </div>
                  {user.current_role && (
                    <div className="flex items-center justify-center md:justify-start gap-2">
                      <Briefcase className="w-4 h-4" />
                      <span className="text-sm">{user.current_role}</span>
                    </div>
                  )}
                </div>
                <div className="flex flex-wrap gap-2 justify-center md:justify-start">
                  <Badge variant="secondary" className="flex items-center gap-1">
                    <Shield className="w-3 h-3" />
                    {(user.provider || 'local').charAt(0).toUpperCase() + (user.provider || 'local').slice(1)}
                  </Badge>
                  {user.is_active && (
                    <Badge variant="default" className="bg-green-500">Active</Badge>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex flex-col gap-2">
                {/* COMMENTED OUT: Edit Profile Button */}
                {/* <Link to="/analysis">
                  <Button variant="default" className="w-full">
                    Edit Profile
                  </Button>
                </Link> */}
                <Button variant="outline" onClick={logout}>
                  Sign Out
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Analysis Insights Card - Latest CV Analysis Results */}
        {user.readiness_score !== undefined && user.readiness_score !== null && (
          <Card className="mb-6 bg-gradient-to-br from-primary/5 to-accent/5 border-primary/20 shadow-elevated animate-fade-in">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Brain className="w-6 h-6 text-primary" />
                  Latest Career Analysis
                </CardTitle>
                {user.latest_analysis_date && (
                  <span className="text-xs text-muted-foreground">
                    {new Date(user.latest_analysis_date).toLocaleDateString()}
                  </span>
                )}
              </div>
              <CardDescription>
                AI-powered insights from your Personalized Learning Path analysis
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Readiness Score */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-primary" />
                    <span className="font-semibold text-foreground">Career Readiness</span>
                  </div>
                  <span className="text-2xl font-bold text-primary">
                    {user.readiness_score}%
                  </span>
                </div>
                <Progress value={user.readiness_score} className="h-3" />
                <p className="text-sm text-muted-foreground">
                  {user.readiness_score >= 80 ? "Excellent! You're well-prepared for your target role." :
                   user.readiness_score >= 60 ? "Good progress! Focus on key skill gaps to improve." :
                   user.readiness_score >= 40 ? "Keep learning! You're building a strong foundation." :
                   "Just getting started. Follow the recommended learning path."}
                </p>
              </div>

              <Separator />

              {/* AI Explanation - More Prominent */}
              {user.ai_explanation && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-lg font-semibold">
                    <Sparkles className="w-5 h-5 text-primary" />
                    <span>Career Insights</span>
                  </div>
                  <div className="bg-gradient-to-br from-primary/10 to-accent/10 rounded-xl p-5 border-2 border-primary/30 shadow-sm">
                    <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                      {user.ai_explanation}
                    </p>
                  </div>
                </div>
              )}

              {/* Summary */}
              {user.analysis_summary && (
                <div className="bg-primary/10 rounded-lg p-3 border border-primary/20">
                  <p className="text-sm text-foreground">
                    {user.analysis_summary}
                  </p>
                </div>
              )}

              <Separator />

              {/* Matched Skills - Detailed View */}
              {user.matched_skills && user.matched_skills.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-base font-semibold text-green-600 dark:text-green-400">
                    <CheckCircle2 className="w-5 h-5" />
                    <span>Your Strengths ({user.matched_skills.length} skills)</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[400px] overflow-y-auto pr-2">
                    {user.matched_skills.map((skill: any, idx: number) => (
                      <div
                        key={idx}
                        className="bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-semibold text-green-700 dark:text-green-300 text-sm">
                            {skill.skill}
                          </h4>
                          <Badge className="bg-green-600 text-white text-xs">
                            {Math.round((skill.confidence || 0) * 100)}%
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Code className="w-3 h-3" />
                            Evidence: {skill.evidence_count || 1}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Missing Skills - GNN Predictions Only */}
              {user.missing_skills && user.missing_skills.filter((s: any) => s.P_gnn !== undefined).length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-base font-semibold text-amber-600 dark:text-amber-400">
                    <Brain className="w-5 h-5" />
                    <span>AI-Recommended Skills to Learn ({user.missing_skills.filter((s: any) => s.P_gnn !== undefined).length} skills)</span>
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">
                    These skills are prioritized by our Graph Neural Network based on your profile, role requirements, and learning potential.
                  </p>
                  <div className="grid grid-cols-1 gap-3 max-h-[500px] overflow-y-auto pr-2">
                    {user.missing_skills
                      .filter((skill: any) => skill.P_gnn !== undefined)
                      .map((skill: any, idx: number) => (
                      <div
                        key={idx}
                        className="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/30 border-2 border-amber-200 dark:border-amber-800 rounded-xl p-5 hover:shadow-lg transition-all hover:border-amber-400"
                      >
                        {/* Skill Header */}
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-2">
                            <h4 className="font-bold text-amber-800 dark:text-amber-200 text-lg">
                              {skill.skill}
                            </h4>
                            {skill.category && (
                              <Badge variant="secondary" className="text-xs">
                                {skill.category}
                              </Badge>
                            )}
                          </div>
                        </div>

                        {/* Learning Potential - Prominent Display */}
                        <div className="bg-gradient-to-r from-amber-100 to-orange-100 dark:from-amber-900/50 dark:to-orange-900/50 rounded-lg p-4 mb-3 border border-amber-200 dark:border-amber-700">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Sparkles className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                              <span className="text-sm font-medium text-muted-foreground">Learning Potential</span>
                            </div>
                            <span className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                              {Math.round((skill.P_gnn || 0) * 100)}%
                            </span>
                          </div>
                        </div>

                        {/* Priority Score */}
                        <div>
                          <div className="flex items-center justify-between text-xs mb-2">
                            <span className="text-muted-foreground font-medium">Priority Score</span>
                            <span className="font-bold text-amber-600 dark:text-amber-400">
                              {((skill.final_score || 0) * 100).toFixed(1)}
                            </span>
                          </div>
                          <Progress 
                            value={(skill.final_score || 0) * 100} 
                            className="h-2 bg-amber-100 dark:bg-amber-950"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Button */}
              <div className="pt-2">
                <Link to="/analysis" className="w-full">
                  <Button variant="default" className="w-full gap-2">
                    <TrendingUp className="w-4 h-4" />
                    Run New Analysis
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Course Recommendations Button */}
        {user.readiness_score !== undefined && user.missing_skills && user.missing_skills.length > 0 && (
          <Card className="mb-6 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 border-blue-200 dark:border-blue-800 shadow-elevated animate-fade-in">
            <CardContent className="py-8">
              <div className="flex flex-col items-center justify-center text-center space-y-4">
                <BookOpen className="w-12 h-12 text-blue-600" />
                <div>
                  <h3 className="text-lg font-semibold mb-2">Ready to Learn?</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    View personalized course recommendations to bridge your skill gaps
                  </p>
                </div>
                <Link to="/courses" className="w-full max-w-md">
                  <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white gap-2 py-6">
                    <Sparkles className="w-5 h-5" />
                    View My Learning Roadmap
                    <ExternalLink className="w-4 h-4" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Profile Details Grid */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Academic Background */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-primary" />
                Academic Background
              </CardTitle>
              <CardDescription>Your educational information</CardDescription>
            </CardHeader>
            <CardContent>
              {user.major ? (
                <div className="space-y-2">
                  <div className="flex justify-between items-start">
                    <span className="text-sm text-muted-foreground">Major</span>
                    <span className="text-sm font-medium text-right">{user.major}</span>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No academic information available</p>
              )}
            </CardContent>
          </Card>

          {/* Career Goals */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5 text-primary" />
                Career Goals
              </CardTitle>
              <CardDescription>Your professional aspirations</CardDescription>
            </CardHeader>
            <CardContent>
              {user.target_role ? (
                <div className="space-y-2">
                  <div className="flex justify-between items-start">
                    <span className="text-sm text-muted-foreground">Target Role</span>
                    <span className="text-sm font-medium text-right">{user.target_role}</span>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No target role set</p>
              )}
            </CardContent>
          </Card>

          {/* Skills */}
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="w-5 h-5 text-primary" />
                Skills & Expertise
              </CardTitle>
              <CardDescription>Your technical and professional skills</CardDescription>
            </CardHeader>
            <CardContent>
              {skills.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {skills.map((skill, index) => (
                    <Badge key={index} variant="secondary">
                      {skill}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No skills added yet</p>
              )}
            </CardContent>
          </Card>

          {/* Interests */}
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Heart className="w-5 h-5 text-primary" />
                Interests
              </CardTitle>
              <CardDescription>Areas you're passionate about</CardDescription>
            </CardHeader>
            <CardContent>
              {interests.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {interests.map((interest, index) => (
                    <Badge key={index} variant="outline" className="border-primary/50">
                      {interest}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No interests added yet</p>
              )}
            </CardContent>
          </Card>

          {/* Personality */}
          {user.personality && (
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="w-5 h-5 text-primary" />
                  Personality Type
                </CardTitle>
                <CardDescription>Your personality profile</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm">{user.personality}</p>
              </CardContent>
            </Card>
          )}

          {/* Account Info */}
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="w-5 h-5 text-primary" />
                Account Information
              </CardTitle>
              <CardDescription>Your account details</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Member Since</span>
                  <span className="text-sm font-medium">
                    {new Date(user.created_at).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </span>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Last Login</span>
                  <span className="text-sm font-medium">
                    {new Date(user.last_login).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </span>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">User ID</span>
                  <span className="text-sm font-medium font-mono">#{user.id}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Navigate to different sections</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Link to="/analysis">
                <Button variant="outline" className="w-full">
                  Edit Profile
                </Button>
              </Link>
              <Link to="/modules">
                <Button variant="outline" className="w-full">
                  Modules
                </Button>
              </Link>
              <Link to="/industry-connect">
                <Button variant="outline" className="w-full">
                  Industry Connect
                </Button>
              </Link>
              <Link to="/">
                <Button variant="outline" className="w-full">
                  Home
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default Profile;
