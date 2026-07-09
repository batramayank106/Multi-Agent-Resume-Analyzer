import difflib
import logging
import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from services.auth_service import get_current_user
from models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/compare", tags=["comparison"])


class CompareRequest(BaseModel):
    text_a: str
    text_b: str
    skills_a: list[str] = []
    skills_b: list[str] = []


class DiffLine(BaseModel):
    line: str
    type: str  # "equal", "insert", "delete"


class SkillsDiff(BaseModel):
    added: list[str] = []
    removed: list[str] = []
    common: list[str] = []


class CompareResponse(BaseModel):
    lines_a: list[DiffLine]
    lines_b: list[DiffLine]
    skills: SkillsDiff
    added_lines: int
    removed_lines: int
    unchanged_lines: int


@router.post("/resumes", response_model=CompareResponse)
async def compare_resumes(body: CompareRequest, current_user: User = Depends(get_current_user)):
    lines_a = body.text_a.splitlines()
    lines_b = body.text_b.splitlines()

    matcher = difflib.SequenceMatcher(None, lines_a, lines_b)
    result_a: list[DiffLine] = []
    result_b: list[DiffLine] = []

    added = 0
    removed = 0
    unchanged = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for i in range(i1, i2):
                result_a.append(DiffLine(line=lines_a[i], type="equal"))
            for j in range(j1, j2):
                result_b.append(DiffLine(line=lines_b[j], type="equal"))
            unchanged += (i2 - i1)
        elif tag == "replace":
            for i in range(i1, i2):
                result_a.append(DiffLine(line=lines_a[i], type="delete"))
                removed += 1
            for j in range(j1, j2):
                result_b.append(DiffLine(line=lines_b[j], type="insert"))
                added += 1
        elif tag == "delete":
            for i in range(i1, i2):
                result_a.append(DiffLine(line=lines_a[i], type="delete"))
                removed += 1
        elif tag == "insert":
            for j in range(j1, j2):
                result_b.append(DiffLine(line=lines_b[j], type="insert"))
                added += 1

    skills_a_norm = {s.strip().lower() for s in body.skills_a if s.strip()}
    skills_b_norm = {s.strip().lower() for s in body.skills_b if s.strip()}

    skills = SkillsDiff(
        added=[s for s in body.skills_b if s.strip().lower() in skills_b_norm - skills_a_norm],
        removed=[s for s in body.skills_a if s.strip().lower() in skills_a_norm - skills_b_norm],
        common=[s for s in body.skills_a if s.strip().lower() in skills_a_norm & skills_b_norm],
    )

    return CompareResponse(
        lines_a=result_a,
        lines_b=result_b,
        skills=skills,
        added_lines=added,
        removed_lines=removed,
        unchanged_lines=unchanged,
    )
