import os, json
import pandas as pd
from datetime import datetime
from typing import Optional

from .ml_audit_agent import run_ml_audit
from .remediation_agent import run_fairness_remediation
from .controls_risks import eval_controls, build_risk_register
from .report_writer import write_audit_pack

# If you have your own RAG audit agent, keep using it.
from .rag_audit_agent import run_rag_audit
from .llm import load_local_llm
from .vectordb import build_retriever
from .run_paths import get_run_dirs
from .config import DEFAULT_LLM_ID

def now_utc():
    return datetime.utcnow().isoformat()

def run_aegis(
    rebuild_vectordb: bool = False,
    strict_citations: bool = True,
    llm_id: Optional[str] = None,
    dataset_csv_path: Optional[str] = None,
    target_col: Optional[str] = None,
    sensitive_col: Optional[str] = None,
):
    llm_id = llm_id or DEFAULT_LLM_ID
    run_id = f"AEGIS-RUN-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    ts = now_utc()

    run_dir, evidence_dir, reports_dir, chroma_dir = get_run_dirs(run_id)

    # RAG setup
    retriever = build_retriever(chroma_dir=chroma_dir, rebuild=rebuild_vectordb, k=4)
    gen, mode = load_local_llm(llm_id)

    logs = [{"node": "bootstrap", "llm_id": llm_id, "llm_mode": mode}]

    # 1) ML audit (dataset-aware)
    ml_summary = run_ml_audit(
        evidence_dir=evidence_dir,
        dataset_csv_path=dataset_csv_path,
        target_col=target_col,
        sensitive_col=sensitive_col
    )
    logs.append({"node": "ml_audit", "summary": ml_summary})

    # 2) Automated remediation if DI < 0.8
    try:
        fair = json.load(open(os.path.join(evidence_dir, "fairness.json")))
        di = float(fair.get("disparate_impact_selection_rate", 0.0))
    except Exception:
        di = 1.0

    remediation_pdf = None
    if di < 0.80:
        mitigation = run_fairness_remediation(evidence_dir, target_di=0.80)
        logs.append({"node": "remediation", "mitigation": mitigation})

    # 3) RAG audit
    rag_summary = run_rag_audit(evidence_dir, retriever, gen, strict=strict_citations)
    logs.append({"node": "rag_audit", "strict": strict_citations, "summary": rag_summary})

    # 4) Controls & risks
    cdf = eval_controls(evidence_dir)
    logs.append({"node": "controls", "counts": cdf["status"].value_counts().to_dict()})

    rdf = build_risk_register(evidence_dir)
    logs.append({"node": "risks", "count": int(len(rdf))})

    # 5) PDF report
    pdf = write_audit_pack(reports_dir, run_id, ts, cdf, rdf)
    logs.append({"node": "report", "pdf": pdf})

    return {
        "run_id": run_id,
        "timestamp": ts,
        "llm_mode": mode,
        "run_dir": run_dir,
        "evidence_dir": evidence_dir,
        "reports_dir": reports_dir,
        "control_csv": os.path.join(evidence_dir, "control_results.csv"),
        "risk_csv": os.path.join(evidence_dir, "risk_register.csv"),
        "audit_pdf": pdf,
        "remediation_pdf": remediation_pdf,
        "logs": logs
    }
