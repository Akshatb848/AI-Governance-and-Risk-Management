import os
import json

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score


def _save_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=str)


def _di(pred, s, groups):
    rates = [pred[s == g].mean() if (s == g).any() else 0.0 for g in groups]
    return float(min(rates) / max(rates)) if max(rates) > 0 else 0.0


def _candidates(scores):
    """Thresholds at score quantiles plus the extremes, so every selection rate
    from 0% to 100% is reachable even when scores are very confident."""
    qs = np.quantile(scores, np.linspace(0, 1, 41))
    return np.unique(np.concatenate([qs, [0.0, 1.0 + 1e-9]]))


def threshold_tune_groupwise(y_true, y_score, sensitive, target_di=0.80):
    """Pick one decision threshold per group. Among settings that reach the DI
    target, keep the most accurate; if none reach it, keep the fairest."""
    s = np.asarray(sensitive).astype(int)
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score).astype(float)
    groups = np.unique(s)

    if len(groups) != 2:
        # multi-group fallback: one shared threshold
        best = None
        for t in _candidates(y_score):
            pred = (y_score >= t).astype(int)
            di, acc = _di(pred, s, groups), float(accuracy_score(y_true, pred))
            key = (di >= target_di, acc if di >= target_di else di)
            if best is None or key > best[0]:
                best = (key, di, acc, {"shared": float(t)})
        _, di_best, acc_best, thr = best
        return {"thresholds": thr, "di": di_best, "acc": acc_best, "target_met": di_best >= target_di}

    g0, g1 = groups
    m0, m1 = s == g0, s == g1
    best = None
    for t0 in _candidates(y_score[m0]):
        p0 = (y_score[m0] >= t0).astype(int)
        for t1 in _candidates(y_score[m1]):
            pred = np.zeros_like(y_true)
            pred[m0] = p0
            pred[m1] = (y_score[m1] >= t1).astype(int)
            di, acc = _di(pred, s, groups), float(accuracy_score(y_true, pred))
            key = (di >= target_di, acc if di >= target_di else di)
            if best is None or key > best[0]:
                best = (key, di, acc, {str(int(g0)): float(t0), str(int(g1)): float(t1)})
    _, di_best, acc_best, thr = best
    return {"thresholds": thr, "di": di_best, "acc": acc_best, "target_met": di_best >= target_di}


def run_fairness_remediation(evidence_dir: str, target_di=0.80):
    scores_path = os.path.join(evidence_dir, "ml_eval_scores.csv")
    if not os.path.exists(scores_path):
        return {"skipped": True, "reason": "ml_eval_scores.csv not found"}

    df = pd.read_csv(scores_path)
    before_acc = float(accuracy_score(df["y_true"], (df["y_score"] >= 0.5).astype(int)))
    result = threshold_tune_groupwise(df["y_true"].values, df["y_score"].values, df["sensitive"].values,
                                      target_di=target_di)

    out = {"method": "group_threshold_tuning", "target_di": target_di,
           "before": {"acc": before_acc}, "after": result}
    _save_json(os.path.join(evidence_dir, "fairness_mitigation.json"), out)
    return out
