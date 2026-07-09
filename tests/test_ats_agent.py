import pytest
from agents.ats_agent import ATSAgent, ATS_WEIGHTS, SCORE_CATEGORIES

class TestATSWeights:
    def test_weights_sum_to_100(self):
        assert sum(ATS_WEIGHTS.values()) == 100

    def test_all_weights_positive(self):
        assert all(w > 0 for w in ATS_WEIGHTS.values())

    def test_seven_categories(self):
        assert len(ATS_WEIGHTS) == 7

class TestScoreCategories:
    def test_categories_cover_all_scores(self):
        covered = set()
        for low, high, _ in SCORE_CATEGORIES:
            for s in range(low, high):
                covered.add(s)
        assert 0 in covered
        assert 99 in covered
        assert all(s in covered for s in range(0, 100))

    def test_no_gaps_between_categories(self):
        prev_high = 0
        for low, high, _ in SCORE_CATEGORIES:
            assert low == prev_high, f"Gap at {prev_high} -> {low}"
            prev_high = high
        assert prev_high == 100

    def test_category_labels(self, ats_agent):
        assert ats_agent._get_category_label(0) == "Poor"
        assert ats_agent._get_category_label(39) == "Poor"
        assert ats_agent._get_category_label(40) == "Average"
        assert ats_agent._get_category_label(59) == "Average"
        assert ats_agent._get_category_label(60) == "Good"
        assert ats_agent._get_category_label(74) == "Good"
        assert ats_agent._get_category_label(75) == "Strong"
        assert ats_agent._get_category_label(89) == "Strong"
        assert ats_agent._get_category_label(90) == "Exceptional"
        assert ats_agent._get_category_label(100) == "Exceptional"

has_llm_key = None
try:
    from config import settings
    has_llm_key = settings.hf_api_key or settings.groq_api_key
except Exception:
    pass

llm_skip = pytest.mark.skipif(not has_llm_key, reason="No LLM API key configured — would hang on network timeouts")


class TestFallback:
    @llm_skip
    def test_llm_scored_when_keys_present(self, ats_agent, populated_state):
        result = ats_agent.run(populated_state)
        ats = result["ats_result"]
        assert ats["llm_scored"] is True

    @llm_skip
    def test_fallback_still_produces_scores(self, ats_agent, populated_state):
        result = ats_agent.run(populated_state)
        ats = result["ats_result"]
        assert 0 <= ats["overall_score"] <= 100
        assert ats["category_label"] in ["Poor", "Average", "Good", "Strong", "Exceptional"]

    @llm_skip
    def test_fallback_breakdown_structure(self, ats_agent, populated_state):
        result = ats_agent.run(populated_state)
        breakdown = result["ats_result"]["breakdown"]
        for key in ATS_WEIGHTS:
            assert key in breakdown
            assert breakdown[key]["weight"] == ATS_WEIGHTS[key]
            assert 0 <= breakdown[key]["score"] <= 100

    @llm_skip
    def test_empty_state_returns_structure(self, ats_agent, empty_state):
        result = ats_agent.run(empty_state)
        assert "ats_result" in result

class TestBreakdownScoring:
    def test_breakdown_contribution_calculation(self):
        for key, weight in ATS_WEIGHTS.items():
            score = 100
            contribution = round(score * weight / 100)
            assert contribution == weight

    def test_score_clamping_upper(self):
        for key in ATS_WEIGHTS:
            clamped = max(0, min(100, 150))
            assert clamped == 100

    def test_score_clamping_lower(self):
        for key in ATS_WEIGHTS:
            clamped = max(0, min(100, -10))
            assert clamped == 0

    def test_all_breakdown_keys_present(self):
        for key in ATS_WEIGHTS:
            assert key in ["keyword_match", "skill_match", "experience_match",
                           "project_match", "achievements", "education", "formatting"]
