import os, json
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from fairlearn.metrics import MetricFrame, selection_rate

def _save_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=str)

def threshold_tune_groupwise(y_true, y_score, sensitive, target_di=0.80, grid=None):
    if grid is None:
        grid = np.linspace(0.05, 0.95, 37)

    best = None
    s = np.asarray(sensitive).astype(int)
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score).astype(float)

    # supports multi-group by tuning a single threshold per group (simple)
    groups = np.unique(s)
    if len(groups) == 2:
        g0, g1 = groups[0], groups[1]
        for t0 in grid:
            for t1 in grid:
                pred = np.zeros_like(y_true)
                pred[s == g0] = (y_score[s == g0] >= t0).astype(int)
                pred[s == g1] = (y_score[s == g1] >= t1).astype(int)

                mf = MetricFrame(metrics={"sr": selection_rate}, y_true=y_true, y_pred=pred, sensitive_features=s)
                sr0 = float(mf.by_group.loc[g0, "sr"])
                sr1 = float(mf.by_group.loc[g1, "sr"])
                di = float(min(sr0, sr1) / max(sr0, sr1)) if max(sr0, sr1) > 0 else 0.0
                acc = float(accuracy_score(y_true, pred))

                ok = di >= target_di
                score = (1 if ok else 0) * 1000 + acc
                cand = (score, di, acc, {int(g0): float(t0), int(g1): float(t1)})
                if (best is None) or (cand[0] > best[0]):
                    best = cand

        _, di_best, acc_best, thr = best
        return {"thresholds": thr, "di": float(di_best), "acc": float(acc_best)}

    # multi-group fallback: single shared threshold
    best = None
    for t in grid:
        pred = (y_score >= t).astype(int)
        mf = MetricFrame(metrics={"sr": selection_rate}, y_true=y_true, y_pred=pred, sensitive_features=s)
        sr = mf.by_group["sr"]
        di = float(sr.min() / sr.max()) if float(sr.max()) > 0 else 0.0
        acc = float(accuracy_score(y_true, pred))
        ok = di >= target_di
        score = (1 if ok else 0) * 1000 + acc
        cand = (score, di, acc, {"shared": float(t)})
        if (best is None) or (cand[0] > best[0]):
            best = cand

    _, di_best, acc_best, thr = best
    return {"thresholds": thr, "di": float(di_best), "acc": float(acc_best)}

def run_fairness_remediation(evidence_dir: str, target_di=0.80):
    scores_path = os.path.join(evidence_dir, "ml_eval_scores.csv")
    if not os.path.exists(scores_path):
        return {"skipped": True, "reason": "ml_eval_scores.csv not found"}

    df = pd.read_csv(scores_path)
    result = threshold_tune_groupwise(df["y_true"].values, df["y_score"].values, df["sensitive"].values, target_di=target_di)

    out = {"method": "group_threshold_tuning", "target_di": target_di, "after": result}
    _save_json(os.path.join(evidence_dir, "fairness_mitigation.json"), out)
    return out
