
import json
from parsers import parse_response

def test_dataset_extraction():
    dataset_path = 'c:\\Users\\Thisaravi\\Dev\\Project-Integration\\Thisaravi-Backend\\datasets\\student_advisor_dataset_v1_evolved_4.jsonl'
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        data = json.loads(line)
        model_output = data['messages'][1]['content']
        
        parsed = parse_response(model_output)
        
        print(f"--- Sample {i+1} ---")
        if "error" in parsed:
            print(f"FAILED: {parsed['error']}")
        else:
            print("SUCCESS")
            # print(json.dumps(parsed, indent=2))
            # Basic validation
            ga = parsed.get("gap_analysis", {})
            pr = parsed.get("project_recommendation", {})
            print(f"  Title: {pr.get('project_title')}")
            print(f"  Gap Title: {ga.get('analysis_summary')[:50]}...")
            print(f"  Steps Count: {len(pr.get('implementation_steps', []))}")
            if not pr.get('project_title') or not pr.get('implementation_steps'):
                print("  WARNING: Missing key fields!")
        print("-" * 20)

if __name__ == "__main__":
    test_dataset_extraction()
