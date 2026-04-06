import json
import os
import random
import thisaravi
from tqdm import tqdm

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(__file__)
SEEDS_FILE = os.path.join(SCRIPT_DIR, "seeds.jsonl")
MODEL_NAME = "qwen3-coder:30b" # Or any available model

# --- Curated Archetypes (The 50+ diverse roles we want to preserve) ---
ARCHETYPES = [
    # Medical
    "Nurse (5 years exp)", "Dental Hygienist", "Veterinarian", "Pharmacist", "Physical Therapist", "Radiologist Assistant", "Paramedic",
    # Finance/Quant
    "Financial Analyst", "Undergraduate, Physics (Quant)", "PhD, Statistics", "MBA Student",
    # Arts/Creative
    "Graphic Designer", "Video Editor", "Sound Designer", "Novelist", "Poet", "Interior Designer", "Stand-up Comedian", "Stunt Performer",
    # Service/Social
    "Chef", "Travel Agent", "Event Planner", "Social Worker", "Crisis Counselor", "Body Language Expert", "Journalist",
    # Industry/Transport
    "Civil Engineer", "Mechanical Engineer", "Commercial Pilot", "Air Traffic Controller", "Ship Captain", "Miner", "Oil Rig Engineer", 
    # Safety/Security
    "Police Officer", "Homicide Detective", "Private Investigator", "Security Guard", "Bodyguard", "Infantry Officer", "Intelligence Officer", "Diplomat",
    # Niche/Academic
    "Epigrapher", "Urban Explorer", "Zookeeper", "Park Ranger", "Rare Book Archivist", "Fact Checker", "Field Linguist"
]

GENERATION_PROMPT = """
You are a Data Generator. Generate a realistic student profile for the following SPECIFIC role: "{role}".
The student is looking to become a Data Scientist or similar technical role.

Schema:
{{
    "student_data": {{
        "demographics": "{role}",
        "major": "Relevant Major",
        "interests": ["Interest 1", "Interest 2"],
        "current_skills": ["Skill 1", "Skill 2"],
        "personality": "Personality adjectives"
    }},
    "job_data": {{
        "target_job_role": "Target Tech Role (e.g. Health Informatics, Crime Analyst, etc.)",
        "required_skills": ["Req Skill 1", "Req Skill 2"],
        "description": "Brief job expectation"
    }}
}}

Output ONLY valid JSON.
"""

def generate_profile_for_role(role):
    prompt = GENERATION_PROMPT.format(role=role)
    try:
        resp = thisaravi.chat(model=MODEL_NAME, messages=[
            {"role": "user", "content": prompt}
        ])
        content = resp['message']['content']
        # Cleaner
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return json.loads(content)
    except Exception as e:
        print(f"Error generating for {role}: {e}")
        return None

def main():
    print(f"Generating seeds for {len(ARCHETYPES)} curated archetypes...")
    
    # We want to ensure these specific archetypes exist in the seeds file
    # If the file exists, we check what's missing. If not, we start fresh.
    
    existing_roles = set()
    if os.path.exists(SEEDS_FILE):
        with open(SEEDS_FILE, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    content = json.loads(data["messages"][0]["content"])
                    role = content["student_data"]["demographics"]
                    existing_roles.add(role)
                except:
                    pass
    
    print(f"Found {len(existing_roles)} existing roles.")
    
    new_entries = []
    
    # Cycle through our curated list. 
    # If we need more than len(ARCHETYPES), we can add variatons or generic ones.
    # For now, let's just make sure we have coverage.
    
    for arc in tqdm(ARCHETYPES):
        # We can loosely match existing to skip duplicates if desired
        # But for 'regeneration' we might want to overwrite or add.
        # Let's just generate and append for now, user can deduce/clean later.
        
        profile = generate_profile_for_role(arc)
        if profile:
            # Format for Seed File
            json_str = json.dumps(profile)
            entry = {
                "messages": [
                    {"role": "user", "content": json_str}
                ]
            }
            new_entries.append(json.dumps(entry))
            
    # Write to file (Append mode or Overwrite? User said "single handedly create", implies overwrite capability)
    # But usually we append. Let's Append.
    
    with open(SEEDS_FILE, "a") as f:
        for line in new_entries:
            f.write(line + "\n")
            
    print(f"Added {len(new_entries)} curated seeds to {SEEDS_FILE}")

if __name__ == "__main__":
    main()
