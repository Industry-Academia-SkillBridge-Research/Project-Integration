import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { startInterview, submitAnswer } from "@/services/nilmaniService";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Mic, MicOff, Send, CheckCircle, Loader2, Bot, User } from "lucide-react";
import "../styles/interview.css";

interface ConversationItem {
  type: 'question' | 'answer' | 'complete';
  content: string;
  number?: number;
}

// Speech Recognition types
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

const InterviewPage = () => {
  const navigate = useNavigate();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(7);
  const [userAnswer, setUserAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<ConversationItem[]>([]);

  // Speech recognition
  const [listening, setListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const recognitionRef = useRef<any>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const conversationEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const storedSessionId = localStorage.getItem("nilmani_sessionId");
    if (!storedSessionId) {
      navigate("/interview-prep");
      return;
    }

    setSessionId(storedSessionId);
    initializeInterview(storedSessionId);
    initializeSpeechRecognition();

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          // Ignore errors on cleanup
        }
      }
    };
  }, [navigate]);

  useEffect(() => {
    // Scroll to bottom when conversation updates
    conversationEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversationHistory]);

  const initializeSpeechRecognition = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join(" ");
      setUserAnswer(transcript);
    };

    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
      setListening(false);
    };

    recognitionRef.current = recognition;
  };

  const toggleListening = () => {
    if (!recognitionRef.current) return;

    if (listening) {
      recognitionRef.current.stop();
    } else {
      setUserAnswer("");
      recognitionRef.current.start();
    }
  };

  const initializeInterview = async (sid: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await startInterview(sid);
      setQuestionNumber(response.question_number);
      setTotalQuestions(response.total_questions);

      setConversationHistory([
        {
          type: "question",
          content: response.question,
          number: response.question_number,
        },
      ]);

      // Speak the question
      speakText(response.question);
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error ? err.message : "Failed to start interview"
      );
    } finally {
      setLoading(false);
    }
  };

  const speakText = (text: string) => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!userAnswer.trim()) {
      setError("Please provide an answer");
      return;
    }

    if (listening && recognitionRef.current) {
      recognitionRef.current.stop();
    }

    setLoading(true);
    setError(null);

    // Add user answer to conversation
    setConversationHistory((prev) => [
      ...prev,
      { type: "answer", content: userAnswer, number: questionNumber },
    ]);

    try {
      const response = await submitAnswer(sessionId!, userAnswer);

      if (response.is_complete) {
        setIsComplete(true);
        setConversationHistory((prev) => [
          ...prev,
          { type: "complete", content: "Interview completed! Great job!" },
        ]);
      } else {
        setQuestionNumber(response.question_number);

        setConversationHistory((prev) => [
          ...prev,
          {
            type: "question",
            content: response.question,
            number: response.question_number,
          },
        ]);

        // Speak the next question
        speakText(response.question);
      }

      setUserAnswer("");
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Failed to submit answer");
    } finally {
      setLoading(false);
    }
  };

  const handleEndInterview = () => {
    if (window.confirm("Are you sure you want to end the interview?")) {
      localStorage.removeItem("nilmani_sessionId");
      navigate("/interview-prep/feedback");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      handleSubmitAnswer();
    }
  };

  if (isComplete) {
    return (
      <div className="interview-page">
        <Card className="interview-completion-card">
          <CheckCircle className="w-16 h-16 text-success mb-4" />
          <h1 className="interview-title">Interview Complete!</h1>
          <p className="interview-completion-text">
            You've successfully completed all {totalQuestions} questions.
          </p>
          <div className="interview-completion-stats">
            <div className="interview-stat-item">
              <div className="interview-stat-number">{totalQuestions}</div>
              <div className="interview-stat-label">Questions Answered</div>
            </div>
            <div className="interview-stat-item">
              <div className="interview-stat-number">
                {conversationHistory.filter((h) => h.type === "answer").length}
              </div>
              <div className="interview-stat-label">Responses Given</div>
            </div>
          </div>
          <div className="interview-button-group">
            <Button onClick={() => navigate("/interview-prep")} size="lg">
              Start New Interview
            </Button>
            <Button
              onClick={() => navigate("/interview-prep/feedback")}
              variant="outline"
              size="lg"
            >
              View Summary
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="interview-page interview-in-progress">
      <div className="interview-header">
        <div>
          <div className="interview-eyebrow">
            Step 2 of 2 • Interview in Progress
          </div>
          <h1 className="interview-title">AI Interview Training</h1>
          <div className="interview-progress-info">
            Question {questionNumber} of {totalQuestions}
          </div>
        </div>
        <Button variant="outline" onClick={handleEndInterview}>
          End Interview
        </Button>
      </div>

      <div className="interview-container">
        {/* Progress Bar */}
        <div className="interview-progress-bar-container">
          <div
            className="interview-progress-bar-fill"
            style={{
              width: `${(questionNumber / totalQuestions) * 100}%`,
            }}
          />
        </div>

        {/* Conversation Thread */}
        <div className="interview-conversation-thread">
          {conversationHistory.map((item, index) => (
            <div key={index} className={`interview-message-bubble ${item.type}`}>
              {item.type === "question" && (
                <div className="interview-message-header">
                  <Bot className="w-5 h-5 text-primary" />
                  <span className="interview-message-label">AI Interviewer</span>
                  {item.number && (
                    <span className="interview-question-badge">
                      Question {item.number}
                    </span>
                  )}
                </div>
              )}
              {item.type === "answer" && (
                <div className="interview-message-header">
                  <User className="w-5 h-5 text-foreground" />
                  <span className="interview-message-label">You</span>
                </div>
              )}
              <div className="interview-message-content">{item.content}</div>
            </div>
          ))}

          {loading && (
            <div className="interview-message-bubble question interview-loading-bubble">
              <div className="interview-message-header">
                <Bot className="w-5 h-5 text-primary" />
                <span className="interview-message-label">AI Interviewer</span>
              </div>
              <div className="interview-typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}

          <div ref={conversationEndRef} />
        </div>

        {/* Answer Input Section */}
        <Card className="interview-answer-section">
          <label className="interview-input-label">Your Answer</label>
          <div className="interview-answer-input-group">
            <textarea
              ref={textareaRef}
              className="interview-answer-textarea"
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Type your answer here or use the microphone..."
              rows={4}
              disabled={loading}
            />

            <div className="interview-input-controls">
              <div className="interview-controls-left">
                {speechSupported && (
                  <Button
                    variant={listening ? "destructive" : "outline"}
                    size="icon"
                    onClick={toggleListening}
                    disabled={loading}
                    title={listening ? "Stop recording" : "Start voice input"}
                  >
                    {listening ? (
                      <MicOff className="w-5 h-5" />
                    ) : (
                      <Mic className="w-5 h-5" />
                    )}
                  </Button>
                )}
              </div>
              <div className="interview-controls-right">
                <Button
                  onClick={handleSubmitAnswer}
                  disabled={loading || !userAnswer.trim()}
                  size="lg"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4 mr-2" />
                      Submit Answer
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>

          {error && (
            <div className="interview-error-message">
              {error}
            </div>
          )}

          <p className="interview-input-hint">
            Press Ctrl+Enter to submit • Click the microphone for voice input
          </p>
        </Card>
      </div>
    </div>
  );
};

export default InterviewPage;
