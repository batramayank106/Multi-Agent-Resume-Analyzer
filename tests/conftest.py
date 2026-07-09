import pytest
from agents.ats_agent import ATSAgent, ATS_WEIGHTS, SCORE_CATEGORIES

@pytest.fixture
def ats_agent():
    return ATSAgent()

@pytest.fixture
def sample_resume():
    return """John Doe
Software Engineer

Skills: Python, FastAPI, PostgreSQL, Docker, AWS, Git

Experience:
Senior Software Engineer, Tech Corp (2020-Present)
- Built microservices architecture with FastAPI and PostgreSQL
- Deployed Docker containers on AWS ECS

Projects:
E-commerce Platform - Full-stack application
CI/CD Pipeline - Automated deployment system

Education:
MS Computer Science, University of Technology

Achievements:
Published 2 research papers
Led team of 5 engineers"""

@pytest.fixture
def sample_jd():
    return """Software Engineer

Requirements:
- Python, FastAPI, PostgreSQL
- Docker, AWS, Kubernetes
- 3+ years experience
- Strong problem-solving skills
- Machine Learning experience preferred"""

@pytest.fixture
def empty_state():
    return {
        "resume_id": None,
        "jd_id": None,
        "resume_text": "",
        "jd_text": None,
        "parsed_skills": [],
        "parsed_experience": [],
        "parsed_projects": [],
        "parsed_education": [],
        "parsed_achievements": [],
        "ats_result": None,
        "recruiter_result": None,
        "hiring_manager_result": None,
        "simulator_results": None,
        "skill_gap_result": None,
        "truthfulness_result": None,
        "company_result": None,
        "salary_result": None,
        "rewrite_result": None,
        "interview_result": None,
        "famous_questions_result": None,
        "selection_probability": None,
        "errors": [],
        "status": "started",
    }

@pytest.fixture
def populated_state(sample_resume, sample_jd):
    return {
        "resume_id": None,
        "jd_id": None,
        "resume_text": sample_resume,
        "jd_text": sample_jd,
        "parsed_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Kubernetes"],
        "parsed_experience": [{"company": "Tech Corp", "title": "Senior Software Engineer", "years": "2020-Present"}],
        "parsed_projects": [{"name": "E-commerce Platform"}, {"name": "CI/CD Pipeline"}],
        "parsed_education": [{"degree": "MS Computer Science", "university": "University of Technology"}],
        "parsed_achievements": ["Published 2 research papers", "Led team of 5 engineers"],
        "ats_result": None,
        "recruiter_result": None,
        "hiring_manager_result": None,
        "simulator_results": None,
        "skill_gap_result": None,
        "truthfulness_result": None,
        "company_result": None,
        "salary_result": None,
        "rewrite_result": None,
        "interview_result": None,
        "famous_questions_result": None,
        "selection_probability": None,
        "errors": [],
        "status": "started",
    }
