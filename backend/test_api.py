"""
API Tests — run with: pytest test_api.py -v
Tests the /analyze endpoint with real and mock data.
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "running" in resp.json()["message"]


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_analyze_valid_user():
    """Test with a real, well-known GitHub user."""
    resp = client.post("/analyze", json={"username": "torvalds"})
    assert resp.status_code == 200
    data = resp.json()
    assert "talent_score" in data
    assert "skill_level" in data
    assert data["skill_level"] in ["Beginner", "Intermediate", "Advanced", "Expert"]
    assert 0 <= data["talent_score"] <= 100
    assert "feature_contributions" in data
    assert "explanation" in data


def test_analyze_invalid_user():
    """Test with a username that does not exist."""
    resp = client.post("/analyze", json={"username": "thisuserdoesnotexist12345xyz"})
    assert resp.status_code == 404


def test_analyze_empty_username():
    """Test empty username returns 400."""
    resp = client.post("/analyze", json={"username": ""})
    assert resp.status_code == 400


def test_response_schema():
    """Verify all expected fields exist in response."""
    resp = client.post("/analyze", json={"username": "torvalds"})
    if resp.status_code == 200:
        data = resp.json()
        required_fields = [
            "username", "name", "talent_score", "skill_level",
            "top_languages", "strengths", "feature_contributions",
            "explanation", "raw_metrics"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
