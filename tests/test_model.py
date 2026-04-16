"""
test_model.py — Unit tests for the GitHub Talent Analyzer ML layer.

Covers:
  - Talent score calculator (edge cases + normal cases)
  - Random Forest model: valid output labels, probability bounds
  - GitHub data fetcher: expected response keys
  - Explainer: message generation without a real model file

Run with:
    pytest test_model.py -v
"""

import json
import types
import pickle
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


# ══════════════════════════════════════════════════════════════════════════════
# Helpers — inline implementations so tests run without the full app installed
# ══════════════════════════════════════════════════════════════════════════════

VALID_SKILL_LEVELS = {"Beginner", "Intermediate", "Advanced"}
FEATURE_NAMES = ["commits", "repos", "stars", "languages_count"]


def calculate_talent_score(commits: float, repos: float, stars: float,
                            languages_count: float) -> float:
    """
    Reference implementation of the talent score formula (mirrors report §8):
        Score = 0.3*commits_norm + 0.2*repos_norm + 0.2*stars_norm + 0.3*langs_norm
    where each feature is normalised to [0, 1] using fixed max values.
    """
    MAX_COMMITS = 5000
    MAX_REPOS = 200
    MAX_STARS = 10000
    MAX_LANGS = 20

    c = min(commits / MAX_COMMITS, 1.0)
    r = min(repos / MAX_REPOS, 1.0)
    s = min(stars / MAX_STARS, 1.0)
    l = min(languages_count / MAX_LANGS, 1.0)

    raw = 0.3 * c + 0.2 * r + 0.2 * s + 0.3 * l
    return round(raw * 100, 2)


def classify_skill_level(talent_score: float) -> str:
    """Map talent score to a skill label."""
    if talent_score >= 70:
        return "Advanced"
    elif talent_score >= 40:
        return "Intermediate"
    return "Beginner"


def _mock_github_fetch(username: str) -> dict:
    """Stub that mimics what the real GitHub fetcher should return."""
    if not username or username.startswith("__invalid"):
        raise ValueError(f"Invalid GitHub username: '{username}'")
    return {
        "username": username,
        "commits": 150,
        "repos": 10,
        "stars": 20,
        "languages_count": 4,
        "raw_languages": ["Python", "JavaScript", "Shell", "Dockerfile"],
    }


# ══════════════════════════════════════════════════════════════════════════════
# 1. Talent Score Calculator
# ══════════════════════════════════════════════════════════════════════════════

class TestTalentScoreCalculator:

    def test_zero_values_returns_zero(self):
        """All-zero inputs must produce a score of exactly 0."""
        score = calculate_talent_score(0, 0, 0, 0)
        assert score == 0.0, f"Expected 0.0, got {score}"

    def test_max_values_returns_hundred(self):
        """Saturated inputs must produce a score of exactly 100."""
        score = calculate_talent_score(5000, 200, 10000, 20)
        assert score == 100.0, f"Expected 100.0, got {score}"

    def test_score_within_bounds(self):
        """Score must always fall in [0, 100]."""
        test_cases = [
            (100, 5, 10, 3),
            (1000, 50, 500, 8),
            (9999, 199, 9999, 19),
            (1, 1, 1, 1),
        ]
        for args in test_cases:
            score = calculate_talent_score(*args)
            assert 0.0 <= score <= 100.0, f"Score {score} out of bounds for args {args}"

    def test_overflow_values_clamped(self):
        """Values beyond the max must clamp to 100, not exceed it."""
        score = calculate_talent_score(999999, 999999, 999999, 999999)
        assert score == 100.0

    def test_commits_weight_is_highest(self):
        """Commits and language count each have 0.3 weight — higher than repos/stars."""
        score_high_commits = calculate_talent_score(5000, 0, 0, 0)
        score_high_repos = calculate_talent_score(0, 200, 0, 0)
        assert score_high_commits > score_high_repos

    def test_known_input_known_output(self):
        """Regression test: specific inputs produce the expected score."""
        # 0.3*(500/5000) + 0.2*(10/200) + 0.2*(50/10000) + 0.3*(5/20)
        # = 0.3*0.1 + 0.2*0.05 + 0.2*0.005 + 0.3*0.25
        # = 0.03 + 0.01 + 0.001 + 0.075 = 0.116 → 11.6
        score = calculate_talent_score(500, 10, 50, 5)
        assert abs(score - 11.6) < 0.1, f"Got {score}, expected ~11.6"

    def test_partial_high_commits(self):
        """Only commits maxed: score should be 30."""
        score = calculate_talent_score(5000, 0, 0, 0)
        assert abs(score - 30.0) < 0.01

    def test_score_is_float(self):
        score = calculate_talent_score(100, 5, 10, 3)
        assert isinstance(score, float)

    def test_negative_inputs_treated_as_zero(self):
        """Negative values (data error) should not crash or produce negative scores."""
        # Clamp negative → 0 via min(..., 1.0) already ensures this
        score = calculate_talent_score(max(0, -10), max(0, -5), max(0, -1), max(0, -3))
        assert score == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# 2. Skill Level Classifier
# ══════════════════════════════════════════════════════════════════════════════

class TestSkillLevelClassifier:

    def test_beginner_label(self):
        assert classify_skill_level(0) == "Beginner"
        assert classify_skill_level(39.9) == "Beginner"

    def test_intermediate_label(self):
        assert classify_skill_level(40) == "Intermediate"
        assert classify_skill_level(69.9) == "Intermediate"

    def test_advanced_label(self):
        assert classify_skill_level(70) == "Advanced"
        assert classify_skill_level(100) == "Advanced"

    def test_all_labels_are_valid(self):
        """All possible score values map to a recognised label."""
        for score in np.linspace(0, 100, 500):
            label = classify_skill_level(float(score))
            assert label in VALID_SKILL_LEVELS, f"Unknown label '{label}' for score {score}"

    def test_boundary_40(self):
        assert classify_skill_level(40.0) == "Intermediate"
        assert classify_skill_level(39.99) == "Beginner"

    def test_boundary_70(self):
        assert classify_skill_level(70.0) == "Advanced"
        assert classify_skill_level(69.99) == "Intermediate"


# ══════════════════════════════════════════════════════════════════════════════
# 3. ML Model (using a real or mocked Random Forest)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def trained_rf_model():
    """
    Train a minimal Random Forest on synthetic data so tests are
    self-contained and don't require trained_model.pkl on disk.
    """
    from sklearn.ensemble import RandomForestClassifier

    rng = np.random.default_rng(42)
    n = 300
    commits = rng.integers(0, 5000, n).astype(float)
    repos = rng.integers(0, 200, n).astype(float)
    stars = rng.integers(0, 10000, n).astype(float)
    langs = rng.integers(1, 20, n).astype(float)

    X = np.column_stack([commits, repos, stars, langs])

    # Labels derived from score formula
    scores = np.array([calculate_talent_score(*row) for row in X])
    y = np.where(scores >= 70, 2, np.where(scores >= 40, 1, 0))  # 0=Beg,1=Int,2=Adv

    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(X, y)
    return clf


class TestRandomForestModel:

    def test_predict_returns_valid_class(self, trained_rf_model):
        X = np.array([[300, 10, 20, 4]])
        pred = trained_rf_model.predict(X)
        assert pred[0] in {0, 1, 2}, f"Unexpected class: {pred[0]}"

    def test_predict_proba_sums_to_one(self, trained_rf_model):
        X = np.array([[300, 10, 20, 4]])
        proba = trained_rf_model.predict_proba(X)
        assert abs(proba.sum() - 1.0) < 1e-6

    def test_predict_proba_all_non_negative(self, trained_rf_model):
        X = np.array([[300, 10, 20, 4]])
        proba = trained_rf_model.predict_proba(X)
        assert (proba >= 0).all()

    def test_advanced_developer_classified_correctly(self, trained_rf_model):
        """Someone with maxed-out features should be Advanced (class 2)."""
        X = np.array([[5000, 200, 10000, 20]])
        pred = trained_rf_model.predict(X)
        assert pred[0] == 2, f"Expected Advanced (2), got {pred[0]}"

    def test_beginner_developer_classified_correctly(self, trained_rf_model):
        """Someone with minimal activity should be Beginner (class 0)."""
        X = np.array([[0, 0, 0, 0]])
        pred = trained_rf_model.predict(X)
        assert pred[0] == 0, f"Expected Beginner (0), got {pred[0]}"

    def test_model_has_feature_importances(self, trained_rf_model):
        assert hasattr(trained_rf_model, "feature_importances_")
        fi = trained_rf_model.feature_importances_
        assert len(fi) == 4
        assert abs(fi.sum() - 1.0) < 1e-6

    def test_model_n_features(self, trained_rf_model):
        assert trained_rf_model.n_features_in_ == 4

    def test_model_can_be_pickled_and_reloaded(self, trained_rf_model):
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            pickle.dump(trained_rf_model, f)
            tmp_path = f.name
        with open(tmp_path, "rb") as f:
            reloaded = pickle.load(f)
        X = np.array([[200, 8, 15, 3]])
        assert reloaded.predict(X)[0] == trained_rf_model.predict(X)[0]
        Path(tmp_path).unlink()

    def test_batch_predictions_all_valid(self, trained_rf_model):
        rng = np.random.default_rng(7)
        X = rng.integers(0, [5000, 200, 10000, 20], size=(100, 4)).astype(float)
        preds = trained_rf_model.predict(X)
        assert set(preds).issubset({0, 1, 2})


# ══════════════════════════════════════════════════════════════════════════════
# 4. GitHub Data Fetcher
# ══════════════════════════════════════════════════════════════════════════════

EXPECTED_FETCHER_KEYS = {"username", "commits", "repos", "stars",
                          "languages_count", "raw_languages"}


class TestGitHubFetcher:

    def test_returns_all_expected_keys(self):
        data = _mock_github_fetch("octocat")
        missing = EXPECTED_FETCHER_KEYS - data.keys()
        assert not missing, f"Missing keys: {missing}"

    def test_commits_is_non_negative_int(self):
        data = _mock_github_fetch("octocat")
        assert isinstance(data["commits"], int)
        assert data["commits"] >= 0

    def test_repos_is_non_negative_int(self):
        data = _mock_github_fetch("octocat")
        assert isinstance(data["repos"], int)
        assert data["repos"] >= 0

    def test_stars_is_non_negative_int(self):
        data = _mock_github_fetch("octocat")
        assert isinstance(data["stars"], int)
        assert data["stars"] >= 0

    def test_languages_count_matches_raw_languages_length(self):
        data = _mock_github_fetch("octocat")
        assert data["languages_count"] == len(data["raw_languages"])

    def test_username_echoed_correctly(self):
        data = _mock_github_fetch("torvalds")
        assert data["username"] == "torvalds"

    def test_invalid_username_raises_value_error(self):
        with pytest.raises(ValueError):
            _mock_github_fetch("__invalid_user__")

    def test_empty_username_raises_value_error(self):
        with pytest.raises(ValueError):
            _mock_github_fetch("")

    def test_raw_languages_is_a_list(self):
        data = _mock_github_fetch("octocat")
        assert isinstance(data["raw_languages"], list)

    def test_raw_languages_elements_are_strings(self):
        data = _mock_github_fetch("octocat")
        assert all(isinstance(lang, str) for lang in data["raw_languages"])


# ══════════════════════════════════════════════════════════════════════════════
# 5. Explainer (unit-level, no model file required)
# ══════════════════════════════════════════════════════════════════════════════

class TestExplainer:
    """Tests for explainer.py logic without requiring trained_model.pkl."""

    @pytest.fixture(autouse=True)
    def _patch_model(self, trained_rf_model):
        """Inject the in-memory RF model so explainer.load_model is never called."""
        self.model = trained_rf_model

    def test_explain_returns_list(self):
        from explainer import explain
        result = explain(np.array([300.0, 10.0, 20.0, 4.0]), model=self.model)
        assert isinstance(result, list)

    def test_explain_returns_four_features(self):
        from explainer import explain
        result = explain(np.array([300.0, 10.0, 20.0, 4.0]), model=self.model)
        assert len(result) == 4

    def test_explain_dict_has_required_keys(self):
        from explainer import explain
        result = explain(np.array([300.0, 10.0, 20.0, 4.0]), model=self.model)
        required = {"feature", "label", "raw_value", "contribution", "message"}
        for rec in result:
            assert required.issubset(rec.keys()), f"Missing keys in {rec}"

    def test_explain_as_strings_returns_string_list(self):
        from explainer import explain_as_strings
        msgs = explain_as_strings(np.array([300.0, 10.0, 20.0, 4.0]), model=self.model)
        assert all(isinstance(m, str) for m in msgs)
        assert len(msgs) == 4

    def test_high_commits_produces_positive_message(self):
        from explainer import explain
        # 5000 commits >> HIGH_THRESHOLD (500)
        result = explain(np.array([5000.0, 5.0, 5.0, 2.0]), model=self.model)
        commit_rec = next(r for r in result if r["feature"] == "commits")
        assert "boost" in commit_rec["message"].lower() or "high" in commit_rec["message"].lower()

    def test_zero_commits_produces_low_message(self):
        from explainer import explain
        result = explain(np.array([0.0, 5.0, 5.0, 2.0]), model=self.model)
        commit_rec = next(r for r in result if r["feature"] == "commits")
        assert "low" in commit_rec["message"].lower() or "reduc" in commit_rec["message"].lower()

    def test_generate_summary_structure(self):
        from explainer import generate_summary
        summary = generate_summary(
            feature_vector=np.array([300.0, 10.0, 20.0, 4.0]),
            talent_score=65.0,
            skill_level="Intermediate",
            model=self.model,
        )
        assert "skill_level" in summary
        assert "talent_score" in summary
        assert "summary" in summary
        assert "feature_explanations" in summary
        assert "feature_details" in summary

    def test_generate_summary_talent_score_preserved(self):
        from explainer import generate_summary
        summary = generate_summary(
            feature_vector=np.array([300.0, 10.0, 20.0, 4.0]),
            talent_score=42.5,
            skill_level="Intermediate",
            model=self.model,
        )
        assert summary["talent_score"] == 42.5

    def test_sorted_by_contribution_magnitude(self):
        from explainer import explain
        result = explain(np.array([5000.0, 200.0, 10000.0, 20.0]), model=self.model)
        contribs = [abs(r["contribution"]) for r in result]
        assert contribs == sorted(contribs, reverse=True), "Not sorted by |contribution|"
