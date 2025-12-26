import re
from datetime import datetime

SENSITIVE_PATTERNS = [
    r"\bsystem prompt\b", r"\bapi key\b", r"\bsecret\b", r"\bpassword\b",
    r"\bprivate data\b", r"\bphone number\b", r"\baddress\b", r"\bssn\b",
]

def now_utc():
    return datetime.utcnow().isoformat()

def new_run_id(prefix="AEGIS"):
    return f"{prefix}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

def is_sensitive(q: str) -> bool:
    ql = (q or "").lower()
    return any(re.search(p, ql) for p in SENSITIVE_PATTERNS)

def is_policy_like(q: str) -> bool:
    ql = (q or "").lower()
    keys = ["policy","standard","requirement","must","should","control","prompt injection","citation","governance","risk","drift"]
    return any(k in ql for k in keys)

def has_citations(text: str) -> bool:
    return bool(re.search(r"\[\d+\]", text or ""))
