import { useState, useEffect } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { Award, TrendingUp, ChevronDown, ChevronUp, Info, ArrowLeft, ArrowRight } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface SkillResult {
  skill_name?: string;
  parent_skill?: string;
  skill?: string;
  correct?: number;
  total_questions?: number;
  questions_answered?: number;
  final_score?: number;
  score?: number;
  final_level?: string;
  level?: string;
  verified_score?: number;
  claimed_score?: number;
  w_quiz?: number;
  w_claimed?: number;
  explanation_text?: string;
}

interface QuizResult {
  per_skill?: SkillResult[];
  skill_results?: SkillResult[];
  skill_scores?: SkillResult[];
  verified_skills?: SkillResult[];
  total_questions?: number;
  average_score?: number;
}

export default function QuizResultsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { studentId, attemptId } = useParams();
  const [expandedSkills, setExpandedSkills] = useState<{ [key: string]: boolean }>({});
  
  // Try to get result from navigation state, then localStorage
  let result: QuizResult | null = location.state?.result;
  if (!result && attemptId) {
    const stored = localStorage.getItem(`quiz_result_${attemptId}`);
    if (stored) {
      try {
        result = JSON.parse(stored);
      } catch (e) {
        console.error('Failed to parse stored result:', e);
      }
    }
  }

  if (!result) {
    return (
      <div className="min-h-screen bg-gradient-hero">
        <div className="container mx-auto max-w-4xl p-6">
          <Card>
            <CardHeader>
              <CardTitle>No Results Found</CardTitle>
              <CardDescription>
                Please complete a quiz first to see your results
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => navigate(`/skill-gap-analysis/${studentId}/skills`)}>
                Start New Quiz
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Normalize backend response - support different field names
  const skillResults = result.per_skill || result.skill_results || result.skill_scores || result.verified_skills || [];
  
  // Use backend-provided statistics directly
  const skillsTested = skillResults.length;
  const totalQuestions = result.total_questions || 0;
  const averageScore = result.average_score || 0;
  
  const toggleExpand = (skillName: string) => {
    setExpandedSkills((prev) => ({
      ...prev,
      [skillName]: !prev[skillName],
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-hero">
      {/* Header */}
      <header className="container mx-auto px-6 py-6">
        <nav className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => navigate(`/skill-gap-analysis/${studentId}/skills`)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Skills
          </Button>
          <h1 className="text-xl font-bold text-foreground">Quiz Results</h1>
          <div className="w-32" /> {/* Spacer */}
        </nav>
      </header>

      {/* Main Content */}
      <div className="container mx-auto max-w-6xl px-6 pb-12 space-y-6">
        <div className="text-center mb-8 animate-fade-in">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary to-accent rounded-full mb-4">
            <Award className="h-10 w-10 text-white" />
          </div>
          <h2 className="text-4xl font-bold text-foreground mb-2">Quiz Complete!</h2>
          <p className="text-muted-foreground text-lg">Here's your detailed performance breakdown</p>
        </div>
        
        <Card className="border-primary/30 shadow-elevated animate-slide-up">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-2xl">
              <Award className="h-8 w-8 text-primary" />
              Quiz Results
            </CardTitle>
            <CardDescription>
              Your skill validation has been completed
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-6">
              <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border border-blue-200">
                <p className="text-sm font-semibold text-blue-700 mb-2">Skills Tested</p>
                <p className="text-4xl font-bold text-blue-600">{skillsTested}</p>
              </div>
              <div className="text-center p-6 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl border border-purple-200">
                <p className="text-sm font-semibold text-purple-700 mb-2">Average Score</p>
                <p className="text-4xl font-bold text-purple-600">{averageScore.toFixed(1)}%</p>
              </div>
              <div className="text-center p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-xl border border-green-200">
                <p className="text-sm font-semibold text-green-700 mb-2">Total Questions</p>
                <p className="text-4xl font-bold text-green-600">{totalQuestions}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-card animate-slide-up" style={{ animationDelay: '0.1s' }}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-6 w-6" />
              Skill-wise Performance
            </CardTitle>
            <CardDescription>
              Detailed breakdown of your performance for each skill
            </CardDescription>
          </CardHeader>
          <CardContent>
            {skillResults.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Skill</TableHead>
                    <TableHead>Correct/Total</TableHead>
                    <TableHead>Final Score</TableHead>
                    <TableHead>Level</TableHead>
                    <TableHead className="text-center">Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {skillResults.map((skill, index) => {
                    // Normalize skill field names
                    const skillName = skill.skill_name || skill.parent_skill || skill.skill || 'Unknown';
                    const correct = skill.correct || 0;
                    const totalQs = skill.total_questions || skill.questions_answered || 0;
                    const finalScore = skill.final_score || skill.score || 0;
                    const finalLevel = skill.final_level || skill.level || 'Unknown';
                    const verifiedScore = skill.verified_score || 0;
                    const claimedScore = skill.claimed_score || 0;
                    const wQuiz = skill.w_quiz || 0.7;
                    const wClaimed = skill.w_claimed || 0.3;
                    const explanation = skill.explanation_text || '';
                    
                    const isExpanded = expandedSkills[skillName];
                    
                    const performance = 
                      finalScore >= 80 ? { label: 'Excellent', color: 'bg-green-100 text-green-700' } :
                      finalScore >= 60 ? { label: 'Good', color: 'bg-blue-100 text-blue-700' } :
                      finalScore >= 40 ? { label: 'Average', color: 'bg-yellow-100 text-yellow-700' } :
                      { label: 'Needs Improvement', color: 'bg-red-100 text-red-700' };

                    return (
                      <>
                        <TableRow key={index}>
                          <TableCell className="font-medium">{skillName}</TableCell>
                          <TableCell>
                            <span className="font-semibold text-primary">{correct}</span>
                            <span className="text-muted-foreground">/{totalQs}</span>
                          </TableCell>
                          <TableCell className="font-semibold">{finalScore.toFixed(1)}%</TableCell>
                          <TableCell>
                            <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${performance.color}`}>
                              {finalLevel}
                            </span>
                          </TableCell>
                          <TableCell className="text-center">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => toggleExpand(skillName)}
                              className="gap-1"
                            >
                              <Info className="h-4 w-4" />
                              {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                            </Button>
                          </TableCell>
                        </TableRow>
                        
                        {isExpanded && (
                          <TableRow key={`${index}-details`}>
                            <TableCell colSpan={5} className="bg-muted/30">
                              <div className="p-4 space-y-3">
                                <h4 className="font-semibold text-sm flex items-center gap-2">
                                  <Info className="h-4 w-4" />
                                  Why this score?
                                </h4>
                                
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                  <div className="space-y-2">
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Quiz Score:</span>
                                      <span className="font-medium">{verifiedScore.toFixed(1)}% ({correct}/{totalQs} correct)</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Claimed Score:</span>
                                      <span className="font-medium">{claimedScore.toFixed(1)}%</span>
                                    </div>
                                  </div>
                                  
                                  <div className="space-y-2">
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Quiz Weight:</span>
                                      <span className="font-medium">{(wQuiz * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Claimed Weight:</span>
                                      <span className="font-medium">{(wClaimed * 100).toFixed(0)}%</span>
                                    </div>
                                  </div>
                                </div>
                                
                                <div className="bg-primary/5 p-3 rounded-md border border-primary/20">
                                  <p className="text-sm font-medium mb-2">Calculation:</p>
                                  <p className="text-sm font-mono">
                                    Final Score = ({(wQuiz * 100).toFixed(0)}% × {verifiedScore.toFixed(1)}%) + ({(wClaimed * 100).toFixed(0)}% × {claimedScore.toFixed(1)}%) = {finalScore.toFixed(1)}%
                                  </p>
                                </div>
                                
                                {explanation && (
                                  <p className="text-sm text-muted-foreground italic">
                                    {explanation}
                                  </p>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                        )}
                      </>
                    );
                  })}
                </TableBody>
              </Table>
            ) : (
              <p className="text-sm text-muted-foreground">No skill results available</p>
            )}
          </CardContent>
        </Card>

        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={() => navigate(`/skill-gap-analysis/${studentId}/skills`)}
          >
            Take Another Quiz
          </Button>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => navigate(`/skill-gap-analysis/${studentId}/portfolio`)}
            >
              View Portfolio
            </Button>
            <Button
              onClick={() => navigate(`/skill-gap-analysis/${studentId}/jobs`)}
              className="gap-2"
            >
              View Job Recommendations
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
