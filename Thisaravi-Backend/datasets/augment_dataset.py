
import json
import os
import sys
import ollama
from tqdm import tqdm
from pydantic import BaseModel
from typing import List, Optional, Union
import time
from google.api_core import exceptions
import google.genai as genai
from dotenv import load_dotenv
import logging
import itertools
from smart_generator import get_smart_data
from hf_uploader import upload_dataset


# --- Logging Setup ---
LOG_FILE = os.path.join(os.path.dirname(__file__), "generation.log")

# Create a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# File Handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Console Handler (Optional, keeps tqdm clean by writing to stderr/stdout appropriately)
# But since we use tqdm, we might just want logs in file and progress in console.
# We'll stick to file-only for INFO logs to keep console clean for tqdm, 
# unless it's a critical error.
logger.addHandler(file_handler)

def log_message(msg):
    logger.info(msg)
    # Also write to tqdm to avoid breaking progress bar in console
    tqdm.write(msg)


# --- Configuration ---
# Options: "v1" (Detailed Text), "v2" (Detailed JSON)
# Change this manually or via env var before running
GENERATION_MODE = os.getenv("GENERATION_MODE", "v1") 

SCRIPT_DIR = os.path.dirname(__file__)

# Allow the seed file to be overridden via env var.
# Set SEED_FILE=real_seeds.jsonl to use real student data collected from the app.
# Falls back to the synthetic seeds.jsonl if unset or if the real file has fewer
# than MIN_REAL_SEEDS entries.
MIN_REAL_SEEDS = int(os.getenv("MIN_REAL_SEEDS", "5"))
_env_seed = os.getenv("SEED_FILE", "")
if _env_seed:
    _candidate = os.path.join(SCRIPT_DIR, _env_seed) if not os.path.isabs(_env_seed) else _env_seed
    if os.path.exists(_candidate):
        with open(_candidate) as _f:
            _real_count = sum(1 for l in _f if l.strip())
        if _real_count >= MIN_REAL_SEEDS:
            INPUT_FILE = _candidate
            log_message(f"Using real student seeds: {INPUT_FILE} ({_real_count} entries)")
        else:
            INPUT_FILE = os.path.join(SCRIPT_DIR, "seeds.jsonl")
            log_message(f"Real seed file has only {_real_count} entries (< {MIN_REAL_SEEDS}), falling back to synthetic seeds.")
    else:
        INPUT_FILE = os.path.join(SCRIPT_DIR, "seeds.jsonl")
        log_message(f"SEED_FILE '{_env_seed}' not found, falling back to synthetic seeds.")
else:
    INPUT_FILE = os.path.join(SCRIPT_DIR, "seeds.jsonl")

TARGET_COUNT = 200

if GENERATION_MODE == "v1":
    OUTPUT_FILE = os.path.join(SCRIPT_DIR, "student_advisor_dataset_v1.jsonl")
    log_message(f"--- MODE: V1 (Detailed Text) -> {OUTPUT_FILE} ---")
else:
    OUTPUT_FILE = os.path.join(SCRIPT_DIR, "student_advisor_dataset_v2.jsonl")
    log_message(f"--- MODE: V2 (Detailed JSON) -> {OUTPUT_FILE} ---")

if os.getenv("TEST_MODE"):
    OUTPUT_FILE = os.path.join(SCRIPT_DIR, "test_sample.jsonl")
    TARGET_COUNT = 1
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE) # Start fresh for test
    log_message(f"--- TEST MODE: Generating 1 entry to {OUTPUT_FILE} ---")


# Load env vars
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    parent_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(parent_env)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_client = None
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY not found in environment variables. Gemini generation will not work.") # Keep print for immediate warn
    logger.warning("Warning: GEMINI_API_KEY not found in environment variables.")

# Configuration
PROVIDER = "ollama" # Options: "gemini", "ollama"
TEACHER_MODEL_GEMINI = os.getenv("TEACHER_MODEL_GEMINI")
TEACHER_MODEL_OLLAMA = os.getenv("TEACHER_MODEL_OLLAMA")

# --- Copied/Simplified from main.py to be Standalone ---

# Models
class StudentData(BaseModel):
    name: str
    current_role: str
    skills: List[str]
    experience_summary: str
    major: Optional[str] = "Undeclared"
    interests: Optional[List[str]] = []
    personality: Optional[str] = "ambitious, learner"

class JobData(BaseModel):
    role: str
    required_skills: List[str]
    description_summary: str

class ProjectRequest(BaseModel):
    student_data: StudentData
    job_data: JobData
    target_role: str

# --- Prompts ---

SYSTEM_PROMPT_JSON = """
You are an expert Technical Career Coach and Solutions Architect.
Your goal is to identify skill gaps and recommend a high-impact capstone project.

Output must be valid JSON with this structure:
{
    "gap_analysis": {
        "missing_skills": ["List", "of", "skills"],
        "match_percentage": <0-100>,
        "analysis_summary": "Detailed gap explanation. Write a full paragraph explaining WHY specific skills are missing relative to the job requirements. Use professional but encouraging tone."
    },
    "project_recommendation": {
        "project_title": "Impressive Project Name",
        "objective": "Primary learning goal.",
        "tech_stack": ["Tech1", "Tech2", "Tech3"],
        "implementation_steps": [
            "Step 1: Detailed Architectual Setup. Explain the environment setup, database choices, and initial project scaffolding in detail (3-4 sentences).", 
            "Step 2: Core Feature Implementation. Explain the backend logic, API design, or data processing steps involved (3-4 sentences).", 
            "Step 3: Frontend/Visualization. Describe how the user will interact with the system or how data will be presented (3-4 sentences).",
            "Step 4: Deployment & Polish. Explain deployment (Docker/Cloud) and final touches (CI/CD, README) (3-4 sentences)."
        ]
    }
}
"""

SYSTEM_PROMPT_TEXT = """
You are an expert Technical Career Coach and Solutions Architect.
Your goal is to identify skill gaps and recommend a high-impact capstone project.

Provide a highly detailed, professional response in the following format. Do NOT use JSON. Use clear headings.

### Gap Analysis
[Missing Skills]: List the key missing skills here.
[Match Score]: Provide a score (e.g., 75%).
[Analysis]: Write a comprehensive paragraph analyzing the student's current profile against the target role. Explain specifically what is lacking and why it matters for this role.

### Project Recommendation
**Title:** [Project Name]
**Objective:** [Project Objective]
**Tech Stack:** [List of Technologies]

**Implementation Plan:**
1. **[Step Name]**: Write a detailed explanation (3-4 sentences) of what to build in this step. Focus on architectural decisions and specific tools.
2. **[Step Name]**: Write a detailed explanation (3-4 sentences) of the implementation logic.
3. **[Step Name]**: Write a detailed explanation (3-4 sentences) covering the interface or data presentation layer.
4. **[Step Name]**: Write a detailed explanation (3-4 sentences) regarding testing, deployment, and documentation.
"""

def construct_smart_prompt(request: ProjectRequest, smart_data: dict, system_prompt: str) -> str:
    return f"""
    Analyze this student against the target job.
    
    I have prepared a DRAFT RECOMMENDATION based on domain expertise.
    USE THIS DRAFT as the core of your response, but expand on it with professional, encouraging language.
    Do not just copy it; Make it feel like a real mentorship session.
    
    DRAFT RECOMMENDATION:
    - Missing Skills: {", ".join(smart_data['missing_skills'])}
    - Match Score: {smart_data['match_score']}
    - Analysis: {smart_data['analysis']}
    - Project Title: {smart_data['project_title']}
    - Objective: {smart_data['objective']}
    - Tech Stack: {", ".join(smart_data['tech_stack'])}
    - Implementation Plan: {str(smart_data['implementation_plan'])}

    CRITICAL INSTRUCTION: Be extremely VERBOSE and DETAILED. 
    - The 'analysis_summary' (or Analysis section) should be a paragraph, not a sentence.
    - Each 'implementation_step' must be very detailed (3-4 sentences), explaining HOW and WHY.
    - Do not be concise. Be an expert mentor explaining the details.

    STUDENT PROFILE:
    Name: {request.student_data.name}
    Role: {request.student_data.current_role}
    Major: {request.student_data.major}
    Interests: {', '.join(request.student_data.interests)}
    Personality: {request.student_data.personality}
    Skills: {', '.join(request.student_data.skills)}
    Experience: {request.student_data.experience_summary}
    
    TARGET JOB:
    Role: {request.job_data.role}
    Required Skills: {', '.join(request.job_data.required_skills)}
    Description: {request.job_data.description_summary}
    
    {system_prompt}
    """

def generate_with_gemini(client, prompt):
    max_retries = 5
    retry_count = 0
    while retry_count < max_retries:
        try:
            response = client.models.generate_content(
                model=TEACHER_MODEL_GEMINI,
                contents=prompt,
            )
            return response.text
        except exceptions.ResourceExhausted:
            wait_time = 10 * (2 ** retry_count)
            log_message(f"Rate limit hit. Waiting {wait_time}s...")
            time.sleep(wait_time)
            retry_count += 1
        except Exception as e:
            if "429" in str(e):
                wait_time = 10 * (2 ** retry_count)
                log_message(f"Rate limit hit (generic). Waiting {wait_time}s...")
                time.sleep(wait_time)
                retry_count += 1
            else:
                log_message(f"Gemini API Error: {e}")
                return None
    return None

def generate_with_ollama(model_name, prompt):
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt}],
            options={'num_ctx': 4096} # Increase context window for verbose output
        )
        return response['message']['content']
    except Exception as e:
        log_message(f"Ollama Error: {e}")
        return None

def augment_dataset(
    custom_system_prompt: str = None,
    custom_output_file: str = None,
    custom_target_count: int = None,
    provider: str = None,
    custom_generation_mode: str = None,
):
    """
    Generate training data by augmenting seed entries with teacher model outputs.

    Args:
        custom_system_prompt: Override the default system prompt (used by evolution pipeline).
        custom_output_file: Override the default output file path.
        custom_target_count: Override the default target count (200).
        provider: Optional override of the LLM provider ("ollama" or "gemini").
                  If omitted the global PROVIDER value is used.
        custom_generation_mode: Override the generation mode ("v1" or "v2").
                  If omitted the global GENERATION_MODE value is used.
    """
    # Allow overrides for evolution pipeline
    active_mode = custom_generation_mode or GENERATION_MODE
    output_file = custom_output_file or OUTPUT_FILE
    target_count = custom_target_count or TARGET_COUNT

    log_message(f"Loading seeds from {INPUT_FILE}...")

    if not os.path.exists(INPUT_FILE):
        log_message(f"Seed file {INPUT_FILE} not found!")
        return

    # Resume logic
    start_index = 0
    if os.path.exists(output_file):
        with open(output_file, "r") as f_out:
            existing_lines = f_out.readlines()
            start_index = len(existing_lines)
            log_message(f"Resuming from index {start_index} (Target: {target_count})...")

    if start_index >= target_count:
         log_message(f"Target count {target_count} already reached. Exiting.")
         return

    with open(INPUT_FILE, "r") as f:
        lines = f.readlines()

    log_message(f"Found {len(lines)} seed entries.")

    # Validation: Ensure we have lines
    if len(lines) == 0:
        log_message("Error: Seed file is empty.")
        return

    # Cyclic Iterator
    lines_cycler = itertools.cycle(lines)

    entries_needed = target_count - start_index
    log_message(f"Need {entries_needed} more entries to reach {target_count}.")

    # Fast forward cycler
    drop_count = start_index % len(lines)
    for _ in range(drop_count):
        next(lines_cycler)

    # determine which provider we'll actually use for this run
    active_provider = provider or PROVIDER
    log_message(f"Starting generation using {active_provider} | MODE: {active_mode.upper()}")

    # Select System Prompt (custom overrides default)
    if custom_system_prompt:
        current_system_prompt = custom_system_prompt
    else:
        current_system_prompt = SYSTEM_PROMPT_TEXT if active_mode == "v1" else SYSTEM_PROMPT_JSON

    # Model Init
    gemini_model = None
    if active_provider == "gemini":
        gemini_model = gemini_client
    
    success_count = start_index
    pbar = tqdm(range(entries_needed), initial=start_index, total=target_count)
    
    for _ in pbar:
        line = next(lines_cycler)
        try:
            entry = json.loads(line)
            
            # 1. Extract User Content
            user_content_str = entry["messages"][0]["content"]
            user_json = json.loads(user_content_str)
            
            # 2. Map Keys
            s_data = user_json["student_data"]
            j_data = user_json["job_data"]

            student = StudentData(
                name="Student", 
                current_role=s_data.get("demographics", "Student"),
                skills=s_data.get("current_skills", []) if "current_skills" in s_data else s_data.get("skills", []),
                experience_summary="Student with academic background.",
                major=s_data.get("major", "Undeclared"),
                interests=s_data.get("interests", []),
                personality=s_data.get("personality", "")
            )
            
            job = JobData(
                role=j_data.get("target_job_role", "Target Role"),
                required_skills=j_data.get("required_skills", []),
                description_summary=j_data.get("description", "")
            )
            
            target_role = j_data.get("target_job_role", "Target Role")

            req = ProjectRequest(student_data=student, job_data=job, target_role=target_role)

            # 3. Construct Prompt (Smart-Guided)
            # Retrieve Expert Knowledge First
            smart_data = get_smart_data(s_data, j_data)
            full_prompt = construct_smart_prompt(req, smart_data, current_system_prompt)

            # 4. Generate
            teacher_output = ""
            try:
                if active_provider == "gemini":
                    teacher_output = generate_with_gemini(gemini_model, full_prompt)
                elif active_provider == "ollama":
                    teacher_output = generate_with_ollama(TEACHER_MODEL_OLLAMA, full_prompt)
            except Exception as e:
                log_message(f"API Generation failed: {e}")

            if not teacher_output or len(teacher_output) < 10:
                log_message(f"API failed to produce quality results for {student.current_role}. Skipping.")
                continue

            # 5. Validate & Save
            # Simple check: Ensure output isn't empty. 
            # For JSON mode, we ideally want { and }, but let's be lenient to capture "mostly correct" data that we can clean.
            # actually, for consistency, let's enforce lenient basic checks.
            
            is_valid = False
            if active_mode == "v2": # JSON
                if "{" in teacher_output and "}" in teacher_output:
                    is_valid = True
            else: # Text
                if len(teacher_output) > 50: # Arbitrary length check
                    is_valid = True
            
            if is_valid:
                new_entry = {
                    "messages": [
                        {"role": "user", "content": user_content_str},
                        {"role": "model", "content": teacher_output}
                    ]
                }
                with open(output_file, "a") as f:
                    f.write(json.dumps(new_entry) + "\n")
                success_count += 1
            else:
                pass # Silent fail for cleanliness in logs
                
        except Exception as e:
            pass # Skip errorszx

    log_message(f"Done! {success_count} entries saved to {output_file}.")

    # --- Auto-upload to HuggingFace Hub ---
    if success_count > 0 and os.path.exists(output_file):
        log_message("[HF Upload] Uploading dataset to HuggingFace Hub...")
        upload_success = upload_dataset(
            file_path=output_file,
            commit_message=f"Auto-upload: {os.path.basename(output_file)} ({success_count} entries, mode={active_mode})",
        )
        if not upload_success:
            log_message("[HF Upload] Auto-upload failed; manual retry will be available in the admin UI.")
    else:
        log_message("[HF Upload] No entries generated; skipping upload.")

if __name__ == "__main__":
    augment_dataset()
