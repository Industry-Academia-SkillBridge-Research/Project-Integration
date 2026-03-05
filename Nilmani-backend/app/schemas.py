from pydantic import BaseModel
from typing import List, Optional

class StartInterviewResponse(BaseModel):
    session_id: str
    question: str

class AnswerRequest(BaseModel):
    session_id: str
    answer: str

class AnswerResponse(BaseModel):
    feedback: Optional[str]
    next_question: Optional[str]
    interview_ended: bool
