"""AEGIS multi-agent workflow, orchestrated with LangGraph.

    planner -> ml_audit -> [remediation if DI < 0.80] -> rag_audit -> controls -> risks -> report

Every node appends to a shared trace that is written to workflow_trace.json, so
an auditor can see which agent produced which evidence and decision.
"""

import json
import operator
import os
import time
from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from .config import DEFAULT_LLM_ID, FAIRNESS_DI_MIN
from .controls_risks import build_risk_register, eval_controls
from .ml_audit_agent import run_ml_audit
from .rag_audit_agent import run_rag_audit
from .remediation_agent import run_fairness_remediation
from .remediation_report import write_remediation_addendum
from .report_writer import write_audit_pack
from .run_paths import get_run_dirs
from .run_store import upsert_run
from .utils import new_run_id, now_utc


class AegisState(TypedDict, total=False):
    # inputs
    run_id: str
    timestamp: str
    llm_id: str
    strict_citations: bool
    rebuild_vectordb: bool
    dataset_csv_path: Optional[str]
    target_col: Optional[str]
    sensitive_col: Optional[str]
    # injected resources (optional; loaded lazily otherwise)
    gen: Any
    retriever: Any
    # produced along the way
    llm_mode: str
    run_dir: str
    evidence_dir: str
    reports_dir: str
    chroma_dir: str
    ml_summary: dict
    mitigation: Optional[dict]
    rag_summary: dict
    control_counts: dict
    risk_count: int
    audit_pdf: str
    remediation_pdf: Optional[str]
    trace: Annotated[list, operator.add]


def _event(node: str, started: float, **payload) -> list:
    return [{"node": node, "at": now_utc(), "seconds": round(time.time() - started, 2), **payload}]


def node_planner(state: AegisState) -> dict:
    t = time.time()
    run_dir, evidence_dir, reports_dir, chroma_dir = get_run_dirs(state["run_id"])
    plan = {"llm_id": state["llm_id"], "strict_citations": state["strict_citations"],
            "dataset": state.get("dataset_csv_path") or "demo: sklearn breast cancer"}
    return {"run_dir": run_dir, "evidence_dir": evidence_dir, "reports_dir": reports_dir,
            "chroma_dir": chroma_dir, "trace": _event("planner", t, plan=plan)}


def node_ml_audit(state: AegisState) -> dict:
    t = time.time()
    summary = run_ml_audit(state["evidence_dir"], state.get("dataset_csv_path"),
                           state.get("target_col"), state.get("sensitive_col"))
    return {"ml_summary": summary, "trace": _event("ml_audit", t, summary=summary)}


def route_after_ml(state: AegisState) -> str:
    return "remediation" if state["ml_summary"]["di"] < FAIRNESS_DI_MIN else "rag_audit"


def node_remediation(state: AegisState) -> dict:
    t = time.time()
    mitigation = run_fairness_remediation(state["evidence_dir"], target_di=FAIRNESS_DI_MIN)
    pdf = None
    if not mitigation.get("skipped"):
        pdf = write_remediation_addendum(state["reports_dir"], state["run_id"], state["timestamp"],
                                         state["ml_summary"]["di"], mitigation)
    return {"mitigation": mitigation, "remediation_pdf": pdf,
            "trace": _event("remediation", t, mitigation=mitigation, pdf=pdf)}


def node_rag_audit(state: AegisState) -> dict:
    t = time.time()
    retriever = state.get("retriever")
    if retriever is None:
        from .vectordb import build_retriever
        retriever = build_retriever(chroma_dir=state["chroma_dir"], rebuild=state["rebuild_vectordb"], k=4)
    gen, mode = state.get("gen"), state.get("llm_mode") or "injected"
    if gen is None:
        from .llm import load_local_llm
        gen, mode = load_local_llm(state["llm_id"])
    summary = run_rag_audit(state["evidence_dir"], retriever, gen, strict=state["strict_citations"])
    return {"rag_summary": summary, "llm_mode": mode,
            "trace": _event("rag_audit", t, llm_mode=mode, summary=summary)}


def node_controls(state: AegisState) -> dict:
    t = time.time()
    cdf = eval_controls(state["evidence_dir"])
    counts = cdf["status"].value_counts().to_dict()
    return {"control_counts": counts, "trace": _event("controls", t, counts=counts)}


def node_risks(state: AegisState) -> dict:
    t = time.time()
    rdf = build_risk_register(state["evidence_dir"])
    return {"risk_count": int(len(rdf)), "trace": _event("risks", t, count=int(len(rdf)),
                                                         risk_ids=rdf["risk_id"].tolist())}


def node_report(state: AegisState) -> dict:
    import pandas as pd
    t = time.time()
    ev = state["evidence_dir"]
    cdf = pd.read_csv(os.path.join(ev, "control_results.csv"))
    rdf = pd.read_csv(os.path.join(ev, "risk_register.csv"))
    redteam = json.load(open(os.path.join(ev, "redteam_summary.json")))
    pdf = write_audit_pack(state["reports_dir"], state["run_id"], state["timestamp"], cdf, rdf, redteam)
    return {"audit_pdf": pdf, "trace": _event("report", t, pdf=pdf)}


def build_graph():
    g = StateGraph(AegisState)
    for name, fn in [("planner", node_planner), ("ml_audit", node_ml_audit), ("remediation", node_remediation),
                     ("rag_audit", node_rag_audit), ("controls", node_controls), ("risks", node_risks),
                     ("report", node_report)]:
        g.add_node(name, fn)
    g.add_edge(START, "planner")
    g.add_edge("planner", "ml_audit")
    g.add_conditional_edges("ml_audit", route_after_ml, {"remediation": "remediation", "rag_audit": "rag_audit"})
    g.add_edge("remediation", "rag_audit")
    g.add_edge("rag_audit", "controls")
    g.add_edge("controls", "risks")
    g.add_edge("risks", "report")
    g.add_edge("report", END)
    return g.compile()


def run_aegis(
    rebuild_vectordb: bool = False,
    strict_citations: bool = True,
    llm_id: Optional[str] = None,
    dataset_csv_path: Optional[str] = None,
    target_col: Optional[str] = None,
    sensitive_col: Optional[str] = None,
    gen: Any = None,
    llm_mode: Optional[str] = None,
    retriever: Any = None,
) -> dict:
    """Run the full audit. Pass `gen`/`retriever` to reuse a loaded model or to test with fakes."""
    state: AegisState = {
        "run_id": new_run_id(),
        "timestamp": now_utc(),
        "llm_id": llm_id or DEFAULT_LLM_ID,
        "strict_citations": strict_citations,
        "rebuild_vectordb": rebuild_vectordb,
        "dataset_csv_path": dataset_csv_path,
        "target_col": target_col,
        "sensitive_col": sensitive_col,
        "gen": gen,
        "llm_mode": llm_mode or "",
        "retriever": retriever,
        "remediation_pdf": None,
        "trace": [],
    }
    final = build_graph().invoke(state)

    ev = final["evidence_dir"]
    with open(os.path.join(ev, "workflow_trace.json"), "w") as f:
        json.dump(final["trace"], f, indent=2, default=str)

    result = {
        "run_id": final["run_id"],
        "timestamp": final["timestamp"],
        "llm_id": final["llm_id"],
        "llm_mode": final.get("llm_mode", ""),
        "run_dir": final["run_dir"],
        "evidence_dir": ev,
        "reports_dir": final["reports_dir"],
        "control_csv": os.path.join(ev, "control_results.csv"),
        "risk_csv": os.path.join(ev, "risk_register.csv"),
        "audit_pdf": final["audit_pdf"],
        "remediation_pdf": final.get("remediation_pdf"),
        "logs": final["trace"],
    }
    upsert_run(result)
    return result
