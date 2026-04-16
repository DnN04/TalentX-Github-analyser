from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import joblib
import numpy as np
from score_calculator import calculate_score, get_skill_level, get_strengths
from app.xai.explainer import explain_as_strings  # ✅ ONLY THIS

app = FastAPI(title="GitHub Talent Analyzer API", version="1.0.0")

# Allow React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# Load ML model
try:
    model = joblib.load("trained_model.pkl")
    MODEL_AVAILABLE = True
    print("✅ ML model loaded successfully")
except FileNotFoundError:
    model = None
    MODEL_AVAILABLE = False
    print("⚠️ trained_model.pkl not found — using rule-based skill level")


class AnalyzeRequest(BaseModel):
    username: str


def get_github_headers():
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def fetch_github_data(username: str) -> dict:
    headers = get_github_headers()
    base = "https://api.github.com"

    user_resp = requests.get(f"{base}/users/{username}", headers=headers)
    if user_resp.status_code == 404:
        raise HTTPException(status_code=404, detail=f"GitHub user '{username}' not found.")
    if user_resp.status_code == 403:
        raise HTTPException(status_code=429, detail="GitHub API rate limit hit.")
    if user_resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch GitHub user data.")

    user_data = user_resp.json()
    public_repos = user_data.get("public_repos", 0)
    followers = user_data.get("followers", 0)

    repos_resp = requests.get(
        f"{base}/users/{username}/repos",
        headers=headers,
        params={"per_page": 100}
    )
    repos = repos_resp.json() if repos_resp.status_code == 200 else []

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    languages = {r["language"] for r in repos if r.get("language")}

    lang_count = {}
    for r in repos:
        lang = r.get("language")
        if lang:
            lang_count[lang] = lang_count.get(lang, 0) + 1
    top_languages = sorted(lang_count, key=lang_count.get, reverse=True)[:5]

    events_resp = requests.get(
        f"{base}/users/{username}/events/public",
        headers=headers,
        params={"per_page": 100}
    )
    events = events_resp.json() if events_resp.status_code == 200 else []
    commit_count = sum(
        len(e.get("payload", {}).get("commits", []))
        for e in events if e.get("type") == "PushEvent"
    )

    if commit_count == 0:
        commit_count = min(followers * 2, 500)

    return {
        "commits": commit_count,
        "repos": public_repos,
        "stars": total_stars,
        "languages_count": len(languages),
        "top_languages": top_languages,
        "followers": followers,
        "name": user_data.get("name") or username,
        "avatar_url": user_data.get("avatar_url", ""),
        "bio": user_data.get("bio", ""),
        "location": user_data.get("location", ""),
    }


@app.get("/")
def root():
    return {"message": "GitHub Talent Analyzer API is running 🚀"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    username = request.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty.")

    github_data = fetch_github_data(username)

    commits = github_data["commits"]
    repos = github_data["repos"]
    stars = github_data["stars"]
    languages_count = github_data["languages_count"]

    # Talent score
    talent_score = calculate_score(commits, repos, stars, languages_count)

    # Skill level
    if MODEL_AVAILABLE and model is not None:
        features = np.array([[commits, repos, stars, languages_count]])
        skill_level = model.predict(features)[0]
    else:
        skill_level = get_skill_level(talent_score)

    # Feature contributions (for chart)
    feature_contributions = {
        "commits": round(0.3 * min(commits / 500, 1) * 100, 1),
        "repos": round(0.2 * min(repos / 50, 1) * 100, 1),
        "stars": round(0.2 * min(stars / 100, 1) * 100, 1),
        "languages": round(0.3 * min(languages_count / 10, 1) * 100, 1),
    }

    # ✅ XAI EXPLANATION (YOUR PART)
    features_array = [commits, repos, stars, languages_count]
    explanations = explain_as_strings(features_array, model)

    strengths = get_strengths(commits, repos, stars, languages_count)

    return {
        "username": username,
        "name": github_data["name"],
        "avatar_url": github_data["avatar_url"],
        "bio": github_data["bio"],
        "location": github_data["location"],
        "talent_score": talent_score,
        "skill_level": skill_level,
        "top_languages": github_data["top_languages"],
        "strengths": strengths,
        "feature_contributions": feature_contributions,
        "explanation": explanations,  # ✅ replaced
        "raw_metrics": {
            "commits": commits,
            "repos": repos,
            "stars": stars,
            "languages_count": languages_count,
            "followers": github_data["followers"],
        }
    }