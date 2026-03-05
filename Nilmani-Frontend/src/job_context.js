import { createContext, useContext, useMemo, useState } from "react";

const JobContext = createContext(null);

const cleanText = (text) => (text || "").replace(/\s+/g, " ").trim();

const keywordQuestions = [
  { keyword: "react", prompt: "Walk me through a React project you shipped and your specific contributions." },
  { keyword: "node", prompt: "Describe how you would design a resilient Node.js API for this role." },
  { keyword: "python", prompt: "What Python libraries would you choose for this job and why?" },
  { keyword: "ml", prompt: "How would you apply machine learning to the requirements you read?" },
  { keyword: "data", prompt: "Tell me about a data pipeline you built and how you validated data quality." },
  { keyword: "cloud", prompt: "Explain how you would deploy this product securely in the cloud." },
  { keyword: "lead", prompt: "Share a time you led a team through ambiguity for a delivery." },
  { keyword: "design", prompt: "How do you approach designing user experiences for this problem space?" }
];

const deriveQuestions = (text) => {
  const base = [
    "Give me a 60-second overview of why you fit this role.",
    "Tell me about a challenging situation from the job description that you have handled before.",
    "How would you measure success in this role in the first 90 days?"
  ];

  const normalized = cleanText(text).toLowerCase();
  const picks = new Set(base);

  keywordQuestions.forEach(({ keyword, prompt }) => {
    if (normalized.includes(keyword)) picks.add(prompt);
  });

  if (cleanText(text).length > 600 && !normalized.includes("stakeholder")) {
    picks.add("How will you align stakeholders with competing priorities?");
  }

  return Array.from(picks).slice(0, 8);
};

const summarize = (text) => {
  const snippet = cleanText(text);
  if (!snippet) return "";
  if (snippet.length <= 420) return snippet;
  return `${snippet.slice(0, 420)}...`;
};

export function JobProvider({ children }) {
  const [fileMeta, setFileMeta] = useState({ name: null, size: 0 });
  const [extractedText, setExtractedText] = useState("");

  const saveExtraction = ({ name, size, text }) => {
    setFileMeta({ name, size });
    setExtractedText(cleanText(text));
  };

  const clearJob = () => {
    setFileMeta({ name: null, size: 0 });
    setExtractedText("");
  };

  const summary = useMemo(() => summarize(extractedText), [extractedText]);
  const questions = useMemo(() => deriveQuestions(extractedText), [extractedText]);

  return (
    <JobContext.Provider
      value={{
        fileMeta,
        extractedText,
        summary,
        questions,
        saveExtraction,
        clearJob
      }}
    >
      {children}
    </JobContext.Provider>
  );
}

export const useJobContext = () => {
  const ctx = useContext(JobContext);
  if (!ctx) throw new Error("useJobContext must be used within JobProvider");
  return ctx;
};
