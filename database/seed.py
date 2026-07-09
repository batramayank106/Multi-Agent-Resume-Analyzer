"""Seed the database with sample data for testing."""

import logging
from database.connection import init_db, SyncSessionLocal
from models import Resume, JobDescription, CompanyInsight, User
from services.auth_service import hash_password

logger = logging.getLogger(__name__)


def seed_database():
    init_db()
    logger.info("Seeding database with sample data...")

    with SyncSessionLocal() as session:
        if session.query(Resume).count() > 0:
            logger.info("Database already seeded, skipping.")
            return

        if session.query(User).count() == 0:
            demo_user = User(
                email="demo@cvchacha.com",
                username="demo",
                hashed_password=hash_password("Demo@1234"),
                role="user",
                is_active=True,
            )
            session.add(demo_user)
            logger.info("Created demo user: demo@cvchacha.com / Demo@1234")
            session.flush()

        resume = Resume(
            filename="sample_resume.pdf",
            original_text="""John Doe
Software Engineer with 5 years of experience in building scalable applications.

Skills: Python, FastAPI, React, PostgreSQL, Docker, AWS, TypeScript, GraphQL

Experience:
Senior Software Engineer at TechCorp (2021-Present)
- Built microservices architecture handling 1M+ requests/day
- Reduced API response time by 40% through optimization
- Led team of 4 engineers on migration from monolith to microservices

Software Engineer at StartupX (2019-2021)
- Developed RESTful APIs using FastAPI and PostgreSQL
- Implemented CI/CD pipelines with GitHub Actions
- Wrote comprehensive unit and integration tests

Projects:
E-Commerce Platform - Full-stack application with React frontend and FastAPI backend
Real-time Chat Application - WebSocket-based chat with Redis pub/sub

Education:
B.S. Computer Science, University of Technology (2015-2019)

Achievements:
- Published 2 technical blog posts on system design
- Speaker at PyCon 2023
""",
            parsed_skills=["Python", "FastAPI", "React", "PostgreSQL", "Docker", "AWS", "TypeScript", "GraphQL"],
            parsed_experience=[
                {
                    "title": "Senior Software Engineer",
                    "company": "TechCorp",
                    "period": "2021-Present",
                    "bullets": [
                        "Built microservices architecture handling 1M+ requests/day",
                        "Reduced API response time by 40% through optimization",
                        "Led team of 4 engineers on migration from monolith to microservices",
                    ],
                },
                {
                    "title": "Software Engineer",
                    "company": "StartupX",
                    "period": "2019-2021",
                    "bullets": [
                        "Developed RESTful APIs using FastAPI and PostgreSQL",
                        "Implemented CI/CD pipelines with GitHub Actions",
                        "Wrote comprehensive unit and integration tests",
                    ],
                },
            ],
            parsed_projects=[
                {"name": "E-Commerce Platform", "description": "Full-stack application with React frontend and FastAPI backend"},
                {"name": "Real-time Chat Application", "description": "WebSocket-based chat with Redis pub/sub"},
            ],
            parsed_education=[
                {"degree": "B.S. Computer Science", "institution": "University of Technology", "period": "2015-2019"},
            ],
            parsed_achievements=[
                "Published 2 technical blog posts on system design",
                "Speaker at PyCon 2023",
            ],
        )
        session.add(resume)

        jd = JobDescription(
            title="Senior Software Engineer",
            company="TechCorp",
            description_text="""We are looking for a Senior Software Engineer to join our team.

Requirements:
- 5+ years of experience in software development
- Strong proficiency in Python, FastAPI, and TypeScript
- Experience with microservices architecture
- Knowledge of PostgreSQL, Docker, and AWS
- Experience with GraphQL is a plus
- Excellent communication and leadership skills

Nice to have:
- Experience with React or similar frontend frameworks
- CI/CD pipeline experience
- Published technical content
""",
            parsed_requirements={
                "required_skills": ["Python", "FastAPI", "TypeScript", "PostgreSQL", "Docker", "AWS"],
                "preferred_skills": ["GraphQL", "React", "Kubernetes"],
                "experience_years": 5,
                "key_areas": ["microservices", "leadership", "communication"],
            },
        )
        session.add(jd)

        session.commit()
        logger.info(f"Created resume id={resume.id}, job description id={jd.id}")

    logger.info("Database seeded successfully!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_database()
