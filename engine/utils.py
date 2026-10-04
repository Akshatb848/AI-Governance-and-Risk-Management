import re
from datetime import datetime, timezone

# Pre-LLM input guard: requests matching these never reach the model.
SENSITIVE_PATTERNS = [
    r"\bsystem prompt\b", r"\bapi keys?\b", r"\bsecrets?\b", r"\bpasswords?\b",
    r"\bprivate data\b", r"\bphone numbers?\b", r"\baddress(es)?\b", r"\bssn\b",
]

# First-person phrases that indicate the model itself declined. Only the opening
# sentence is checked, so an answer *about* refusal policy ("attempts must be
# refused [1]") is not mistaken for a refusal.
REFUSAL_PATTERNS = [
    r"\bi (?:can(?:'|no)?t|cannot|won'?t|am unable|'m unable|am not able|'m not able)\b",
    r"\b(?:sorry|apologi[sz]e)\b", r"\bcannot (?:help|provide|share|comply|assist|reveal)\b",
    r"\bunable to (?:help|provide|share|comply|assist|reveal)\b", r"^\s*insufficient context\b",
    r"\bnot (?:allowed|permitted) to\b",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_run_id(prefix: str = "AEGIS-RUN") -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"


def is_sensitive(q: str) -> bool:
    ql = (q or "").lower()
    return any(re.search(p, ql) for p in SENSITIVE_PATTERNS)


def looks_like_refusal(answer: str) -> bool:
    first = re.split(r"(?<=[.!?])\s|\n", (answer or "").strip().lower(), maxsplit=1)[0]
    return any(re.search(p, first) for p in REFUSAL_PATTERNS)


def is_policy_like(q: str) -> bool:
    ql = (q or "").lower()
    keys = ["policy", "standard", "requirement", "must", "should", "control", "prompt injection",
            "citation", "governance", "risk", "drift"]
    return any(k in ql for k in keys)


def has_citations(text: str) -> bool:
    return bool(re.search(r"\[\d+\]", text or ""))
