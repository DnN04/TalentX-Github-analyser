"""
explainer.py — Explainable AI layer for GitHub Talent Analyzer
Uses SHAP (with Random Forest feature_importances_ fallback) to generate
human-readable explanations for a developer's talent score.
"""

import os
import pickle
import logging
import numpy as np
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Feature metadata ──────────────────────────────────────────────────────────
# Order must match the feature vector used during training:
# [commits, repos, stars, languages_count]

FEATURE_META = {
    "commits": {
        "label": "commit count",
        "high_msg": "High commit activity strongly boosted your score — consistent contributions signal an active developer.",
        "low_msg": "Low commit count reduced your score — try committing more regularly to show ongoing activity.",
        "neutral_msg": "Moderate commit activity had a neutral effect on your score.",
    },
    "repos": {
        "label": "repository count",
        "high_msg": "A healthy number of repositories boosted your score — breadth of projects demonstrates initiative.",
        "low_msg": "Few public repositories slightly lowered your score — consider open-sourcing more of your work.",
        "neutral_msg": "Your repository count had a moderate positive effect on your score.",
    },
    "stars": {
        "label": "star count",
        "high_msg": "High star count significantly boosted your score — community recognition is a strong signal of quality work.",
        "low_msg": "Low stars on your repositories reduced your score — promoting your projects can help grow visibility.",
        "neutral_msg": "Your projects' star count had a small effect on your score.",
    },
    "languages_count": {
        "label": "language diversity",
        "high_msg": "Wide language diversity boosted your score — proficiency across multiple languages shows versatility.",
        "low_msg": "Limited language diversity slightly reduced your score — exploring new languages can broaden your profile.",
        "neutral_msg": "Your language diversity had a moderate effect on your score.",
    },
}

FEATURE_NAMES = list(FEATURE_META.keys())  # ['commits', 'repos', 'stars', 'languages_count']

# Thresholds that define "high" / "low" for human-readable messaging.
# Adjust these based on your training data distribution.
HIGH_THRESHOLDS = {
    "commits": 500,
    "repos": 20,
    "stars": 50,
    "languages_count": 5,
}

LOW_THRESHOLDS = {
    "commits": 50,
    "repos": 3,
    "stars": 5,
    "languages_count": 2,
}


# ── Model loader ──────────────────────────────────────────────────────────────

def load_model(model_path: str = "trained_model.pkl"):
    """Load the pickled Random Forest model from disk."""
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Model file not found at '{model_path}'. "
            "Train the model first and save it with pickle."
        )
    with open(path, "rb") as f:
        model = pickle.load(f)
    logger.info("Model loaded from %s", model_path)
    return model


# ── SHAP-based explainer ──────────────────────────────────────────────────────

def _get_shap_values(model, feature_vector: np.ndarray) -> Optional[np.ndarray]:
    """
    Attempt to compute SHAP values for the given feature vector.
    Returns a 1-D array of per-feature SHAP values (for the predicted class),
    or None if SHAP is unavailable.
    """
    try:
        import shap  # optional dependency

        explainer = shap.TreeExplainer(model)
        # shap_values shape: (n_classes, n_samples, n_features) for multi-class RF
        shap_values = explainer.shap_values(feature_vector.reshape(1, -1))

        # For a multi-class model shap_values is a list; pick the predicted class.
        if isinstance(shap_values, list):
            predicted_class = int(model.predict(feature_vector.reshape(1, -1))[0])
            return shap_values[predicted_class][0]

        # Binary classifier — shap_values is a 2-D array
        return shap_values[0]

    except ImportError:
        logger.warning("SHAP not installed — falling back to feature_importances_.")
        return None
    except Exception as exc:
        logger.warning("SHAP computation failed (%s) — falling back.", exc)
        return None


def _get_importance_based_values(model, feature_vector: np.ndarray) -> np.ndarray:
    """
    Fallback: use the RF's global feature_importances_ weighted by the
    normalised feature values to approximate per-instance contributions.
    """
    importances = model.feature_importances_          # shape: (n_features,)
    normed = feature_vector / (feature_vector.sum() + 1e-9)
    return importances * normed


# ── Human-readable message builder ───────────────────────────────────────────

def _build_message(feature_name: str, raw_value: float, shap_value: float) -> str:
    """
    Combine the raw feature value and its SHAP contribution into a single
    human-readable sentence.
    """
    meta = FEATURE_META[feature_name]
    high_thresh = HIGH_THRESHOLDS[feature_name]
    low_thresh = LOW_THRESHOLDS[feature_name]

    if raw_value >= high_thresh:
        base = meta["high_msg"]
    elif raw_value <= low_thresh:
        base = meta["low_msg"]
    else:
        base = meta["neutral_msg"]

    # Append a SHAP-magnitude qualifier so the recruiter/developer can see
    # how much each feature actually moved the needle.
    abs_shap = abs(shap_value)
    if abs_shap > 0.15:
        qualifier = " (very high impact)"
    elif abs_shap > 0.07:
        qualifier = " (moderate impact)"
    else:
        qualifier = " (low impact)"

    return base + qualifier


# ── Public API ────────────────────────────────────────────────────────────────

def explain(
    feature_vector: np.ndarray,
    model=None,
    model_path: str = "trained_model.pkl",
) -> list[dict]:
    """
    Generate a list of explanation dicts for one developer profile.

    Parameters
    ----------
    feature_vector : np.ndarray
        1-D array in order [commits, repos, stars, languages_count].
    model : sklearn estimator, optional
        Pre-loaded model object. If None, the model is loaded from *model_path*.
    model_path : str
        Path to the pickled model file (used only when *model* is None).

    Returns
    -------
    list of dict, each with keys:
        feature      – internal feature name
        label        – human-friendly label
        raw_value    – the developer's actual value
        contribution – SHAP / importance-based contribution score
        message      – human-readable explanation string
    """
    if model is None:
        model = load_model(model_path)

    feature_vector = np.asarray(feature_vector, dtype=float)

    # 1. Try SHAP, fall back to importance-weighted approach.
    contributions = _get_shap_values(model, feature_vector)
    if contributions is None:
        contributions = _get_importance_based_values(model, feature_vector)

    # 2. Build explanation records, sorted by absolute contribution (desc).
    explanations = []
    # for i, fname in enumerate(FEATURE_NAMES):
    #     explanations.append(
    #         {
    #             "feature": fname,
    #             "label": FEATURE_META[fname]["label"],
    #             "raw_value": float(feature_vector[i]),
    #             "contribution": round(float(contributions[i][0]), 4),
    #             "message": _build_message(fname, feature_vector[i], contributions[i]),
    #         }
    #     )
    for i, fname in enumerate(FEATURE_NAMES):
        value = float(feature_vector[i])

        # ✅ FIX: ensure scalar
        contrib = float(np.array(contributions[i]).flatten()[0])

        explanations.append(
            {
                "feature": fname,
                "label": FEATURE_META[fname]["label"],
                "raw_value": value,
                "contribution": round(contrib, 4),
                "message": _build_message(fname, value, contrib),  # ✅ pass scalar
            }
    )
    explanations.sort(key=lambda x: abs(x["contribution"]), reverse=True)
    return explanations


def explain_as_strings(
    feature_vector: np.ndarray,
    model=None,
    model_path: str = "trained_model.pkl",
) -> list[str]:
    """
    Convenience wrapper — returns only the human-readable message strings,
    which is what the FastAPI /analyze endpoint embeds directly in the response.

    Example output:
      [
        "High commit activity strongly boosted your score — consistent … (very high impact)",
        "Wide language diversity boosted your score — … (moderate impact)",
        ...
      ]
    """
    records = explain(feature_vector, model=model, model_path=model_path)
    return [r["message"] for r in records]


def generate_summary(
    feature_vector: np.ndarray,
    talent_score: float,
    skill_level: str,
    model=None,
    model_path: str = "trained_model.pkl",
) -> dict:
    """
    High-level summary dict intended to be returned by the FastAPI /analyze
    endpoint's 'explanation' key.

    Returns
    -------
    dict with keys:
        skill_level          – "Beginner" | "Intermediate" | "Advanced"
        talent_score         – float 0–100
        summary              – one-liner verdict string
        feature_explanations – list of human-readable strings (sorted by impact)
        feature_details      – full list of explanation dicts (for frontend charts)
    """
    records = explain(feature_vector, model=model, model_path=model_path)
    messages = [r["message"] for r in records]

    # Build a one-liner verdict.
    if talent_score >= 75:
        verdict = (
            f"Impressive profile! Your GitHub activity places you firmly in the "
            f"{skill_level} tier with a talent score of {talent_score:.1f}/100."
        )
    elif talent_score >= 45:
        verdict = (
            f"Solid profile. You are ranked {skill_level} with a talent score of "
            f"{talent_score:.1f}/100 — there is room to grow."
        )
    else:
        verdict = (
            f"Early-stage profile. Your current talent score is {talent_score:.1f}/100 "
            f"({skill_level}). Regular contributions will improve your ranking quickly."
        )

    return {
        "skill_level": skill_level,
        "talent_score": round(talent_score, 2),
        "summary": verdict,
        "feature_explanations": messages,
        "feature_details": records,
    }


# ── CLI helper (for quick manual checks) ─────────────────────────────────────

if __name__ == "__main__":
    import json

    # Example: a mid-level developer
    sample = np.array([320, 18, 42, 6], dtype=float)  # commits, repos, stars, languages

    print("Running explainer on sample feature vector:", sample)
    print("(Model file 'trained_model.pkl' must exist in the working directory)\n")

    try:
        result = generate_summary(
            feature_vector=sample,
            talent_score=68.5,
            skill_level="Intermediate",
        )
        print(json.dumps(result, indent=2))
    except FileNotFoundError as e:
        print(f"[DEMO MODE — no model file] {e}")
        print("\nRunning without a real model (importance fallback disabled).")
        print("Feature messages based on raw thresholds only:\n")
        for fname, val in zip(FEATURE_NAMES, sample):
            meta = FEATURE_META[fname]
            if val >= HIGH_THRESHOLDS[fname]:
                print(f"  ✓ {meta['high_msg']}")
            elif val <= LOW_THRESHOLDS[fname]:
                print(f"  ✗ {meta['low_msg']}")
            else:
                print(f"  ~ {meta['neutral_msg']}")
