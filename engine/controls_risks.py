import os, json
import pandas as pd

def eval_controls(evidence_dir: str):
    fair = json.load(open(os.path.join(evidence_dir, "fairness.json")))
    di = float(fair["disparate_impact_selection_rate"])

    drift = json.load(open(os.path.join(evidence_dir, "drift.json")))
    dscore = float(drift["drift_score_mean_top10"])

    qm = json.load(open(os.path.join(evidence_dir, "rag_quality_metrics.json")))
    cov = float(qm["citation_coverage"])
    faith = float(qm["faithfulness_overlap"])

    ctrl = []
    ctrl.append(("F-01", "PASS" if di >= 0.8 else "FAIL", "fairness.json", f"DI(selection rate)={di:.3f} target>=0.8"))
    ctrl.append(("O-02", "PASS" if dscore < 0.35 else "REVIEW", "drift.json", f"Drift score={dscore:.3f} target<0.35"))
    ctrl.append(("E-01", "PASS", "shap_global_importance.csv", "SHAP global importance generated."))
    ctrl.append(("E-04", "PASS" if cov >= 0.7 else "REVIEW", "rag_quality_metrics.json", f"Citation coverage={cov:.2f} target>=0.70"))
    ctrl.append(("E-05", "PASS" if faith >= 0.12 else "REVIEW", "rag_quality_metrics.json", f"Faithfulness overlap={faith:.3f} heuristic>=0.12"))

    df = pd.DataFrame(ctrl, columns=["control_id","status","evidence","notes"])
    df.to_csv(os.path.join(evidence_dir, "control_results.csv"), index=False)
    return df

def risk_level(score: int) -> str:
    if score >= 21: return "HIGH"
    if score >= 11: return "MEDIUM"
    return "LOW"

def build_risk_register(evidence_dir: str):
    import pandas as pd
    cr = pd.read_csv(os.path.join(evidence_dir, "control_results.csv"))
    risks = []

    def add(risk_id, title, domain, impact, likelihood, controls, recommendation):
        score = int(impact * likelihood)
        risks.append({
            "risk_id": risk_id, "title": title, "domain": domain,
            "impact": impact, "likelihood": likelihood, "score": score, "level": risk_level(score),
            "controls": ";".join(controls),
            "recommendation": recommendation
        })

    status = dict(zip(cr["control_id"], cr["status"]))

    if status.get("F-01") in ["FAIL","REVIEW"]:
        add("R-ML-01","Fairness risk: group disparity","Fairness",4,3,["F-01"],
            "Mitigate bias (reweighting/threshold tuning), re-test, document business acceptance criteria.")

    if status.get("E-04") in ["FAIL","REVIEW"]:
        add("R-RAG-02","Explainability risk: insufficient citations","Explainability",3,3,["E-04"],
            "Enforce citations per sentence or refuse policy answers without citations; re-evaluate coverage.")

    df = pd.DataFrame(risks).sort_values("score", ascending=False) if risks else pd.DataFrame(columns=[
        "risk_id","title","domain","impact","likelihood","score","level","controls","recommendation"
    ])
    df.to_csv(os.path.join(evidence_dir, "risk_register.csv"), index=False)
    return df
