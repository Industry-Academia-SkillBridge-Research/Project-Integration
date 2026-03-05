from app.services.openai_client import get_client
from app.interview.prompts import INTERVIEW_PROMPT, EVALUATION_PROMPT
from app.core.config import settings


class InterviewSession:
    """
    Manages the interview conversation flow using RAG for context-aware questions.
    """

    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.client = get_client()
        self.history = []
        self.question_count = 0
        self.max_questions = settings.MAX_INTERVIEW_QUESTIONS

    def retrieve_context(self, query: str) -> str:
        docs = self.vectorstore.similarity_search(query, k=5)
        return "\n\n".join(d["page_content"] for d in docs)

    def ask_next_question(self, user_answer: str | None = None) -> str:
        if user_answer:
            self.history.append({"role": "user", "content": user_answer})

        # 🔹 JD-anchored queries (NOT abstract)
        if not user_answer:
            query = "skills, technologies, tools, and responsibilities mentioned in this job description"
        else:
            query = f"job responsibilities and skills related to: {user_answer}"

        context = self.retrieve_context(query)

        # HARD STOP → prevents hallucination
        if len(context.strip()) < 200:
            return "I need more information from the Job Description to continue the interview."

        # SINGLE authoritative system prompt (CRITICAL FIX)
        system_prompt = f"""
            You are an AI Interviewer conducting a professional technical interview.

            STRICT RULES (MANDATORY):
            - Ask questions ONLY based on the Job Description below
            - DO NOT ask math problems, puzzles, riddles, or theory questions
            - DO NOT include answers, explanations, or hints
            - Ask EXACTLY ONE interview question
            - No apologies, no corrections, no extra text

            JOB DESCRIPTION (ONLY SOURCE OF TRUTH):
            =====================================
            {context}
            =====================================

            TASK:
            Ask ONE interview question based strictly on the Job Description above.
            Output ONLY the interview question.
            """

        messages = [{"role": "system", "content": system_prompt}] + self.history

        response = self.client.chat(
            model=settings.OLLAMA_MODEL,
            messages=messages,
            options={
                "temperature": 0.2,   # deterministic
                "num_predict": 80
            }
        )

        question = response["message"]["content"].strip()

        self.history.append({"role": "assistant", "content": question})
        self.question_count += 1
        return question

    def evaluate_answer(self, question: str, answer: str) -> dict:
        query = f"skills and requirements related to: {question}"
        context = self.retrieve_context(query)

        messages = [
            {"role": "system", "content": EVALUATION_PROMPT},
            {
                "role": "system",
                "content": f"""
                    Job Description Context:
                    ========================
                    {context}
                    ========================

                    Question: {question}
                    Candidate Answer: {answer}

                    Evaluate strictly based on the JD above.
                    """
            }
        ]

        response = self.client.chat(
            model=settings.OLLAMA_MODEL,
            messages=messages,
            options={"temperature": 0.5, "num_predict": 200}
        )

        return {
            "question": question,
            "answer": answer,
            "feedback": response["message"]["content"].strip()
        }





# from app.services.openai_client import get_client
# from app.interview.prompts import INTERVIEW_PROMPT, EVALUATION_PROMPT
# from app.core.config import settings


# class InterviewSession:
#     """
#     Manages the interview conversation flow using RAG for context-aware questions.
#     """
    
#     def __init__(self, vectorstore):
#         self.vectorstore = vectorstore
#         self.client = get_client()
#         self.history = []
#         self.question_count = 0
#         self.max_questions = settings.MAX_INTERVIEW_QUESTIONS

#     def retrieve_context(self, query: str) -> str:
#         """
#         Use RAG to retrieve relevant context from job description.
#         Retrieves top-k most relevant chunks based on semantic similarity.
#         """
#         docs = self.vectorstore.similarity_search(query, k=5)
#         context = "\n\n".join([d["page_content"] for d in docs])
#         return context

#     def ask_next_question(self, user_answer: str | None = None) -> str:
#         """
#         Generate next interview question based on conversation history and JD context.
#         Uses RAG to ground questions in the actual Job Description.
#         """
#         if user_answer:
#             self.history.append({"role": "user", "content": user_answer})

#         # Retrieve relevant context from JD using RAG with improved queries
#         # For first question: get comprehensive JD overview
#         # For subsequent questions: retrieve context related to previous answer
#         if not user_answer:
#             query = "required technical skills, qualifications, responsibilities, experience requirements, and key competencies for this job position"
#         else:
#             query = f"technical skills, tools, technologies, and job responsibilities relevant to: {user_answer[:200]}"
        
#         context = self.retrieve_context(query)
        
#         # DEBUG: Verify retrieved context (CRITICAL for troubleshooting)
#         print("\n" + "="*80)
#         print("RETRIEVED JD CONTEXT:")
#         print("="*80)
#         print(context[:500] + "..." if len(context) > 500 else context)
#         print("="*80 + "\n")

#         # Build messages with STRICT system prompt + EXPLICIT JD context injection
#         messages = [
#             {"role": "system", "content": INTERVIEW_PROMPT},
#             {
#                 "role": "system", 
#                 "content": f"""Job Description Context (USE THIS TO ASK YOUR QUESTION):
# ========================
# {context}
# ========================

# Based STRICTLY on the Job Description context above, ask ONE interview question.
# DO NOT include the answer."""
#             },
#         ] + self.history

#         # Get response from Ollama
#         response = self.client.chat(
#             model=settings.OLLAMA_MODEL,
#             messages=messages,
#             options={
#                 "temperature": 0.7,
#                 "num_predict": 150  # Reduced to prevent long answers
#             }
#         )

#         question = response["message"]["content"]
        
#         # DEBUG: Show generated question
#         print(f"GENERATED QUESTION: {question}\n")
        
#         self.history.append({"role": "assistant", "content": question})
#         self.question_count += 1

#         return question

#     def evaluate_answer(self, question: str, answer: str) -> dict:
#         """
#         Evaluate candidate's answer based on JD context.
#         Returns feedback and score (1-5).
        
#         This is a SEPARATE LLM call from question generation.
#         """
#         # Retrieve relevant JD context for evaluation
#         query = f"skills and requirements related to: {question[:200]}"
#         context = self.retrieve_context(query)
        
#         messages = [
#             {"role": "system", "content": EVALUATION_PROMPT},
#             {
#                 "role": "system",
#                 "content": f"""Job Description Context:
# ========================
# {context}
# ========================

# Question Asked: {question}
# Candidate's Answer: {answer}

# Evaluate the answer based on the JD context above."""
#             }
#         ]
        
#         response = self.client.chat(
#             model=settings.OLLAMA_MODEL,
#             messages=messages,
#             options={"temperature": 0.5, "num_predict": 200}
#         )
        
#         feedback = response["message"]["content"]
        
#         print(f"EVALUATION: {feedback}\n")
        
#         return {
#             "feedback": feedback,
#             "question": question,
#             "answer": answer
#         }

