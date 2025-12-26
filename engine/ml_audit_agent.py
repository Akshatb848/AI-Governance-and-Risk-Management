import os, json
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from fairlearn.metrics import MetricFrame, selection_rate, true_positive_rate, false_positive_rate

import shap

def _save_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=str)

def _prep_dataset(df: pd.DataFrame, target_col: str, sensitive_col: str):
    assert target_col in df.columns, f"target_col '{target_col}' not in columns"
    assert sensitive_col in df.columns, f"sensitive_col '{sensitive_col}' not in columns"

    y_raw = df[target_col]
    X = df.drop(columns=[target_col]).copy()

    # map y to {0,1} if needed
    if y_raw.dtype == "O" or str(y_raw.dtype).startswith("category"):
        y = y_raw.astype("category").cat.codes
    else:
        y = y_raw.copy()

    # binary enforce if more than 2 classes -> pick most frequent as 0, rest 1 (simple baseline)
    uniq = pd.Series(y).dropna().unique()
    if len(uniq) > 2:
        # collapse to binary for MVP governance demo
        top = pd.Series(y).value_counts().index[0]
        y = (y != top).astype(int)

    y = pd.Series(y).fillna(0).astype(int)

    # sensitive to binary codes (0/1/...); if >2 groups we keep codes (fairlearn supports multi-group)
    s_raw = df[sensitive_col]
    if s_raw.dtype == "O" or str(s_raw.dtype).startswith("category"):
        s = s_raw.astype("category").cat.codes
    else:
        s = pd.Series(s_raw).fillna(0).astype(int)

    # ensure sensitive column exists in X too (it will, unless removed) - keep it by default for now
    return X, y, s

def run_ml_audit(evidence_dir: str, dataset_csv_path: str | None = None, target_col: str | None = None, sensitive_col: str | None = None):
    """
    Writes:
      - ml_metrics.json
      - fairness.json
      - drift.json
      - shap_global_importance.csv
      - ml_eval_scores.csv (y_true, y_score, sensitive)
    """
    os.makedirs(evidence_dir, exist_ok=True)

    # Load dataset
    if dataset_csv_path and target_col and sensitive_col:
        df = pd.read_csv(dataset_csv_path)
    else:
        # fallback demo dataset (small)
        from sklearn.datasets import load_breast_cancer
        data = load_breast_cancer(as_frame=True)
        df = data.frame
        target_col = "target"
        sensitive_col = "mean radius"  # will exist as feature, used as mock sensitive

    # if sensitive col is continuous -> binarize for DI style check
    if pd.api.types.is_numeric_dtype(df[sensitive_col]) and df[sensitive_col].nunique() > 10:
        df[sensitive_col] = (df[sensitive_col] > df[sensitive_col].median()).astype(int)

    X, y, s = _prep_dataset(df, target_col, sensitive_col)

    # Train/test
    X_train, X_test, y_train, y_test, s_train, s_test = train_test_split(
        X, y, s, test_size=0.25, random_state=42, stratify=y if y.nunique() > 1 else None
    )

    # Preprocess
    cat_cols = [c for c in X.columns if X[c].dtype == "O" or str(X[c].dtype).startswith("category")]
    num_cols = [c for c in X.columns if c not in cat_cols]

    num_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    pre = ColumnTransformer([
        ("num", num_pipe, num_cols),
        ("cat", cat_pipe, cat_cols)
    ], remainder="drop")

    clf = LogisticRegression(max_iter=4000)
    model = Pipeline([("pre", pre), ("clf", clf)])
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1] if len(np.unique(y_train)) > 1 else np.zeros(len(y_test))

    metrics = {
        "accuracy": float(accuracy_score(y_test, pred)),
        "auc": float(roc_auc_score(y_test, proba)) if len(np.unique(y_test)) > 1 else None,
        "n_test": int(len(y_test)),
        "target_col": target_col,
        "sensitive_col": sensitive_col
    }
    _save_json(os.path.join(evidence_dir, "ml_metrics.json"), metrics)

    # Save eval scores for remediation
    pd.DataFrame({
        "y_true": y_test.astype(int).values,
        "y_score": proba.astype(float),
        "sensitive": pd.Series(s_test).astype(int).values
    }).to_csv(os.path.join(evidence_dir, "ml_eval_scores.csv"), index=False)

    # Fairness metrics
    mf = MetricFrame(
        metrics={"accuracy": accuracy_score, "selection_rate": selection_rate, "tpr": true_positive_rate, "fpr": false_positive_rate},
        y_true=y_test, y_pred=pred, sensitive_features=s_test
    )
    by = mf.by_group

    # DI (min/max selection rate) across groups
    sr = by["selection_rate"]
    di = float(sr.min() / sr.max()) if float(sr.max()) > 0 else 0.0

    _save_json(os.path.join(evidence_dir, "fairness.json"), {
        "fairness_by_group": by.to_dict(),
        "disparate_impact_selection_rate": di
    })

    # Drift (simple: mean shift on numeric columns)
    drift_score = 0.0
    drift_top = {}
    if len(num_cols) > 0:
        train_means = X_train[num_cols].mean(numeric_only=True)
        test_means  = X_test[num_cols].mean(numeric_only=True)
        drift = (test_means - train_means).abs() / (train_means.abs() + 1e-6)
        top10 = drift.sort_values(ascending=False).head(min(10, len(drift)))
        drift_score = float(top10.mean()) if len(top10) else 0.0
        drift_top = top10.to_dict()

    _save_json(os.path.join(evidence_dir, "drift.json"), {
        "drift_score_mean_top10": drift_score,
        "top": drift_top
    })

    # SHAP (on transformed data)
    try:
        Xbg = X_train.sample(min(100, len(X_train)), random_state=42)
        Xex = X_test.sample(min(25, len(X_test)), random_state=42)

        Xt_bg = model.named_steps["pre"].fit_transform(Xbg)
        Xt_ex = model.named_steps["pre"].transform(Xex)

        explainer = shap.LinearExplainer(model.named_steps["clf"], Xt_bg, feature_perturbation="interventional")
        sv = explainer.shap_values(Xt_ex)
        mean_abs = np.mean(np.abs(sv), axis=0)

        # attempt to reconstruct feature names
        feat_names = []
        if len(num_cols):
            feat_names += num_cols
        if len(cat_cols):
            ohe = model.named_steps["pre"].named_transformers_["cat"].named_steps["onehot"]
            cat_names = ohe.get_feature_names_out(cat_cols).tolist()
            feat_names += cat_names

        # safety: align lengths
        n = min(len(mean_abs), len(feat_names))
        imp = pd.Series(mean_abs[:n], index=feat_names[:n]).sort_values(ascending=False)
        imp.to_csv(os.path.join(evidence_dir, "shap_global_importance.csv"))
    except Exception:
        # don't fail the whole run if SHAP breaks
        pd.Series({"shap_error": 1}).to_csv(os.path.join(evidence_dir, "shap_global_importance.csv"))

    return {"di": di, "drift_score": drift_score, "metrics": metrics}
