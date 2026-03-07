import json
import csv
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Read the JSON file
with open(os.path.join(script_dir, 'Job_data.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

# Define CSV columns
fieldnames = [
    'job_id', 'title', 'company', 'location', 'posted_date', 'job_url', 
    'scraped_at', 'description', 'seniority_level', 'employment_type', 
    'job_function', 'industries', 'skills', 'role_tag', 'role_key', 'job_role_id'
]

# Write to CSV
with open(os.path.join(script_dir, 'Job_data.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    
    for job in data:
        # Flatten the criteria object
        criteria = job.get('criteria', {})
        
        # Convert skills array to pipe-separated string
        skills = ' | '.join(job.get('skills', []))
        
        row = {
            'job_id': job.get('job_id', ''),
            'title': job.get('title', ''),
            'company': job.get('company', ''),
            'location': job.get('location', ''),
            'posted_date': job.get('posted_date', ''),
            'job_url': job.get('job_url', ''),
            'scraped_at': job.get('scraped_at', ''),
            'description': job.get('description', ''),
            'seniority_level': criteria.get('Seniority level', ''),
            'employment_type': criteria.get('Employment type', ''),
            'job_function': criteria.get('Job function', ''),
            'industries': criteria.get('Industries', ''),
            'skills': skills,
            'role_tag': job.get('role_tag', ''),
            'role_key': job.get('role_key', ''),
            'job_role_id': job.get('job_role_id', '')
        }
        
        writer.writerow(row)

print(f"Conversion complete! Processed {len(data)} job entries.")
print(f"Output file: {os.path.join(script_dir, 'Job_data.csv')}")
