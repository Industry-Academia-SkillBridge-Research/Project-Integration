import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { BookOpen, Send, ArrowLeft } from "lucide-react";
import { generateQuizFromBank, submitQuiz } from "@/services/nipuniService";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ErrorAlert } from "@/components/ui/error-alert";
import { Spinner } from "@/components/ui/spinner";

interface QuizQuestion {
  question_id: number;
  question_text: string;
  parent_skill: string;
  difficulty_level: string;
  options?: {
    A: string;
    B: string;
    C: string;
    D: string;
  };
  option_a?: string;
  option_b?: string;
  option_c?: string;
  option_d?: string;
}

interface QuizData {
  attempt_id: string | number;
  questions: QuizQuestion[];
}

interface Answers {
  [key: number]: string | null;
}

export default function SkillQuizPage() {
  const navigate = useNavigate();
  const { studentId } = useParams();
  const [quiz, setQuiz] = useState<QuizData | null>(null);
  const [answers, setAnswers] = useState<Answers>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<any>(null);

  useEffect(() => {
    const fetchQuiz = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await generateQuizFromBank(studentId!) as QuizData;
        setQuiz(data);
        // Initialize answers object
        const initialAnswers: Answers = {};
        data.questions?.forEach((q: QuizQuestion) => {
          initialAnswers[q.question_id] = null;
        });
        setAnswers(initialAnswers);
      } catch (err: any) {
        setError(err.response?.data || { message: err.message });
      } finally {
        setLoading(false);
      }
    };

    fetchQuiz();
  }, [studentId]);

  const handleAnswerChange = (questionId: number, option: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: option,
    }));
  };

  const handleSubmit = async () => {
    // Check if all questions are answered
    const unanswered = Object.values(answers).filter(a => a === null).length;
    if (unanswered > 0) {
      setError({ message: `Please answer all questions. ${unanswered} question(s) remaining.` });
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const formattedAnswers = Object.entries(answers).map(([question_id, selected_option]) => ({
        question_id: parseInt(question_id),
        selected_option,
      }));

      const result = await submitQuiz(studentId!, quiz!.attempt_id, formattedAnswers);
      
      // Save to localStorage as backup
      localStorage.setItem(`quiz_result_${quiz!.attempt_id}`, JSON.stringify(result));
      
      // Navigate with attemptId in URL and state
      navigate(`/skill-gap-analysis/${studentId}/results/${quiz!.attempt_id}`, { state: { result } });
    } catch (err: any) {
      setError(err.response?.data || { message: err.message });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <Spinner />;
  if (error && !quiz) return (
    <div className="min-h-screen bg-gradient-hero">
      <div className="container mx-auto max-w-4xl p-6">
        <ErrorAlert error={error} />
        <div className="mt-4 flex justify-center">
          <Button onClick={() => navigate(`/skill-gap-analysis/${studentId}/skills`)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Skills
          </Button>
        </div>
      </div>
    </div>
  );

  const answeredCount = Object.values(answers).filter(a => a !== null).length;
  const totalQuestions = quiz?.questions?.length || 0;

  return (
    <div className="min-h-screen bg-gradient-hero">
      {/* Header */}
      <header className="container mx-auto px-6 py-6">
        <nav className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => navigate(`/skill-gap-analysis/${studentId}/skills`)}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Skills
          </Button>
          <h1 className="text-xl font-bold text-foreground">Skill Validation Quiz</h1>
          <div className="w-32" /> {/* Spacer */}
        </nav>
      </header>

      {/* Main Content */}
      <div className="container mx-auto max-w-4xl px-6 pb-12 space-y-6">
        <Card className="shadow-elevated">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-6 w-6" />
              Skill Validation Quiz
            </CardTitle>
            <CardDescription>
              Answer all questions to validate your skills
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-muted/50 p-4 rounded-md mb-6">
              <p className="text-sm font-medium">
                Progress: {answeredCount} / {totalQuestions} questions answered
              </p>
              <div className="mt-2 h-2 bg-background rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary transition-all duration-300"
                  style={{ width: `${(answeredCount / totalQuestions) * 100}%` }}
                />
              </div>
            </div>

            {error && <ErrorAlert error={error} />}
          </CardContent>
        </Card>

        <div className="space-y-4">
          {quiz?.questions?.map((question, index) => (
            <Card key={question.question_id} className="shadow-card animate-fade-in" style={{ animationDelay: `${index * 0.05}s` }}>
              <CardHeader>
                <CardTitle className="text-lg">
                  Question {index + 1}
                </CardTitle>
                <div className="flex gap-2 text-xs text-muted-foreground">
                  <span className="bg-secondary px-2 py-1 rounded">
                    {question.parent_skill}
                  </span>
                  <span className="bg-secondary px-2 py-1 rounded">
                    Difficulty: {question.difficulty_level}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-base font-medium">{question.question_text}</p>
                
                <div className="space-y-2">
                  {(['A', 'B', 'C', 'D'] as const).map((option) => {
                    const optionText = question.options?.[option] || 
                      (question as any)[`option_${option.toLowerCase()}`] || '';
                    
                    return (
                      <label
                        key={option}
                        className={`flex items-start gap-3 p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                          answers[question.question_id] === option
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50'
                        }`}
                      >
                        <input
                          type="radio"
                          name={`question-${question.question_id}`}
                          value={option}
                          checked={answers[question.question_id] === option}
                          onChange={() => handleAnswerChange(question.question_id, option)}
                          className="mt-1 h-4 w-4 text-primary focus:ring-primary"
                        />
                        <span className="flex-1">
                          <span className="font-semibold mr-2">{option}.</span>
                          {optionText}
                        </span>
                      </label>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="flex justify-end">
          {submitting ? (
            <Spinner />
          ) : (
            <Button
              onClick={handleSubmit}
              disabled={answeredCount < totalQuestions}
              size="lg"
              className="gap-2"
            >
              <Send className="h-4 w-4" />
              Submit Quiz
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
