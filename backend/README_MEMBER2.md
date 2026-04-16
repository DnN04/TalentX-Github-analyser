# GitHub Talent Analyzer — Backend (Member 2)

## Your Files
| File | Purpose |
|------|---------|
| `main.py` | FastAPI app — main entry point |
| `score_calculator.py` | Talent score formula + skill level logic |
| `explainer.py` | Human-readable score explanations |
| `requirements.txt` | All Python dependencies |
| `test_api.py` | API tests (pytest) |
| `.env.example` | Template for your GitHub token |

## Setup Steps

### Step 1 — Install Python (3.10+)
Make sure Python is installed: `python --version`
#### backend
cd backend
### Step 2 — Create virtual environment
```bash
# python -m venv venv
py -3.11 -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```
.\venv\Scripts\activate
### Step 4 — Add GitHub Token
```bash
cp .env.example .env
# Open .env and paste your GitHub Personal Access Token
# Get one at: https://github.com/settings/tokens
# Needs NO special permissions (public data only)
```

### Step 5 — Run the server
```bash
uvicorn main:app --reload
```
Server runs at: http://localhost:8000

## API Endpoints

### POST /analyze
```json
Request:  { "username": "torvalds" }

Response: {
  "username": "torvalds",
  "name": "Linus Torvalds",
  "avatar_url": "...",
  "talent_score": 87.5,
  "skill_level": "Expert",
  "top_languages": ["C", "Python", "Shell"],
  "strengths": ["High commit activity", "Community recognition"],
  "feature_contributions": {
    "commits": 30.0,
    "repos": 18.0,
    "stars": 20.0,
    "languages": 27.0
  },
  "explanation": ["✅ Strong commit history...", ...],
  "raw_metrics": { "commits": 450, "repos": 12, "stars": 180, ... }
}
```

### GET /health
Returns `{ "status": "ok", "model_loaded": true/false }`

## Run Tests
```bash
pytest test_api.py -v
```

## Integration with Other Members
- **Member 1** will give you `trained_model.pkl` — drop it in this folder, the API auto-loads it
- **Member 3** (Frontend) calls `POST /analyze` — CORS is already configured for localhost:3000 and localhost:5173
- **Member 4** (XAI/Tests) may add SHAP to explainer.py — drop-in compatible

## Interactive API Docs
Visit http://localhost:8000/docs — FastAPI auto-generates a full Swagger UI
