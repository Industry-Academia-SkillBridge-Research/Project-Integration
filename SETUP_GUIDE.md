# Project Setup Guide

## Database: MySQL
- **Host**: localhost:3306
- **Database**: `oauth_users`
- **User**: root
- **Data Storage**: `candidates` table

## Setup Steps

### 1. Run Database Migration

```bash
# Navigate to login directory
cd e:\Integration\login

# Run the MySQL migration script
mysql -u root -p oauth_users < migrations/001_add_analysis_fields_mysql.sql
# Password: tharusha2001
```

This adds 7 new columns to store analysis results:
- `latest_analysis_date` - When analysis was last run
- `readiness_score` - Score 0-100
- `skill_gap_index` - JSON array of skill gaps
- `ai_explanation` - AI-generated career insights
- `matched_skills` - JSON array of matched skills with confidence
- `missing_skills` - JSON array of missing skills
- `analysis_summary` - Brief text summary

### 2. Start Backend (Login API)

```bash
cd e:\Integration\login
uvicorn app.main:app --reload --port 8182
```

Runs on: http://localhost:8182

### 3. Start Frontend

```bash
cd e:\Integration\NewFrontend
npm run dev
```

Runs on: http://localhost:8080

### 4. Test the Feature

1. **Login** → Google OAuth
2. **Go to Personalized Learning Path** → Upload CV, select role
3. **Wait for analysis** → Pipeline completes (6 stages)
4. **Check Profile page** → See "Latest Career Analysis" card with:
   - Readiness score progress bar
   - Matched skills (green badges)
   - Missing skills (amber badges)
   - AI explanation
5. **Logout and login again** → Data persists

## Data Flow

```
CV Upload → Pipeline Analysis → Saves to MySQL
                                    ↓
                              candidates table
                                    ↓
                              Profile displays
```

## Verify Migration

Check if columns were added:

```sql
DESCRIBE candidates;
```

Should show the 7 new columns at the bottom.

## Troubleshooting

**Migration fails**: Check if columns already exist
```sql
SELECT * FROM information_schema.columns 
WHERE table_schema = 'oauth_users' 
AND table_name = 'candidates' 
AND column_name LIKE '%analysis%';
```

**Data not saving**: Check browser console for errors after pipeline completes

**Data not loading**: Check Network tab for `/candidate/me` response
