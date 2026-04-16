"""
Score Calculator — GitHub Talent Analyzer
Formula: 0.3*commits + 0.2*repos + 0.2*stars + 0.3*languages
All values normalized to 0-100 scale before applying weights.
"""

def calculate_score(commits: int, repos: int, stars: int, languages_count: int) -> float:
    """Calculate talent score (0-100) using weighted normalized formula."""
    # Normalization caps (based on realistic developer ranges)
    norm_commits   = min(commits / 500, 1.0)       # 500 commits = max
    norm_repos     = min(repos / 50, 1.0)           # 50 repos = max
    norm_stars     = min(stars / 200, 1.0)          # 200 stars = max
    norm_languages = min(languages_count / 10, 1.0) # 10 languages = max

    score = (
        0.3 * norm_commits +
        0.2 * norm_repos +
        0.2 * norm_stars +
        0.3 * norm_languages
    ) * 100

    return round(score, 2)


def get_skill_level(talent_score: float) -> str:
    """Rule-based skill classification from talent score."""
    if talent_score >= 75:
        return "Expert"
    elif talent_score >= 50:
        return "Advanced"
    elif talent_score >= 25:
        return "Intermediate"
    else:
        return "Beginner"


def get_strengths(commits: int, repos: int, stars: int, languages_count: int) -> list:
    """Return a list of top strength strings based on metrics."""
    strengths = []

    if commits >= 200:
        strengths.append("High commit activity — actively contributes code")
    if repos >= 20:
        strengths.append("Diverse project portfolio")
    if stars >= 50:
        strengths.append("Community recognition — projects attract stars")
    if languages_count >= 5:
        strengths.append("Polyglot developer — works across multiple languages")
    if commits >= 100 and repos >= 10:
        strengths.append("Consistent and productive developer")

    if not strengths:
        strengths.append("Early-stage developer — growing their GitHub presence")

    return strengths[:4]  # Return top 4 max
