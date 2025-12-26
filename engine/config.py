import os

APP_ROOT = r"/content/aegis/aegis_streamlit_full"
DATA_DIR = os.path.join(APP_ROOT, "data")
KB_DIR = os.path.join(DATA_DIR, "kb")

OUTPUTS_DIR = os.path.join(APP_ROOT, "outputs")
RUNS_DIR = os.path.join(OUTPUTS_DIR, "runs")

DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_LLM_ID = "Qwen/Qwen2.5-1.5B-Instruct"  # open-weights (free)

def ensure_base_dirs():
    os.makedirs(KB_DIR, exist_ok=True)
    os.makedirs(RUNS_DIR, exist_ok=True)
