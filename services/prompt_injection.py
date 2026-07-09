import re
import logging

logger = logging.getLogger(__name__)

_SUSPICIOUS_PATTERNS: list[tuple[str, str]] = [
    ("system_override", r"(?i)(ignore|override|forget|disregard|skip)\s+(all\s+)?(prior|previous|above|system|instructions)"),
    ("role_switch", r"(?i)(you are now|act as|pretend|from now on)\s+(a\s+)?(different|new|free|unrestricted|admin|developer)"),
    ("prompt_leak", r"(?i)(print|show|reveal|output|display|leak|dump)\s+(your\s+)?(prompt|instructions|system|rules)"),
    ("delimiter_break", r"(?i)(---|\"\"\"|'''|<\|im_end|<\s*system\s*>)"),
    ("token_theft", r"(?i)(api[_-]?key|token|password|secret|credential)"),
    ("jailbreak_prefix", r"(?i)^(sure|okay|fine|alright),?\s+(i'll|here|i will|let me)"),
]

INJECTION_THRESHOLD = 2


def check_prompt_injection(text: str) -> tuple[bool, list[str], int]:
    matches: list[str] = []
    score = 0
    for name, pattern in _SUSPICIOUS_PATTERNS:
        found = re.findall(pattern, text)
        if found:
            count = len(found)
            score += count
            matches.append(f"{name} (×{count})")
    is_suspicious = score >= INJECTION_THRESHOLD
    if is_suspicious:
        logger.warning(f"Prompt injection detected (score={score}): {matches}")
    return is_suspicious, matches, score
