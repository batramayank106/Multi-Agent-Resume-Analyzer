import pytest
from pydantic import ValidationError
from schemas.analysis import AnalysisRequest, AnalysisResponse

class TestAnalysisRequest:
    def test_valid_request(self):
        req = AnalysisRequest(resume_text="My resume", jd_text="A job")
        assert req.resume_text == "My resume"
        assert req.jd_text == "A job"

    def test_resume_text_required(self):
        with pytest.raises(ValidationError):
            AnalysisRequest()

    def test_optional_fields_default(self):
        req = AnalysisRequest(resume_text="test")
        assert req.jd_text is None
        assert req.parsed_skills == []
        assert req.parsed_experience == []
        assert req.parsed_projects == []
        assert req.parsed_education == []
        assert req.parsed_achievements == []

    def test_parsed_lists_accept_values(self):
        req = AnalysisRequest(
            resume_text="test",
            parsed_skills=["Python", "FastAPI"],
            parsed_experience=[{"company": "A"}],
            parsed_projects=[{"name": "P1"}],
            parsed_education=[{"degree": "BS"}],
            parsed_achievements=["Award"],
        )
        assert len(req.parsed_skills) == 2
        assert len(req.parsed_experience) == 1
        assert len(req.parsed_projects) == 1
        assert len(req.parsed_education) == 1
        assert len(req.parsed_achievements) == 1

class TestAnalysisResponse:
    def test_default_response(self):
        resp = AnalysisResponse(status="completed")
        assert resp.status == "completed"
        assert resp.ats_result is None
        assert resp.errors == []

    def test_all_fields_set(self):
        resp = AnalysisResponse(
            status="completed",
            ats_result={"overall_score": 85},
            recruiter_result={"score": 75},
            errors=[],
        )
        assert resp.ats_result["overall_score"] == 85
        assert resp.recruiter_result["score"] == 75

    def test_errors_list(self):
        resp = AnalysisResponse(status="completed", errors=["err1", "err2"])
        assert len(resp.errors) == 2
