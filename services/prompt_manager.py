"""Prompt templates for all agents and services."""

from typing import Optional


class PromptManager:

    @staticmethod
    def ats_analysis(resume_text: str, jd_text: Optional[str] = None) -> list[dict]:
        system = """You are an ATS (Applicant Tracking System) expert. Analyze the resume against the job description.
Score each category on 0-100 and provide evidence for all deductions.
Base your analysis strictly on the provided resume and job description. Never fabricate or assume information not present in the text.

ATS Scoring Weights:
- Keyword Match: 30%
- Skill Match: 20%
- Experience Match: 15%
- Project Match: 15%
- Achievements: 10%
- Education: 5%
- Formatting: 5%

Return ONLY a raw JSON object with NO markdown, NO code fences, NO extra text.
Required keys: overall_score (int 0-100), category_scores (object with keys: 'Keyword Match', 'Skill Match', 'Experience Match', 'Project Match', 'Achievements', 'Education', 'Formatting'), evidence (array of objects with 'category' string and 'deductions' array of strings).
CRITICAL: Do NOT use unescaped quotes inside string values. Escape all internal quotes with backslash."""

        user = f"Resume:\n{resume_text}\n\n"
        if jd_text:
            user += f"Job Description:\n{jd_text}\n\n"
        user += "Provide detailed ATS analysis with evidence for every deduction. Return ONLY raw JSON with no markdown."

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    @staticmethod
    def recruiter_review(resume_text: str, jd_text: Optional[str] = None) -> list[dict]:
        system = """You are an experienced recruiter evaluating a resume. Be honest and constructive.
Base your evaluation strictly on the provided resume and job description. Never invent or assume skills, experience, or qualifications not present in the text.
Evaluate these dimensions 0-100: Readability, Impact, Leadership, Communication, Achievement.
Return ONLY valid JSON with keys: recruiter_score (int 0-100), decision (string PASS/REJECT), confidence (int 0-100), reasoning (string), dimension_scores (object with keys: Readability, Impact, Leadership, Communication, Achievement, each int 0-100)."""

        user = f"Resume:\n{resume_text}\n\n"
        if jd_text:
            user += f"Job Description:\n{jd_text}\n\n"
        user += "Evaluate this resume from a recruiter's perspective. Return ONLY valid JSON."

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    @staticmethod
    def hiring_manager_review(resume_text: str, jd_text: Optional[str] = None) -> list[dict]:
        system = """You are a hiring manager evaluating technical fit.
Base your evaluation strictly on the provided resume and job description. Never fabricate technical experience or qualifications.
Evaluate these dimensions 0-100: Technical Depth, Project Quality, Domain Fit, Growth Trajectory.
Return ONLY valid JSON with keys: hiring_manager_score (int 0-100), decision (string PASS/REJECT), reasoning (string), dimension_scores (object with keys: Technical Depth, Project Quality, Domain Fit, Growth Trajectory, each int 0-100)."""

        user = f"Resume:\n{resume_text}\n\n"
        if jd_text:
            user += f"Job Description:\n{jd_text}\n\n"
        user += "Evaluate this resume from a hiring manager's perspective. Return ONLY valid JSON."

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    @staticmethod
    def recruiter_simulator(resume_text: str, persona: str) -> list[dict]:
        personas = {
            "ATS": "You are an ATS system. Focus on keywords, formatting, and ATS rules.",
            "HR": "You are an HR professional. Focus on communication, leadership, and profile quality.",
            "Engineering Manager": "You are an Engineering Manager. Focus on projects, skills, and technical depth.",
        }
        system = personas.get(persona, personas["ATS"])
        system += "\nBase your assessment strictly on the provided resume text. Never assume or invent details not present."
        system += "\nReturn ONLY valid JSON with keys: decision (string PASS/REJECT), suggestions (string), confidence (int 0-100, vary based on how well the resume meets YOUR specific criteria — do NOT give the same confidence as other personas), explanation (string)."

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Evaluate this resume. Return ONLY valid JSON:\n{resume_text}"},
        ]

    @staticmethod
    def skill_gap(resume_skills: list[str], jd_requirements: list[str]) -> list[dict]:
        system = """Analyze skill gaps between the resume and job requirements.
Base analysis strictly on the provided skill lists. Missing skills are those listed in JD requirements but absent from the resume. Extra skills the candidate has beyond the JD are beneficial and should not be counted as gaps.
Also suggest 2-3 complementary skills not in the JD or resume that would strengthen the candidate's profile — only suggest skills commonly paired with the JD's existing requirements, with a brief reason for each.
Identify: required_skills, preferred_skills, missing_skills, priority_levels, gap_severity, suggested_additions (array of objects with 'skill' and 'reason').
Return ONLY valid JSON."""

        user = f"Resume Skills: {', '.join(resume_skills)}\nJD Requirements: {', '.join(jd_requirements)}"
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    @staticmethod
    def truthfulness_check(resume_text: str) -> list[dict]:
        system = """You are a truthfulness validator. Check for potentially exaggerated or false claims.
NEVER invent skills, projects, experience, or certifications.
Classify each claim as: Safe, Needs Verification, or Potentially Misleading.
Return ONLY valid JSON with keys: truthfulness_score (int 0-100), flagged_items (array of objects with 'claim', 'classification', 'reasoning')."""

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Check this resume for truthfulness. Return ONLY valid JSON:\n{resume_text}"},
        ]

    @staticmethod
    def interview_questions(resume_text: str, jd_text: Optional[str] = None) -> list[dict]:
        system = """Generate interview questions based on the resume and job description.
Base questions strictly on the candidate's actual experience and the role requirements. Never fabricate project details or assume technologies not mentioned.
Cover ALL these categories (at least 1-2 per category):
- Technical: role-specific coding, algorithms, architecture, or domain knowledge
- Management: team leadership, project planning, prioritization, mentoring
- Communication: explaining complex ideas, stakeholder management, documentation
- Behavioral: STAR-based situational, conflict resolution, teamwork, failure handling
- Project & Portfolio: deep-dive into specific projects, design choices, trade-offs
- HR & Culture: career goals, why this company, strengths/weaknesses, work style
Mark each question with one of these categories: Technical, Management, Communication, Behavioral, Project, HR.
Mark difficulty as Easy, Medium, or Hard.
Return ONLY a valid JSON array of objects with keys: question (string), category (string), difficulty (string)."""

        user = f"Resume:\n{resume_text}\n\n"
        if jd_text:
            user += f"Job Description:\n{jd_text}\n\n"
        user += "Generate 10-14 diverse interview questions covering technical, management, communication, behavioral, project, and HR categories. Return ONLY a valid JSON array."

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    @staticmethod
    def resume_rewrite(resume_text: str, suggestions: str) -> list[dict]:
        system = """Rewrite the resume bullet points and descriptions based on the suggestions.
IMPORTANT: NEVER change template, layout, fonts, colors, or margins.
Only modify: bullet points, descriptions, wording, keywords.
Return the updated resume text."""

        user = f"Original Resume:\n{resume_text}\n\nSuggestions:\n{suggestions}\n\nProvide the updated resume."
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    @staticmethod
    def company_insight(company_name: str, jd_text: Optional[str] = None) -> list[dict]:
        system = """You are a company research analyst. Analyze the company and job description.
Distinguish between information stated in the job description and general knowledge. Clearly label speculation.
Provide: company_overview, culture_fit_indicators, growth_opportunities, red_flags, industry_position.
Also provide employee review insights: culture_score (int 0-100), review_summary (string), pros (array of strings), cons (array of strings), work_life_balance (Good/Average/Poor), career_growth (Good/Average/Poor).
Rate overall_suitability as POOR/FAIR/GOOD/EXCELLENT.
Return ONLY valid JSON."""

        user = f"Company: {company_name}\n"
        if jd_text:
            user += f"Job Description:\n{jd_text}\n\n"
        user += "Analyze this company and provide insights including employee review data."

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    @staticmethod
    def selection_probability(
        ats_score: int,
        recruiter_score: int,
        hm_score: int,
        skill_gap_severity: str,
        truthfulness_score: int,
    ) -> list[dict]:
        system = """You are a hiring probability analyst. Based on multi-dimensional assessment scores,
estimate the candidate's probability of advancing through each stage.
Base your estimate solely on the provided scores. Do not fabricate additional candidate attributes.
Stages: ATS Screen, Recruiter Review, HM Review, On-site Interview, Offer.
Return ONLY valid JSON with keys: overall_probability (int 0-100), stage_probabilities (object),
key_factors (array of strings), recommendations (array of strings)."""

        user = f"""ATS Score: {ats_score}/100
Recruiter Score: {recruiter_score}/100
Hiring Manager Score: {hm_score}/100
Skill Gap Severity: {skill_gap_severity}
Truthfulness Score: {truthfulness_score}/100

Estimate the selection probability for this candidate."""
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    @staticmethod
    def salary_estimate(company_name: str, jd_text: Optional[str], parsed_skills: list[str]) -> list[dict]:
        system = """You are a compensation analyst for the Indian job market. Estimate the expected salary range for this role × company × location in India.
Consider: role seniority, required skills, company size/prestige, location (if mentioned), industry standards in India.
State clearly that this is an estimate based on general market knowledge, not real-time data.
IMPORTANT: Always assume India market rates in INR. Return salary in LPA (Lakhs Per Annum).
Return ONLY valid JSON with keys:
- salary_range (string, e.g. "₹12 LPA - ₹18 LPA")
- currency (string, e.g. "INR")
- confidence (string: "Low" / "Medium" / "High")
- factors (array of strings describing key factors affecting the estimate, India-focused)
- source (string: "LLM Knowledge")"""
        user = f"Company: {company_name}\n"
        if jd_text:
            user += f"Job Description:\n{jd_text}\n\n"
        user += f"Key Skills: {', '.join(parsed_skills) if parsed_skills else 'Not specified'}\n\n"
        user += "Estimate the salary range for this role in Indian Rupees (INR) as LPA. Return ONLY valid JSON."
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    @staticmethod
    def famous_questions(company_name: str, jd_text: Optional[str]) -> list[dict]:
        system = """You are a career coach who knows famous interview questions from top tech companies.
Generate well-known interview questions for the specified company.
Only include questions that are genuinely known to be asked by this company. Do not fabricate questions.
Include questions from: Leadership Principles (Amazon), System Design (Google), Behavioral (Meta), etc.
Return ONLY a valid JSON array of objects with keys:
- question (string)
- source (string, e.g. "Amazon LPs", "Google SD", "Meta Behavioral")
- difficulty (string: "Easy" / "Medium" / "Hard")
- round (string: "Phone Screen" / "Onsite" / "System Design" / "Behavioral" / "Hiring Manager")"""
        user = f"Company: {company_name}\n"
        if jd_text:
            user += f"Job Description:\n{jd_text}\n\n"
        user += "Generate famous interview questions for this company. Return ONLY a valid JSON array."
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    @staticmethod
    def chatbot_response(question: str, context: str, history: list[dict]) -> list[dict]:
        system = """You are a resume coaching assistant. Use the provided context to answer questions.
Provide helpful, specific advice. Cite your sources when possible.
Be encouraging but honest. Never fabricate resume strategies or career advice. If unsure, say so."""

        messages = [{"role": "system", "content": system}]
        for h in history[-10:]:
            messages.append(h)
        messages.append({
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        })
        return messages


prompt_manager = PromptManager()
