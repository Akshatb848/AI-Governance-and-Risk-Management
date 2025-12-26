import os, sqlite3, json
from .config import OUTPUTS_DIR

DB_PATH = os.path.join(OUTPUTS_DIR, "runs.db")

def init_db():
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        timestamp TEXT,
        llm_id TEXT,
        llm_mode TEXT,
        evidence_dir TEXT,
        reports_dir TEXT,
        control_csv TEXT,
        risk_csv TEXT,
        audit_pdf TEXT,
        remediation_pdf TEXT,
        logs_json TEXT
    )
    """)
    con.commit()
    con.close()

def upsert_run(meta: dict):
    init_db()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        meta.get("run_id"),
        meta.get("timestamp"),
        meta.get("llm_id",""),
        meta.get("llm_mode",""),
        meta.get("evidence_dir",""),
        meta.get("reports_dir",""),
        meta.get("control_csv",""),
        meta.get("risk_csv",""),
        meta.get("audit_pdf",""),
        meta.get("remediation_pdf",""),
        json.dumps(meta.get("logs", []))
    ))
    con.commit()
    con.close()

def list_runs(limit=20):
    init_db()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT run_id, timestamp, llm_mode FROM runs ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    con.close()
    return rows

def load_run(run_id: str):
    init_db()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT * FROM runs WHERE run_id=?", (run_id,))
    row = cur.fetchone()
    cols = [d[0] for d in cur.description]
    con.close()
    if not row:
        return None
    return dict(zip(cols, row))
