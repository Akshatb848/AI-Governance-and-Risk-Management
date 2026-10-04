import os
from pathlib import Path

# Everything lives under the repository root by default, so a fresh clone runs
# anywhere. Set AEGIS_HOME to keep data and outputs somewhere else.
APP_ROOT = os.environ.get("AEGIS_HOME", str(Path(__file__).resolve().parents[1]))
DATA_DIR = os.path.join(APP_ROOT, "data")
KB_DIR = os.path.join(DATA_DIR, "kb")

OUTPUTS_DIR = os.path.join(APP_ROOT, "outputs")
RUNS_DIR = os.path.join(OUTPUTS_DIR, "runs")

DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# Open-weights instruct model from Hugging Face; override with AEGIS_LLM_ID.
DEFAULT_LLM_ID = os.environ.get("AEGIS_LLM_ID", "Qwen/Qwen2.5-1.5B-Instruct")

# Governance thresholds (mirrors data/kb/02_aegis_policy_model_risk.txt)
FAIRNESS_DI_MIN = 0.80
DRIFT_SCORE_MAX = 0.35
CITATION_COVERAGE_MIN = 0.70
FAITHFULNESS_MIN = 0.12


def ensure_base_dirs():
    os.makedirs(KB_DIR, exist_ok=True)
    os.makedirs(RUNS_DIR, exist_ok=True)
