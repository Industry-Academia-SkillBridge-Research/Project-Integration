import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import Landing from "./pages/Landing";
import Auth from "./pages/Auth";
import AuthCallback from "./pages/AuthCallback";
import Modules from "./pages/Modules";
import Analysis from "./pages/Analysis";
import Pipeline from "./pages/Pipeline";
import SkillGap from "./pages/SkillGap";
import Recommendations from "./pages/Recommendations";
import NotFound from "./pages/NotFound";
import Profile from "./pages/Profile";
import CourseRecommendations from "./pages/CourseRecommendations";
import {
  TranscriptUploadPage,
  TranscriptDetailsPage,
  SkillSelectionPage,
  SkillQuizPage,
  QuizResultsPage,
  JobRecommendationsPage,
  BrowseJobsPage,
  JobDetailPage,
  PortfolioPage
} from "./pages/skillGapAnalysis";
import {
  UploadJDPage,
  InterviewPage,
  FeedbackPage
} from "./pages/interviewPrep";
import IndustryConnect from "./pages/IndustryConnect";

const queryClient = new QueryClient();

// Default student ID for Skill Gap Analysis workflow
const DEFAULT_STUDENT_ID = 'IT21013928';

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/auth" element={<Auth />} />
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route
              path="/modules"
              element={
                <ProtectedRoute>
                  <Modules />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analysis"
              element={
                <ProtectedRoute>
                  <Analysis />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              }
            />
            <Route
              path="/pipeline"
              element={
                <ProtectedRoute>
                  <Pipeline />
                </ProtectedRoute>
              }
            />
            <Route
              path="/courses"
              element={
                <ProtectedRoute>
                  <CourseRecommendations />
                </ProtectedRoute>
              }
            />
            <Route
              path="/skill-gap"
              element={
                <ProtectedRoute>
                  <SkillGap />
                </ProtectedRoute>
              }
            />
            
            {/* Skill Gap Analysis Workflow (Nipuni Backend) */}
            <Route
              path="/skill-gap-analysis"
              element={<Navigate to={`/skill-gap-analysis/${DEFAULT_STUDENT_ID}/upload`} replace />}
            />
            <Route
              path="/skill-gap-analysis/:studentId/upload"
              element={
                <ProtectedRoute>
                  <TranscriptUploadPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/skill-gap-analysis/:studentId/transcript"
              element={
                <ProtectedRoute>
                  <TranscriptDetailsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/skill-gap-analysis/:studentId/skills"
              element={
                <ProtectedRoute>
                  <SkillSelectionPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/skill-gap-analysis/:studentId/quiz"
              element={
                <ProtectedRoute>
                  <SkillQuizPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/skill-gap-analysis/:studentId/results/:attemptId"
              element={
                <ProtectedRoute>
                  <QuizResultsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/skill-gap-analysis/:studentId/portfolio"
              element={
                <ProtectedRoute>
                  <PortfolioPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/skill-gap-analysis/:studentId/jobs"
              element={
                <ProtectedRoute>
                  <JobRecommendationsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/skill-gap-analysis/:studentId/browse-jobs"
              element={
                <ProtectedRoute>
                  <BrowseJobsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/skill-gap-analysis/jobs/:jobId"
              element={
                <ProtectedRoute>
                  <JobDetailPage />
                </ProtectedRoute>
              }
            />
            
            <Route
              path="/recommendations"
              element={
                <ProtectedRoute>
                  <Recommendations />
                </ProtectedRoute>
              }
            />
            
            {/* Interview Prep Workflow (Nilmani Backend) */}
            <Route
              path="/interview-prep"
              element={
                <ProtectedRoute>
                  <UploadJDPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/interview-prep/interview"
              element={
                <ProtectedRoute>
                  <InterviewPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/interview-prep/feedback"
              element={
                <ProtectedRoute>
                  <FeedbackPage />
                </ProtectedRoute>
              }
            />
            
            {/* Industry Connect Portal (Thisaravi Backend) */}
            <Route
              path="/industry-connect"
              element={
                <ProtectedRoute>
                  <IndustryConnect />
                </ProtectedRoute>
              }
            />
            
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
