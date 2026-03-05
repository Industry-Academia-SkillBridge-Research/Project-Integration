import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { startInterview, submitAnswer } from "../services/api";

function InterviewPage() {
  const navigate = useNavigate();
  const [sessionId, setSessionId] = useState(null);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(7);
  const [userAnswer, setUserAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isComplete, setIsComplete] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  
  // Speech recognition
  const [listening, setListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const recognitionRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    const storedSessionId = localStorage.getItem('sessionId');
    if (!storedSessionId) {
      navigate("/");
      return;
    }
    
    setSessionId(storedSessionId);
    initializeInterview(storedSessionId);
    initializeSpeechRecognition();
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigate]);

  const initializeSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join(" ");
      setUserAnswer(transcript);
    };

    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = (event) => {
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

  const initializeInterview = async (sid) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await startInterview(sid);
      setQuestionNumber(response.question_number);
      setTotalQuestions(response.total_questions);
      
      setConversationHistory([
        { type: 'question', content: response.question, number: response.question_number }
      ]);
      
      // Speak the question
      speakText(response.question);
      
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to start interview");
    } finally {
      setLoading(false);
    }
  };

  const speakText = (text) => {
    if ('speechSynthesis' in window) {
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
    setConversationHistory(prev => [
      ...prev,
      { type: 'answer', content: userAnswer, number: questionNumber }
    ]);

    try {
      const response = await submitAnswer(sessionId, userAnswer);
      
      if (response.is_complete) {
        setIsComplete(true);
        setConversationHistory(prev => [
          ...prev,
          { type: 'complete', content: 'Interview completed! Great job!' }
        ]);
      } else {
        setQuestionNumber(response.question_number);
        
        setConversationHistory(prev => [
          ...prev,
          { type: 'question', content: response.question, number: response.question_number }
        ]);
        
        // Speak the next question
        speakText(response.question);
      }
      
      setUserAnswer("");
      
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to submit answer");
    } finally {
      setLoading(false);
    }
  };

  const handleEndInterview = () => {
    if (window.confirm("Are you sure you want to end the interview?")) {
      localStorage.removeItem('sessionId');
      navigate("/feedback");
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmitAnswer();
    }
  };

  if (isComplete) {
    return (
      <div className="page">
        <div className="completion-card">
          <div className="completion-icon">✓</div>
          <h1>Interview Complete!</h1>
          <p className="completion-text">
            You've successfully completed all {totalQuestions} questions.
          </p>
          <div className="completion-stats">
            <div className="stat-item">
              <div className="stat-number">{totalQuestions}</div>
              <div className="stat-label">Questions Answered</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">{conversationHistory.filter(h => h.type === 'answer').length}</div>
              <div className="stat-label">Responses Given</div>
            </div>
          </div>
          <div className="button-group">
            <button className="button primary" onClick={() => navigate("/")}>
              Start New Interview
            </button>
            <button className="button" onClick={() => navigate("/feedback")}>
              View Conversation
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page interview-page">
      <div className="page-header">
        <div>
          <div className="eyebrow">Step 2 of 2 • Interview in Progress</div>
          <h1>AI Interview Training</h1>
          <div className="progress-info">
            Question {questionNumber} of {totalQuestions}
          </div>
        </div>
        <button className="button secondary-button" onClick={handleEndInterview}>
          End Interview
        </button>
      </div>

      <div className="interview-container">
        {/* Progress Bar */}
        <div className="progress-bar-container">
          <div 
            className="progress-bar-fill" 
            style={{ width: `${(questionNumber / totalQuestions) * 100}%` }}
          />
        </div>

        {/* Conversation Thread */}
        <div className="conversation-thread">
          {conversationHistory.map((item, index) => (
            <div key={index} className={`message-bubble ${item.type}`}>
              {item.type === 'question' && (
                <div className="message-header">
                  <span className="message-icon"></span>
                  <span className="message-label">AI Interviewer</span>
                  {item.number && (
                    <span className="question-badge">Question {item.number}</span>
                  )}
                </div>
              )}
              {item.type === 'answer' && (
                <div className="message-header">
                  <span className="message-icon">👤</span>
                  <span className="message-label">You</span>
                </div>
              )}
              <div className="message-content">{item.content}</div>
            </div>
          ))}
          
          {loading && (
            <div className="message-bubble question loading-bubble">
              <div className="message-header">
                <span className="message-icon"></span>
                <span className="message-label">AI Interviewer</span>
              </div>
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
        </div>

        {/* Answer Input Section */}
        <div className="answer-section">
          <div className="answer-card">
            <label className="input-label">Your Answer</label>
            <div className="answer-input-group">
              <textarea
                ref={textareaRef}
                className="answer-textarea"
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your answer here or use the microphone..."
                rows="4"
                disabled={loading}
              />
              
              <div className="input-controls">
                <div className="controls-left">
                  {speechSupported && (
                    <button
                      className={`icon-button ${listening ? 'listening' : ''}`}
                      onClick={toggleListening}
                      disabled={loading}
                      title={listening ? "Stop recording" : "Start voice input"}
                    >
                      {listening ? '⏹' : '🎤'}
                      {listening && <span className="pulse-ring"></span>}
                    </button>
                  )}
                  <span className="char-count">{userAnswer.length} characters</span>
                </div>
                
                <button
                  className="button primary"
                  onClick={handleSubmitAnswer}
                  disabled={loading || !userAnswer.trim()}
                >
                  {loading ? 'Processing...' : 'Submit Answer →'}
                </button>
              </div>
            </div>
            
            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}
            
            <div className="hint-text">
              💡 Press Ctrl+Enter to submit • Use the microphone for voice input
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default InterviewPage;
