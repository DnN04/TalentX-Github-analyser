"""
test_api.py — API integration tests for the GitHub Talent Analyzer /analyze endpoint.

Uses FastAPI's TestClient (backed by httpx) so no running server is needed.
The GitHub API calls and ML model are mocked so tests are deterministic and
do not consume real GitHub API rate-limit quota.

Run with:
    pytest test_api.py -v

To run ONLY the live-network tests (uses real GitHub API — slow):
    pytest test_api.py -v -m live
"""

import json
import pickle
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ── Build a self-contained FastAPI app for testing ────────────────────────────
# In a real project this would simply be:
#   from main import app
# Here we define a minimal inline app so the test file is fully self-contained.

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

# ── Inline stubs (replace with real imports in production) ────────────────────

VALID_SKILL_LEVELS = {"Beginner", "Intermediate", "Advanced"}


def _fake_fetch_github(username: str) -> dict:
    """Stub GitHub fetcher used inside the test app."""
    MOCK_DB = {
        "torvalds": {
            "username": "torvalds",
            "commits": 4800,
            "repos": 7,
            "stars": 180000,
            "languages_count": 5,
            "raw_languages": ["C", "Makefile", "Shell", "Python", "Perl"],
        },
        "octocat": {
            "username": "octocat",
            "commits": 50,
            "repos": 9,
            "stars": 3000,
            "languages_count": 3,
            "raw_languages": ["Ruby", "HTML", "CSS"],
        },
        "test_beginner": {
            "username": "test_beginner",
            "commits": 5,
            "repos": 1,
            "stars": 0,
            "languages_count": 1,
            "raw_languages": ["Python"],
        },
    }
    if username not in MOCK_DB:
        raise ValueError(f"GitHub user '{username}' not found")
    return MOCK_DB[username]


def _fake_calculate_score(commits, repos, stars, languages_count):
    MAX = [5000, 200, 10000, 20]
    weights = [0.3, 0.2, 0.2, 0.3]
    vals = [commits, repos, stars, languages_count]
    score = sum(w * min(v / m, 1.0) for w, v, m in zip(weights, vals, MAX))
    return round(score * 100, 2)


def _fake_classify(score):
    if score >= 70:
        return "Advanced"
    elif score >= 40:
        return "Intermediate"
    return "Beginner"


def _fake_explain(commits, repos, stars, languages_count):
    return [
        "High commit activity strongly boosted your score.",
        "Moderate repository count had a neutral effect.",
        "High star count significantly boosted your score.",
        "Wide language diversity boosted your score.",
    ]


# ── Inline FastAPI app ────────────────────────────────────────────────────────

app = FastAPI(title="GitHub Talent Analyzer", version="1.0.0")


class AnalyzeRequest(BaseModel):
    username: str


class FeatureContribution(BaseModel):
    feature: str
    label: str
    raw_value: float
    contribution: float
    message: str


class AnalyzeResponse(BaseModel):
    username: str
    talent_score: float
    skill_level: str
    feature_contributions: list[FeatureContribution]
    explanations: list[str]


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    username = request.username.strip()
    if not username:
        raise HTTPException(status_code=422, detail="Username must not be empty.")

    try:
        data = _fake_fetch_github(username)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    c, r, s, l = data["commits"], data["repos"], data["stars"], data["languages_count"]
    talent_score = _fake_calculate_score(c, r, s, l)
    skill_level = _fake_classify(talent_score)
    explanations = _fake_explain(c, r, s, l)

    feature_contributions = [
        FeatureContribution(feature="commits",          label="commit count",       raw_value=c, contribution=0.30, message=explanations[0]),
        FeatureContribution(feature="repos",            label="repository count",   raw_value=r, contribution=0.20, message=explanations[1]),
        FeatureContribution(feature="stars",            label="star count",         raw_value=s, contribution=0.20, message=explanations[2]),
        FeatureContribution(feature="languages_count",  label="language diversity", raw_value=l, contribution=0.30, message=explanations[3]),
    ]

    return AnalyzeResponse(
        username=username,
        talent_score=talent_score,
        skill_level=skill_level,
        feature_contributions=feature_contributions,
        explanations=explanations,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# ── TestClient fixture ────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ══════════════════════════════════════════════════════════════════════════════
# 1. /health endpoint
# ══════════════════════════════════════════════════════════════════════════════

class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_body(self, client):
        resp = client.get("/health")
        assert resp.json() == {"status": "ok"}


# ══════════════════════════════════════════════════════════════════════════════
# 2. /analyze with valid usernames
# ══════════════════════════════════════════════════════════════════════════════

class TestAnalyzeValidUsers:

    def test_torvalds_returns_200(self, client):
        resp = client.post("/analyze", json={"username": "torvalds"})
        assert resp.status_code == 200

    def test_torvalds_is_advanced(self, client):
        resp = client.post("/analyze", json={"username": "torvalds"})
        body = resp.json()
        assert body["skill_level"] == "Advanced"

    def test_torvalds_talent_score_in_range(self, client):
        resp = client.post("/analyze", json={"username": "torvalds"})
        score = resp.json()["talent_score"]
        assert 0 <= score <= 100, f"Score {score} out of [0,100]"

    def test_torvalds_username_echoed(self, client):
        resp = client.post("/analyze", json={"username": "torvalds"})
        assert resp.json()["username"] == "torvalds"

    def test_beginner_profile_labelled_correctly(self, client):
        resp = client.post("/analyze", json={"username": "test_beginner"})
        assert resp.status_code == 200
        assert resp.json()["skill_level"] == "Beginner"

    def test_octocat_profile(self, client):
        resp = client.post("/analyze", json={"username": "octocat"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["skill_level"] in VALID_SKILL_LEVELS


# ══════════════════════════════════════════════════════════════════════════════
# 3. /analyze response schema validation
# ══════════════════════════════════════════════════════════════════════════════

class TestAnalyzeSchema:

    @pytest.fixture(autouse=True)
    def _response(self, client):
        self.resp = client.post("/analyze", json={"username": "torvalds"})
        self.body = self.resp.json()

    def test_has_username_field(self):
        assert "username" in self.body

    def test_has_talent_score_field(self):
        assert "talent_score" in self.body

    def test_has_skill_level_field(self):
        assert "skill_level" in self.body

    def test_has_explanations_field(self):
        assert "explanations" in self.body

    def test_has_feature_contributions_field(self):
        assert "feature_contributions" in self.body

    def test_talent_score_is_float(self):
        assert isinstance(self.body["talent_score"], (int, float))

    def test_skill_level_is_valid_string(self):
        assert self.body["skill_level"] in VALID_SKILL_LEVELS

    def test_explanations_is_list_of_strings(self):
        exps = self.body["explanations"]
        assert isinstance(exps, list)
        assert all(isinstance(e, str) for e in exps)

    def test_explanations_not_empty(self):
        assert len(self.body["explanations"]) > 0

    def test_feature_contributions_has_four_items(self):
        assert len(self.body["feature_contributions"]) == 4

    def test_feature_contribution_keys(self):
        required = {"feature", "label", "raw_value", "contribution", "message"}
        for fc in self.body["feature_contributions"]:
            assert required.issubset(fc.keys()), f"Missing keys in {fc}"

    def test_feature_contribution_raw_value_non_negative(self):
        for fc in self.body["feature_contributions"]:
            assert fc["raw_value"] >= 0

    def test_feature_names_present(self):
        feature_names = {fc["feature"] for fc in self.body["feature_contributions"]}
        expected = {"commits", "repos", "stars", "languages_count"}
        assert expected == feature_names

    def test_response_is_valid_json(self, client):
        resp = client.post("/analyze", json={"username": "octocat"})
        # If this doesn't throw, the response is valid JSON
        _ = resp.json()

    def test_content_type_is_json(self, client):
        resp = client.post("/analyze", json={"username": "octocat"})
        assert "application/json" in resp.headers["content-type"]


# ══════════════════════════════════════════════════════════════════════════════
# 4. /analyze with invalid / edge-case inputs
# ══════════════════════════════════════════════════════════════════════════════

class TestAnalyzeInvalidInputs:

    def test_nonexistent_username_returns_404(self, client):
        resp = client.post("/analyze", json={"username": "this_user_does_not_exist_xyz"})
        assert resp.status_code == 404

    def test_nonexistent_username_has_detail_field(self, client):
        resp = client.post("/analyze", json={"username": "ghost_user_99999"})
        assert "detail" in resp.json()

    def test_empty_username_returns_error(self, client):
        resp = client.post("/analyze", json={"username": ""})
        # Either 422 (validation) or 404/400 depending on handler
        assert resp.status_code in {400, 404, 422}

    def test_missing_username_field_returns_422(self, client):
        resp = client.post("/analyze", json={})
        assert resp.status_code == 422

    def test_wrong_content_type_returns_error(self, client):
        resp = client.post("/analyze", content="torvalds",
                           headers={"Content-Type": "text/plain"})
        assert resp.status_code in {400, 415, 422}

    def test_numeric_username_not_in_db_returns_404(self, client):
        resp = client.post("/analyze", json={"username": "12345"})
        assert resp.status_code == 404

    def test_whitespace_only_username_returns_error(self, client):
        resp = client.post("/analyze", json={"username": "   "})
        assert resp.status_code in {400, 404, 422}


# ══════════════════════════════════════════════════════════════════════════════
# 5. Idempotency & consistency
# ══════════════════════════════════════════════════════════════════════════════

class TestAnalyzeConsistency:

    def test_same_username_same_score(self, client):
        """Calling /analyze twice for the same user must return the same score."""
        resp1 = client.post("/analyze", json={"username": "octocat"})
        resp2 = client.post("/analyze", json={"username": "octocat"})
        assert resp1.json()["talent_score"] == resp2.json()["talent_score"]

    def test_same_username_same_skill_level(self, client):
        resp1 = client.post("/analyze", json={"username": "octocat"})
        resp2 = client.post("/analyze", json={"username": "octocat"})
        assert resp1.json()["skill_level"] == resp2.json()["skill_level"]

    def test_advanced_score_higher_than_beginner(self, client):
        adv = client.post("/analyze", json={"username": "torvalds"}).json()["talent_score"]
        beg = client.post("/analyze", json={"username": "test_beginner"}).json()["talent_score"]
        assert adv > beg


# ══════════════════════════════════════════════════════════════════════════════
# 6. Live network tests (skipped by default)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.live
class TestLiveGitHubAPI:
    """
    These tests hit the real GitHub API.
    Run with: pytest test_api.py -v -m live
    Requires GITHUB_TOKEN env var for higher rate limits (optional).
    """

    def test_real_torvalds_profile(self):
        """Placeholder — implement with your real GitHub fetcher."""
        pytest.skip("Live test: plug in the real GitHub fetcher to enable.")
