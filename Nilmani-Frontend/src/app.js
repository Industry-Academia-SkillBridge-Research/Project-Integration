import { BrowserRouter, Routes, Route } from "react-router-dom";
import UploadJDPage from "./pages/upload_jd_page.js";
import InterviewPage from "./pages/interview_page.js";
import FeedbackPage from "./pages/feedback_page.js";
import { JobProvider } from "./job_context";

function App() {
  return (
    <JobProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<UploadJDPage />} />
          <Route path="/interview" element={<InterviewPage />} />
          <Route path="/feedback" element={<FeedbackPage />} />
        </Routes>
      </BrowserRouter>
    </JobProvider>
  );
}

export default App;
