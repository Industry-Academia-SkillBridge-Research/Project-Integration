import re
import json


def extract_json(text: str) -> dict:
    """Extracts JSON from markdown code blocks or raw strings"""
    try:
        # Try finding markdown JSON block
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match: return json.loads(match.group(1))
        
        # Try finding raw JSON object
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match: return json.loads(match.group(1))
        
        # Try regular load
        return json.loads(text)
    except Exception:
        return {}


def parse_structured_text(text: str) -> dict:
    """
    Parses the raw text output from the fine-tuned Gemma model into structured JSON.
    
    Expected Text Format:
    Gap Analysis: <text> 
    Match Score: <number>% 
    Project Recommendation: <title> 
    Tech Stack: <list> 
    Steps: <list>
    """
    try:
        # Regex Extraction - Fuzzy / Robust
        # 1. Gap Analysis: Look for "Gap Analysis" or "Analysis" header
        # Followed by colon/space OR newline
        gap_match = re.search(r'(?:Gap Analysis|Analysis)(?:[:\s-]*|\s*\n)(.*?)(?=(?:\*\*|#|Match Score|Project)|$)', text, re.DOTALL | re.IGNORECASE)
        
        # 2. Match Score: Look for "Match Score" or just a percentage near the top if specific header missing
        score_match = re.search(r'Match Score[^\d]*(\d+)', text, re.IGNORECASE)
        
        # 3. Project Rec: Look for "Project Recommendation" etc.
        proj_match = re.search(r'(?:Project Recommendation|Recommended Project|Project)(?:[:\s-]*|\s*\n)(.*?)(?=(?:\*\*|#|Tech Stack)|$)', text, re.DOTALL | re.IGNORECASE)
        
        # 4. Tech Stack: "Tech Stack"
        stack_match = re.search(r'(?:Tech Stack|Technologies|Stack)(?:[:\s-]*|\s*\n)(.*?)(?=(?:\*\*|#|Steps|Implementation)|$)', text, re.DOTALL | re.IGNORECASE)
        
        # 5. Steps: "Steps"
        steps_match = re.search(r'(?:Steps|Implementation|Plan)(?:[:\s-]*|\s*\n)(.*)', text, re.DOTALL | re.IGNORECASE)

        # Fallback for Gap Analysis if regex failed but we have text
        gap_text = gap_match.group(1).strip() if gap_match else (text[:500] + "..." if len(text) > 500 else text)

        # Parsing Lists (Tech Stack & Steps)
        raw_stack = stack_match.group(1).strip() if stack_match else ""
        tech_stack = [s.strip() for s in re.split(r',|and|\n|-|\*|;', raw_stack) if s.strip()]
        
        raw_steps = steps_match.group(1).strip() if steps_match else ""
        steps = [s.strip() for s in re.split(r'\d+\.|-|\*', raw_steps) if s.strip()]

        # Construct JSON even if some matches failed (Best Effort)
        data = {
            "gap_analysis": {
                "analysis_summary": gap_text,
                "match_percentage": int(score_match.group(1)) if score_match else 0,
                "missing_skills": [] 
            },
            "project_recommendation": {
                "project_title": proj_match.group(1).strip() if proj_match else "Recommended Capstone",
                "objective": "Capstone Project",
                "tech_stack": tech_stack if tech_stack else ["Python", "General Dev"],
                "implementation_steps": steps if steps else ["Review full analysis for details."]
            }
        }
        return data
            
    except Exception as e:
        print(f"Parser Exception: {e}")
        return {"error": f"Failed to parse text: {str(e)}", "raw_text": text}


def parse_response(text: str) -> dict:
    """
    Master parsing function that attempts to handle both JSON and Structured Text formats.
    """
    # 1. Attempt JSON Parsing first (Generic Models)
    json_data = extract_json(text)
    if json_data and "gap_analysis" in json_data:
        return json_data
        
    # 2. Attempt Structured Text Parsing (Fine-tuned Model)
    text_data = parse_structured_text(text)
    if text_data and "gap_analysis" in text_data:
        return text_data
        
    # 3. Fallback / Error
    return {
        "error": "Could not parse output",
        "raw_text": text
    }
