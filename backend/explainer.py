"""
Explainer Module — GitHub Talent Analyzer
Generates human-readable explanations for the talent score.
Works standalone (no SHAP needed) — uses rule-based feature contributions.
When Member 1 delivers trained_model.pkl, this can be upgraded to SHAP.
"""

def generate_explanation(
    commits: int,
    repos: int,
    stars: int,
    languages_count: int,
    talent_score: float
) -> list[str]:
    """
    Returns a list of explanation strings describing what drove the score.
    Each string is a plain-English insight for the dashboard.
    """
    explanations = []

    # Commits analysis (weight: 30%)
    if commits >= 300:
        explanations.append(f"✅ Strong commit history ({commits} commits) — biggest positive driver of your score.")
    elif commits >= 100:
        explanations.append(f"🟡 Moderate commit activity ({commits} commits) — increasing this will boost your score most.")
    else:
        explanations.append(f"🔴 Low commit count ({commits}) — this is holding your score back the most (30% weight).")

    # Languages analysis (weight: 30%)
    if languages_count >= 7:
        explanations.append(f"✅ You work in {languages_count} languages — strong technology diversity boosts your score.")
    elif languages_count >= 4:
        explanations.append(f"🟡 You know {languages_count} languages — adding more technologies will help.")
    else:
        explanations.append(f"🔴 Only {languages_count} language(s) detected — expanding tech stack will significantly improve score.")

    # Repos analysis (weight: 20%)
    if repos >= 30:
        explanations.append(f"✅ {repos} public repositories show an active builder mindset.")
    elif repos >= 10:
        explanations.append(f"🟡 {repos} repos is decent — aim for 30+ to maximize this factor.")
    else:
        explanations.append(f"🔴 Only {repos} public repos — create more projects to improve this component.")

    # Stars analysis (weight: 20%)
    if stars >= 100:
        explanations.append(f"✅ {stars} stars show your work is recognized by the community.")
    elif stars >= 20:
        explanations.append(f"🟡 {stars} stars — solid but building more impactful projects will help.")
    else:
        explanations.append(f"🔴 {stars} stars — focus on projects that solve real problems to gain community recognition.")

    # Overall summary
    if talent_score >= 75:
        explanations.append("🏆 Overall: Expert-level profile — top percentile of developers on GitHub.")
    elif talent_score >= 50:
        explanations.append("🚀 Overall: Advanced developer profile — consistently active and skilled.")
    elif talent_score >= 25:
        explanations.append("📈 Overall: Intermediate level — good foundation, keep building projects.")
    else:
        explanations.append("🌱 Overall: Early stage — great time to start contributing more regularly.")

    return explanations
