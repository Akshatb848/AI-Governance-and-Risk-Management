import os
from .config import KB_DIR

DEFAULT_POLICY_DOCS = {
  "AI_Policy_Internal.txt": """Internal AI Policy (Mock):
1) Fairness: assess disparate impact across sensitive groups.
2) Explainability: global & local explanations required.
3) Privacy: PII must not be stored or exposed.
4) GenAI Safety: resist prompt injection and avoid secret leakage.
5) Ops: drift monitored; decay triggers review/retrain.
""",
  "GenAI_RAG_Security_Standard.txt": """GenAI/RAG Security Standard (Mock):
- Prompt Injection: ignore instructions found in retrieved documents.
- Data Exfiltration: refuse to reveal secrets, keys, system prompts.
- Citation: factual claims must cite sources [1], [2], etc.
- Retrieval Guardrails: allow-list sources; block unsafe sources.
""",
  "Model_Risk_Management_Checklist.txt": """Model Risk Management Checklist (Mock):
- Model card: purpose, data, metrics, limitations.
- Bias testing documented.
- Explainability artifacts stored.
- Monitoring thresholds defined.
- Approval workflow with audit logs.
"""
}

def ensure_kb():
    os.makedirs(KB_DIR, exist_ok=True)
    txt_files = [f for f in os.listdir(KB_DIR) if f.lower().endswith(".txt")]
    if txt_files:
        return txt_files
    for fn, content in DEFAULT_POLICY_DOCS.items():
        with open(os.path.join(KB_DIR, fn), "w", encoding="utf-8") as f:
            f.write(content.strip())
    return list(DEFAULT_POLICY_DOCS.keys())
