import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { CheckCircle2, ArrowRight, Briefcase, Target, List, LayoutGrid, ArrowLeft } from "lucide-react";
import { getClaimedSkills, planQuiz } from "@/services/nipuniService";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ErrorAlert } from "@/components/ui/error-alert";
import { Spinner } from "@/components/ui/spinner";

interface SkillCourse {
  code: string;
  grade: string;
  contribution: number;
}

interface ClaimedSkill {
  skill_name: string;
  claimed_level: string;
  claimed_score: number;
  evidence_count: number;
  category: string;
  courses?: SkillCourse[];
}

interface GroupedSkills {
  [category: string]: ClaimedSkill[];
}

export default function SkillSelectionPage() {
  const navigate = useNavigate();
  const { studentId } = useParams();
  const [skills, setSkills] = useState<ClaimedSkill[]>([]);
  const [groupedSkills, setGroupedSkills] = useState<GroupedSkills>({});
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<any>(null);
  const [viewMode, setViewMode] = useState<'list' | 'card'>('list');

  useEffect(() => {
    const fetchSkills = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await getClaimedSkills(studentId!) as any;
        const claimedSkills = data.claimed_skills || [];
        setSkills(claimedSkills);
        
        // Group skills by category
        const grouped = claimedSkills.reduce((acc: GroupedSkills, skill: ClaimedSkill) => {
          const category = skill.category || 'General';
          if (!acc[category]) {
            acc[category] = [];
          }
          acc[category].push(skill);
          return acc;
        }, {});
        
        // Sort skills within each category by score (descending)
        Object.keys(grouped).forEach(category => {
          grouped[category].sort((a, b) => b.claimed_score - a.claimed_score);
        });
        
        setGroupedSkills(grouped);
      } catch (err: any) {
        setError(err.response?.data || { message: err.message });
      } finally {
        setLoading(false);
      }
    };

    fetchSkills();
  }, [studentId]);

  const handleSkillToggle = (skillName: string) => {
    setSelectedSkills((prev) => {
      if (prev.includes(skillName)) {
        setError(null);
        return prev.filter((s) => s !== skillName);
      } else {
        if (prev.length >= 5) {
          setError({ message: "Maximum 5 skills allowed. Please deselect a skill to choose another." });
          return prev;
        }
        setError(null);
        return [...prev, skillName];
      }
    });
  };

  const handlePlanQuiz = async () => {
    if (selectedSkills.length === 0) {
      setError({ message: "Please select at least one skill" });
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await planQuiz(studentId!, selectedSkills);
      navigate(`/skill-gap-analysis/${studentId}/quiz`);
    } catch (err: any) {
      setError(err.response?.data || { message: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <Spinner />;

  // Define category order
  const categoryOrder = [
    'Programming Languages',
    'Databases',
    'Web Development',
    'Cloud & DevOps',
    'AI & Machine Learning',
    'Data Science & Analytics',
    'Big Data & Distributed Systems',
    'Software Engineering',
    'Operating Systems',
    'Networking',
    'Security & Compliance',
    'Mobile Development',
    'General'
  ];

  // Sort categories
  const sortedCategories = Object.keys(groupedSkills).sort((a, b) => {
    const indexA = categoryOrder.indexOf(a);
    const indexB = categoryOrder.indexOf(b);
    if (indexA === -1 && indexB === -1) return a.localeCompare(b);
    if (indexA === -1) return 1;
    if (indexB === -1) return -1;
    return indexA - indexB;
  });

  return (
    <div className="min-h-screen bg-gradient-hero">
      {/* Header */}
      <header className="container mx-auto px-6 py-6">
        <nav className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => navigate(`/skill-gap-analysis/${studentId}/transcript`)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Transcript
          </Button>
          <h1 className="text-xl font-bold text-foreground">Your Skills Portfolio</h1>
          <div className="w-40" /> {/* Spacer */}
        </nav>
      </header>

      {/* Main Content */}
      <div className="container mx-auto max-w-7xl px-6 pb-12 space-y-6">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-foreground mb-2">Your Skills Portfolio</h2>
          <p className="text-muted-foreground">Select up to 5 skills to validate through personalized quizzes</p>
        </div>
        
        <Card className="border-primary/20 sticky top-20 z-10 bg-background/95 backdrop-blur shadow-elevated">
          <CardContent className="pt-6">
            {error && <ErrorAlert error={error} />}
            
            <div className="flex items-center justify-between mb-4">
              <div className={`p-4 rounded-xl border flex-1 mr-4 transition-colors ${
                selectedSkills.length >= 5 
                  ? 'bg-gradient-to-r from-green-50 to-green-100 border-green-300' 
                  : 'bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20'
              }`}>
                <p className="text-sm font-semibold text-foreground mb-2">
                  Selected: <span className={`text-lg ${selectedSkills.length >= 5 ? 'text-green-600' : 'text-primary'}`}>
                    {selectedSkills.length}
                  </span> / 5 skills
                  {selectedSkills.length >= 5 && (
                    <span className="ml-2 text-xs font-normal text-green-700">✓ Maximum reached</span>
                  )}
                </p>
                <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-300 ${
                      selectedSkills.length >= 5 
                        ? 'bg-gradient-to-r from-green-500 to-green-600' 
                        : 'bg-gradient-to-r from-primary to-accent'
                    }`}
                    style={{ width: `${(selectedSkills.length / 5) * 100}%` }}
                  />
                </div>
              </div>
              
              <div className="flex gap-2">
                <Button
                  variant={viewMode === 'list' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                  className="gap-2"
                >
                  <List className="h-4 w-4" />
                  List
                </Button>
                <Button
                  variant={viewMode === 'card' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('card')}
                  className="gap-2"
                >
                  <LayoutGrid className="h-4 w-4" />
                  Cards
                </Button>
              </div>
            </div>

            <div className="flex justify-end pt-4 gap-3">
              <Button
                variant="outline"
                onClick={() => navigate(`/skill-gap-analysis/${studentId}/jobs`)}
                className="gap-2"
                size="lg"
              >
                <Target className="h-5 w-5" />
                AI Job Matches
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate(`/skill-gap-analysis/${studentId}/browse-jobs`)}
                className="gap-2"
                size="lg"
              >
                <Briefcase className="h-5 w-5" />
                Browse Jobs
              </Button>
              {submitting ? (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Spinner className="h-5 w-5" />
                  <span>Planning quiz...</span>
                </div>
              ) : (
                <Button
                  onClick={handlePlanQuiz}
                  disabled={selectedSkills.length === 0}
                  className="gap-2"
                  size="lg"
                >
                  Plan Quiz
                  <ArrowRight className="h-5 w-5" />
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {skills.length > 0 ? (
          <div className="space-y-6">
            {sortedCategories.map((category, catIndex) => (
              <Card key={category} className="border-l-4 border-l-primary shadow-card animate-fade-in" style={{ animationDelay: `${catIndex * 0.05}s` }}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-primary" />
                    {category}
                    <span className="ml-auto text-sm font-normal text-muted-foreground">
                      {groupedSkills[category].length} {groupedSkills[category].length === 1 ? 'skill' : 'skills'}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {viewMode === 'list' ? (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-12">Select</TableHead>
                          <TableHead>Skill</TableHead>
                          <TableHead>Level</TableHead>
                          <TableHead>Evidence</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {groupedSkills[category].map((skill, index) => {
                          const skillName = skill.skill_name;
                          const level = skill.claimed_level || 'Beginner';
                          return (
                            <TableRow key={index} className="hover:bg-muted/50">
                              <TableCell>
                                <input
                                  type="checkbox"
                                  checked={selectedSkills.includes(skillName)}
                                  onChange={() => handleSkillToggle(skillName)}
                                  className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer"
                                  disabled={
                                    !selectedSkills.includes(skillName) &&
                                    selectedSkills.length >= 5
                                  }
                                />
                              </TableCell>
                              <TableCell className="font-medium">{skillName}</TableCell>
                              <TableCell>
                                <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                                  level === 'Advanced' ? 'bg-green-100 text-green-700' :
                                  level === 'Intermediate' ? 'bg-blue-100 text-blue-700' :
                                  'bg-yellow-100 text-yellow-700'
                                }`}>
                                  {level}
                                </span>
                              </TableCell>
                              <TableCell>
                                <div className="group relative">
                                  <span className="text-sm text-muted-foreground cursor-help border-b border-dashed border-gray-300">
                                    {skill.evidence_count} {skill.evidence_count === 1 ? 'course' : 'courses'}
                                  </span>
                                  {skill.courses && skill.courses.length > 0 && (
                                    <div className="invisible group-hover:visible absolute z-50 left-0 mt-2 w-64 p-3 bg-white border border-gray-200 rounded-lg shadow-xl">
                                      <div className="text-xs font-semibold text-gray-700 mb-2">Contributing Courses:</div>
                                      <div className="space-y-1 max-h-48 overflow-y-auto">
                                        {skill.courses.map((course, idx) => (
                                          <div key={idx} className="flex items-center justify-between text-xs">
                                            <span className="font-medium text-gray-900">{course.code}</span>
                                            <div className="flex items-center gap-2">
                                              <span className="text-green-600 font-semibold">{course.grade}</span>
                                              <span className="text-gray-500">({course.contribution.toFixed(1)})</span>
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {groupedSkills[category].map((skill, index) => {
                        const skillName = skill.skill_name;
                        const level = skill.claimed_level || 'Beginner';
                        const isSelected = selectedSkills.includes(skillName);
                        const canSelect = isSelected || selectedSkills.length < 5;
                        
                        return (
                          <div
                            key={index}
                            onClick={() => canSelect && handleSkillToggle(skillName)}
                            className={`relative p-4 rounded-lg border-2 transition-all cursor-pointer ${
                              isSelected 
                                ? 'border-primary bg-primary/5 shadow-md' 
                                : canSelect
                                  ? 'border-gray-200 hover:border-primary/50 hover:shadow'
                                  : 'border-gray-100 opacity-50 cursor-not-allowed'
                            }`}
                          >
                            {/* Selection Indicator */}
                            <div className="absolute top-3 right-3">
                              {isSelected ? (
                                <CheckCircle2 className="h-5 w-5 text-primary" />
                              ) : (
                                <div className="h-5 w-5 rounded-full border-2 border-gray-300" />
                              )}
                            </div>

                            {/* Skill Name */}
                            <h4 className="font-semibold text-lg mb-3 pr-8">{skillName}</h4>

                            {/* Level */}
                            <div className="flex items-center gap-3 mb-3">
                              <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                                level === 'Advanced' ? 'bg-green-100 text-green-700' :
                                level === 'Intermediate' ? 'bg-blue-100 text-blue-700' :
                                'bg-yellow-100 text-yellow-700'
                              }`}>
                                {level}
                              </span>
                            </div>

                            {/* Evidence - Courses */}
                            <div className="space-y-1">
                              <div className="text-xs font-semibold text-gray-700">
                                Evidence ({skill.evidence_count} {skill.evidence_count === 1 ? 'course' : 'courses'}):
                              </div>
                              {skill.courses && skill.courses.length > 0 && (
                                <div className="space-y-1 max-h-24 overflow-y-auto text-xs">
                                  {skill.courses.slice(0, 3).map((course, idx) => (
                                    <div key={idx} className="flex items-center justify-between bg-gray-50 px-2 py-1 rounded">
                                      <span className="font-medium text-gray-900">{course.code}</span>
                                      <div className="flex items-center gap-1">
                                        <span className="text-green-600 font-semibold">{course.grade}</span>
                                      </div>
                                    </div>
                                  ))}
                                  {skill.courses.length > 3 && (
                                    <div className="text-xs text-muted-foreground italic px-2">
                                      +{skill.courses.length - 3} more course{skill.courses.length - 3 > 1 ? 's' : ''}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground">No skills found. Please upload a transcript first.</p>
              <Button 
                className="mt-4" 
                onClick={() => navigate(`/skill-gap-analysis/${studentId}/upload`)}
              >
                Upload Transcript
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
