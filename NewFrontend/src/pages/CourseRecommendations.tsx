import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Sparkles, Star, ExternalLink, Loader2 } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { getCourseRecommendationsForJobGap, type CourseRecommendation } from "@/services/courseService";

// Helper function to convert target_role to role_key format
const getRoleKey = (targetRole?: string): string | null => {
  if (!targetRole) return null;
  const roleMap: Record<string, string> = {
    "ML Engineer": "ai_ml_engineer",
    "Data Analyst": "data_analyst",
    "Data Engineer": "data_engineer",
    "Data Scientist": "data_scientist",
    "Software Engineer": "software_engineer",
    "DevOps Engineer": "devops_engineer",
  };
  return roleMap[targetRole] || null;
};

const CourseRecommendations = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [courses, setCourses] = useState<CourseRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCourses = async () => {
      if (!user?.missing_skills || user.missing_skills.length === 0) {
        setError("No skill gaps found. Please complete an analysis first.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const roleKey = getRoleKey(user.target_role);
        
        if (!roleKey) {
          setError("Target role not found. Please complete your profile.");
          setLoading(false);
          return;
        }

        // Extract skill names from missing skills
        const missingSkillNames = user.missing_skills.map((s: any) => 
          typeof s === 'string' ? s : s.skill
        );

        const response = await getCourseRecommendationsForJobGap(
          roleKey,
          missingSkillNames
        );

        setCourses(response.recommendations || []);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch course recommendations:", err);
        setError("Failed to load course recommendations. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchCourses();
  }, [user]);

  if (!user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <p className="text-muted-foreground">Please log in to view recommendations.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(-1)}
              className="text-slate-300 hover:text-white"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Analysis
            </Button>
          </div>
          <h1 className="text-xl font-bold text-white">Course Recommendations</h1>
          <Button
            onClick={() => navigate("/analysis")}
            className="bg-cyan-600 hover:bg-cyan-700 text-white"
          >
            New Analysis
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-12 max-w-7xl">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="w-8 h-8 text-cyan-400" />
            <h2 className="text-4xl font-bold text-white">Your Learning Roadmap</h2>
          </div>
          <p className="text-slate-400 text-lg">
            Personalized course recommendations to help you bridge your skill gaps for{" "}
            <span className="text-cyan-400 font-semibold">{user.target_role || "your target role"}</span>
          </p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-12 h-12 text-cyan-400 animate-spin mb-4" />
            <p className="text-slate-400">Loading personalized courses for you...</p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-950/30 border border-red-800 rounded-lg p-6 text-center">
            <p className="text-red-400 mb-4">{error}</p>
            <Button
              onClick={() => navigate("/analysis")}
              className="bg-cyan-600 hover:bg-cyan-700"
            >
              Start Analysis
            </Button>
          </div>
        )}

        {/* Course Grid */}
        {!loading && !error && courses.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {courses.map((course, idx) => (
              <div
                key={idx}
                className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden hover:border-cyan-500 hover:shadow-2xl hover:shadow-cyan-500/20 transition-all duration-300 flex flex-col"
              >
                {/* Course Image */}
                {course.imageUrl ? (
                  <div className="relative h-48 bg-gradient-to-br from-slate-800 to-slate-900">
                    <img
                      src={course.imageUrl}
                      alt={course.title}
                      className="w-full h-full object-cover"
                    />
                    {course.avg_rating && (
                      <Badge className="absolute top-3 right-3 bg-amber-500 text-white border-0">
                        <Star className="w-3 h-3 mr-1 fill-white" />
                        {course.avg_rating}
                      </Badge>
                    )}
                  </div>
                ) : (
                  <div className="relative h-48 bg-gradient-to-br from-cyan-900/30 to-slate-900 flex items-center justify-center">
                    <div className="text-slate-600 text-6xl font-bold">
                      {course.title.charAt(0)}
                    </div>
                    {course.avg_rating && (
                      <Badge className="absolute top-3 right-3 bg-amber-500 text-white border-0">
                        <Star className="w-3 h-3 mr-1 fill-white" />
                        {course.avg_rating}
                      </Badge>
                    )}
                  </div>
                )}

                {/* Course Content */}
                <div className="p-6 flex flex-col flex-1">
                  {/* Course Title */}
                  <h3 className="text-white font-bold text-lg mb-2 line-clamp-2">
                    {course.title}
                  </h3>

                  {/* Provider */}
                  {course.provider && (
                    <p className="text-slate-400 text-sm mb-3">
                      {course.provider}
                    </p>
                  )}

                  {/* Skills Section */}
                  <div className="mb-4 flex-1">
                    <p className="text-slate-400 text-xs mb-2">Skills you'll gain:</p>
                    <div className="flex flex-wrap gap-2">
                      {course.covered_deficit_skills?.slice(0, 3).map((skill, skillIdx) => (
                        <Badge
                          key={skillIdx}
                          variant="secondary"
                          className="bg-slate-800 text-slate-300 text-xs"
                        >
                          {skill}
                        </Badge>
                      ))}
                      {course.covered_deficit_skills && course.covered_deficit_skills.length > 3 && (
                        <Badge
                          variant="outline"
                          className="border-slate-700 text-slate-400 text-xs"
                        >
                          +{course.covered_deficit_skills.length - 3}
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Difficulty and Impact */}
                  <div className="flex items-center justify-between mb-4">
                    {course.difficulty && (
                      <Badge className="bg-cyan-950 text-cyan-300 border-cyan-800 text-xs">
                        {course.difficulty.toUpperCase()}
                      </Badge>
                    )}
                    <div className="text-right">
                      <p className="text-xs text-slate-500">Impact</p>
                      <p className="text-amber-400 font-bold">
                        {Math.round((course.gain_score || 0) * 10)}
                      </p>
                    </div>
                  </div>

                  {/* View Course Button */}
                  {course.url && (
                    <a
                      href={course.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full"
                    >
                      <Button className="w-full bg-cyan-600 hover:bg-cyan-700 text-white group">
                        View Course
                        <ExternalLink className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                      </Button>
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && courses.length === 0 && (
          <div className="text-center py-20">
            <Sparkles className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-300 mb-2">
              No Courses Available
            </h3>
            <p className="text-slate-500 mb-6">
              We couldn't find courses for your skill gaps. Try running a new analysis.
            </p>
            <Button
              onClick={() => navigate("/analysis")}
              className="bg-cyan-600 hover:bg-cyan-700"
            >
              Start New Analysis
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default CourseRecommendations;
