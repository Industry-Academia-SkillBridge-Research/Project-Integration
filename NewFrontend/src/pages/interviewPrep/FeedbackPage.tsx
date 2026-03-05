import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CheckCircle, ArrowLeft } from "lucide-react";
import "../styles/interview.css";

const FeedbackPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Session data available in localStorage if needed
  }, []);

  const handleStartNew = () => {
    localStorage.removeItem("nilmani_sessionId");
    localStorage.removeItem("nilmani_jdText");
    localStorage.removeItem("nilmani_chunksCount");
    navigate("/interview-prep");
  };

  const handleBackToModules = () => {
    navigate("/modules");
  };

  return (
    <div className="interview-page">
      <div className="interview-header">
        <div>
          <div className="interview-eyebrow">Completed</div>
          <h1 className="interview-title">Interview Summary</h1>
        </div>
      </div>

      <div className="interview-feedback-container">
        <Card className="interview-feedback-card success-card">
          <CheckCircle className="w-16 h-16 text-success mb-4" />
          <h2 className="interview-feedback-title">
            Interview Completed Successfully!
          </h2>
          <p className="interview-card-description">
            You've finished your AI-powered interview training session. Great work!
          </p>
        </Card>

        <div className="interview-action-buttons">
          <Button onClick={handleStartNew} size="lg" className="w-full sm:w-auto">
            Start New Interview
          </Button>
          <Button
            onClick={handleBackToModules}
            variant="outline"
            size="lg"
            className="w-full sm:w-auto"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Modules
          </Button>
        </div>
      </div>
    </div>
  );
};

export default FeedbackPage;
