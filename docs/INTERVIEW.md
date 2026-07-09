# Interview Preparation Guide

The Interview Prep agent is one of the most personalized modules in CV Chacha — by Mayank Batra. It reads your actual resume content and the job description to generate questions that are specific to you — not generic interview templates.

---

## How the Interview Prep Agent Works

Defined in `agents/interview_agent.py`, the agent:

1. Receives the full `resume_text` and optional `jd_text` from the shared pipeline state
2. Calls the LLM with a prompt engineered to generate 10-14 questions across **6 diverse categories** (not just technical)
3. Parses the structured JSON response into a `questions` array
4. Returns the result via `interview_result`

The prompt explicitly instructs the model to reference specific projects, skills, and experiences from the resume. This means the same job description at two different companies will produce different question sets because the resume content is different.

---

## 6 Question Categories

Each generated question belongs to one of these categories:

### 1. Technical
Role-specific coding, algorithms, architecture, or domain knowledge. Tests core technical skills listed in the resume and required by the job description. These are role-specific — a data scientist will get ML theory questions while a backend engineer will get API design and database questions.

### 2. Management
Team leadership, project planning, prioritization, mentoring, and delegation. Evaluates your ability to lead engineering teams, make architectural decisions, manage timelines, and grow junior engineers — critical for senior and staff-level roles.

### 3. Communication
Explaining complex technical ideas to non-technical stakeholders, writing documentation, presenting proposals, and cross-team collaboration. Tests how well you can translate between business requirements and technical solutions.

### 4. Behavioral
Situational and STAR-method questions that evaluate soft skills, teamwork, conflict resolution, failure handling, and leadership. These draw on actual experiences mentioned in the resume. Expect "Tell me about a time when..." prompts.

### 5. Project & Portfolio
Deep-dive questions about specific projects listed on the resume. The agent reads the project description and generates questions about architecture decisions, challenges faced, technical trade-offs, and outcomes. You should be ready to defend every line of your projects.

### 6. HR & Culture
Career goals, why this company, strengths/weaknesses, work style preferences, and growth aspirations. Evaluates culture fit and long-term alignment with the role.

---

## Difficulty Levels

Every question is tagged with one of three difficulty levels:

| Level | Description |
|---|---|
| **Easy** | Foundational knowledge, definitions, basic experience questions |
| **Medium** | Applied knowledge, scenario-based, requires some depth |
| **Hard** | Advanced concepts, system design, complex trade-off analysis |

Distribution typically skews Medium (50-60%), with Easy (20-25%) and Hard (20-25%) making up the rest.

---

## How Questions Are Personalized

The agent uses four personalization signals:

| Signal | Source | Example |
|---|---|---|
| **Resume text** | Uploaded resume | "Tell me about your experience building the E-Commerce Platform mentioned in your resume." |
| **GitHub/portfolio links** | Resume content | "I noticed your GitHub link to the microservices project — walk me through the architecture decisions." |
| **Company name** | Extracted from JD | "What interests you about Acme Corp's approach to fintech?" |
| **Detected role** | JD title/requirements | "As a Senior Backend Engineer, how would you design a rate-limiting system?" |

### Category Diversity Guarantee

The prompt explicitly requires the LLM to generate **at least 1-2 questions per category**. This prevents the model from defaulting to all-technical questions. If you see a category missing, the pipeline ensures balanced coverage across Technical, Management, Communication, Behavioral, Project, and HR types.

---

## STAR Methodology

Many behavioral and project questions lend themselves to the **STAR** framework. Here is a quick reference:

| Component | What to Cover | Example |
|---|---|---|
| **S**ituation | Context — where and when | "Our checkout service was crashing under peak load during the holiday season." |
| **T**ask | Your specific responsibility | "I was tasked with redesigning the checkout flow to handle 10x traffic." |
| **A**ction | What you actually did | "I implemented a queue-based async processing system using Redis and Celery." |
| **R**esult | Measurable outcome | "Checkout success rate went from 78% to 99.5%, and the system handled 50K concurrent users." |

**Tips for stronger STAR answers:**
- Lead with the Result when it is impressive, then backtrack to explain how
- Use specific numbers — percentages, dollar amounts, time saved
- Keep each story to 60-90 seconds
- Practice bridging from "we" to "I" so the interviewer knows your personal contribution

---

## Using the Interview Prep Page

In the CV Chacha — by Mayank Batra frontend, the Interview Prep page is accessible from the sidebar navigation (icon: microphone).

### Steps

1. **Upload and analyze** — First, upload your resume and optional JD on the respective pages, then click **Run Full Analysis** on the Dashboard
2. **Navigate to Interview Prep** — Click the Interview Prep link in the sidebar
3. **Review generated questions** — Questions are displayed grouped by category with difficulty badges
4. **Filter by category** — Use the tabbed interface to filter Technical, Management, Communication, Behavioral, Project, or HR questions
5. **View rationale** — Each question includes a rationale explaining why it is being asked and what the interviewer is looking for
6. **Practice** — Read through questions and formulate STAR responses. The rationale text gives you hints about what a strong answer would include

### Tips for Best Results

- **Include a job description** — Questions are significantly more relevant when a JD is provided. Without one, the agent generates general questions based solely on your resume
- **Add GitHub/portfolio links** — If your resume includes links to GitHub or a portfolio, the agent will generate project-specific questions based on those repositories
- **Re-run analysis for different roles** — The same resume paired with different job descriptions will produce different question sets. Try multiple JDs to get a broader preparation range
- **Check the difficulty distribution** — If you see too many Easy questions, consider that your resume may lack depth in certain areas. Use the Skill Gap analysis page to identify and fill those gaps
