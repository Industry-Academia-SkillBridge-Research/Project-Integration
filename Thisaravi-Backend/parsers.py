import re
import json


def extract_json(text: str) -> dict:
    """Extracts JSON from markdown code blocks or raw strings"""
    try:
        # 1. Try finding markdown JSON block
        match = re.search(r'```json\s+(.*?)\s+```', text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip()
            # Try parsing the whole block content first
            try:
                data = json.loads(content)
                if isinstance(data, dict): return data
            except json.JSONDecodeError:
                # If that fails, try finding the biggest { } block inside the backticks
                first_brace = content.find('{')
                last_brace = content.rfind('}')
                while first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    candidate = content[first_brace:last_brace+1]
                    try:
                        data = json.loads(candidate)
                        if isinstance(data, dict): return data
                    except json.JSONDecodeError:
                        last_brace = content.rfind('}', 0, last_brace)

        # 2. Try to find the largest valid { ... } in the entire text
        # (Handles cases where JSON is not in backticks or backticks are malformed)
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        
        while first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            # Optimization: only try if the substring length is significant
            if (last_brace - first_brace) < 20: break
            
            candidate = text[first_brace:last_brace+1]
            try:
                data = json.loads(candidate)
                # Success if it's a dict
                if isinstance(data, dict): return data
            except json.JSONDecodeError:
                pass
            
            # Move last_brace back to find a smaller candidate that might be valid
            last_brace = text.rfind('}', 0, last_brace)
        
        return {}
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
    
    # We check for a significant dictionary output before trying to normalize
    if json_data and isinstance(json_data, dict) and len(json_data) > 0:
        # Normalize the JSON structure to the one expected by the frontend
        normalized = {
            "gap_analysis": {
                "analysis_summary": "",
                "match_percentage": 0,
                "missing_skills": []
            },
            "project_recommendation": {
                "project_title": "",
                "objective": "",
                "tech_stack": [],
                "implementation_steps": []
            }
        }

        # Extract Gap Analysis
        if "gap_analysis" in json_data:
            ga = json_data["gap_analysis"]
            normalized["gap_analysis"]["analysis_summary"] = ga.get("analysis_summary", "")
            normalized["gap_analysis"]["match_percentage"] = ga.get("match_percentage", 0)
            
            # dataset uses 'primary_skill_gap' or 'missing_skills'
            missing = ga.get("missing_skills", [])
            if not missing and "primary_skill_gap" in ga:
                val = ga["primary_skill_gap"]
                missing = [s.strip() for s in val.split(",")] if isinstance(val, str) else val
            normalized["gap_analysis"]["missing_skills"] = missing
        
        # Fallback for analysis_summary if gaps exist but summary is empty
        if not normalized["gap_analysis"]["analysis_summary"] and "gap_analysis" in json_data:
             # Basic heuristic: use the first 2-3 lines of text if everything is flat
             pass

        # Extract Project Recommendation
        if "project_recommendation" in json_data:
            pr = json_data["project_recommendation"]
            normalized["project_recommendation"]["project_title"] = pr.get("title") or pr.get("project_title", "Recommended Capstone")
            normalized["project_recommendation"]["objective"] = pr.get("goal") or pr.get("objective", "Capstone Project")
            
            # dataset uses 'skills_required' or 'tech_stack'
            stack = pr.get("tech_stack") or pr.get("skills_required", [])
            normalized["project_recommendation"]["tech_stack"] = stack

            # dataset implementation_steps is list of dicts with 'step' and 'details'
            steps = pr.get("implementation_steps", [])
            parsed_steps = []
            for item in steps:
                if isinstance(item, dict):
                    # Try 'details' or 'description'
                    step_num = item.get('step', '')
                    step_desc = item.get('details') or item.get('description', '')
                    step_text = f"Step {step_num}: {step_desc}".strip(": ")
                    parsed_steps.append(step_text)
                else:
                    parsed_steps.append(str(item))
            normalized["project_recommendation"]["implementation_steps"] = parsed_steps

        # Final check: If we have successfully filled at least the title or summary, return it
        if normalized["project_recommendation"]["project_title"] or normalized["gap_analysis"]["analysis_summary"]:
            return normalized
        
    # 2. Attempt Structured Text Parsing (Fine-tuned Model)
    text_data = parse_structured_text(text)
    if text_data and "gap_analysis" in text_data:
        return text_data
        
    # 3. Fallback / Error
    return {
        "error": "Could not parse output",
        "raw_text": text
    }
