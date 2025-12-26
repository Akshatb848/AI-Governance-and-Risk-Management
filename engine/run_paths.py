import os
from .config import RUNS_DIR

def get_run_dirs(run_id: str):
    run_dir = os.path.join(RUNS_DIR, run_id)
    evidence_dir = os.path.join(run_dir, "evidence")
    reports_dir = os.path.join(run_dir, "reports")
    chroma_dir = os.path.join(run_dir, "chroma_policy")
    os.makedirs(evidence_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(chroma_dir, exist_ok=True)
    return run_dir, evidence_dir, reports_dir, chroma_dir
