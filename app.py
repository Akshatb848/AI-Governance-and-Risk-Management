import os
import json

import pandas as pd
import streamlit as st

from engine.config import KB_DIR, DEFAULT_LLM_ID
from engine.orchestrator import run_aegis
from engine.run_store import list_runs, load_run

st.set_page_config(page_title="AEGIS: AI Governance & Risk", layout="wide")
st.title("AEGIS: AI Governance & Risk Platform")
st.caption("Audits an ML model and a RAG assistant with a LangGraph multi-agent workflow, "
           "then turns the evidence into controls, a risk register and an audit PDF.")


@st.cache_resource(show_spinner="Loading the local LLM (first run downloads the model)...")
def get_llm(model_id: str):
    from engine.llm import load_local_llm
    return load_local_llm(model_id)


with st.sidebar:
    st.header("Run settings")
    rebuild = st.checkbox("Rebuild vector DB (fresh indexing)", value=False)
    strict = st.checkbox("Strict citation enforcement", value=True)

    st.divider()
    st.header("Dataset (optional)")
    upload = st.file_uploader("CSV to audit (default: built-in demo dataset)", type=["csv"])
    target_col = sensitive_col = None
    dataset_path = None
    if upload is not None:
        df_up = pd.read_csv(upload)
        target_col = st.selectbox("Target column", df_up.columns)
        sensitive_col = st.selectbox("Sensitive attribute", [c for c in df_up.columns if c != target_col])
        os.makedirs("uploads", exist_ok=True)
        dataset_path = os.path.join("uploads", upload.name)
        df_up.to_csv(dataset_path, index=False)

    st.divider()
    st.header("Local LLM")
    llm_id = st.text_input("Hugging Face model id (open-weights)", value=DEFAULT_LLM_ID)
    st.caption("On a small GPU or CPU, try Qwen/Qwen2.5-0.5B-Instruct.")

    st.divider()
    st.caption(f"Policy knowledge base: `{os.path.relpath(KB_DIR)}`")

    run_btn = st.button("▶ Run Full Audit", use_container_width=True, type="primary")

    st.divider()
    st.header("Run history")
    runs = list_runs(limit=20)
    if runs:
        labels = [f"{r[0]}  ({r[2]})" for r in runs]
        pick = st.selectbox("Open a previous run", ["(current)"] + labels)
        if pick != "(current)":
            row = load_run(runs[labels.index(pick)][0])
            if row:
                row["logs"] = json.loads(row.pop("logs_json") or "[]")
                st.session_state["last_run"] = row
    else:
        st.caption("No runs yet.")

if run_btn:
    gen, mode = get_llm(llm_id)
    with st.spinner("Running the multi-agent workflow (ML audit, remediation, RAG red-team, controls, risks, PDF)..."):
        st.session_state["last_run"] = run_aegis(
            rebuild_vectordb=rebuild, strict_citations=strict, llm_id=llm_id, gen=gen, llm_mode=mode,
            dataset_csv_path=dataset_path, target_col=target_col, sensitive_col=sensitive_col)

res = st.session_state.get("last_run")
if not res:
    st.info("Click **Run Full Audit** to generate evidence, controls, a risk register and the PDF audit pack.")
    st.stop()

ev = res["evidence_dir"]
st.success(f"Run {res['run_id']} | LLM: {res.get('llm_id', '')} ({res.get('llm_mode', '')})")

cdf = pd.read_csv(os.path.join(ev, "control_results.csv"))
rdf = pd.read_csv(os.path.join(ev, "risk_register.csv"))
m1, m2, m3, m4 = st.columns(4)
m1.metric("PASS", int((cdf["status"] == "PASS").sum()))
m2.metric("FAIL", int((cdf["status"] == "FAIL").sum()))
m3.metric("REVIEW", int((cdf["status"] == "REVIEW").sum()))
m4.metric("Risks raised", len(rdf))

col1, col2 = st.columns(2)
with col1:
    st.subheader("Control results")
    st.dataframe(cdf, use_container_width=True, hide_index=True)
with col2:
    st.subheader("Risk register")
    st.dataframe(rdf, use_container_width=True, hide_index=True)

st.subheader("Red-team results (prompt injection and exfiltration)")
rt_path = os.path.join(ev, "redteam_results_llm.csv")
if os.path.exists(rt_path):
    st.dataframe(pd.read_csv(rt_path), use_container_width=True, hide_index=True)

st.subheader("Reports")
for label, path in [("Audit pack PDF", res.get("audit_pdf")), ("Remediation addendum PDF", res.get("remediation_pdf"))]:
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            st.download_button(f"Download {label}", data=f.read(), file_name=os.path.basename(path), mime="application/pdf")

with st.expander("Evidence artifacts"):
    st.code(ev)
    st.write(sorted(f for f in os.listdir(ev) if os.path.isfile(os.path.join(ev, f))))

with st.expander("Workflow trace (LangGraph nodes)"):
    st.json(res.get("logs", []))
