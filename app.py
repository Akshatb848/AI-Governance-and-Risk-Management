import os, json
import pandas as pd
import streamlit as st

from engine.config import APP_ROOT, KB_DIR
from engine.orchestrator import run_aegis

st.set_page_config(page_title="AEGIS – Full Audit", layout="wide")
st.title("AEGIS – AI Governance & Risk Platform (Full End-to-End)")
st.caption("Runs ML + GenAI/RAG audits inside Streamlit using a LangGraph multi-agent workflow.")

with st.sidebar:
    st.header("Run Settings")
    rebuild = st.checkbox("Rebuild VectorDB (fresh indexing)", value=False)
    strict = st.checkbox("Strict citation enforcement", value=True)

    st.divider()
    st.header("Local LLM")
    llm_id = st.text_input("HF model id (open-weights)", value="Qwen/Qwen2.5-1.5B-Instruct")
    st.caption("Tip: if GPU is weak, try a smaller instruct model.")

    st.divider()
    st.header("Knowledge Base")
    st.write("KB folder:")
    st.code(KB_DIR)
    st.caption("Upload/replace .txt policy docs here for custom governance.")

    run_btn = st.button("▶ Run Full Audit", use_container_width=True)

@st.cache_resource
def _warmup():
    # Ensures Streamlit caches resources across reruns
    return True

_warmup()

if run_btn:
    with st.spinner("Running multi-agent workflow (ML + RAG + controls + risks + PDF)..."):
        result = run_aegis(rebuild_vectordb=rebuild, strict_citations=strict, llm_id=llm_id)
    st.session_state["last_run"] = result

res = st.session_state.get("last_run")
if not res:
    st.info("Click **Run Full Audit** to generate evidence, risk register, and the PDF audit pack.")
    st.stop()

st.success(f"Run complete: {res['run_id']} | LLM mode: {res.get('llm_mode','')}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Control Results")
    cpath = os.path.join(res["evidence_dir"], "control_results.csv")
    cdf = pd.read_csv(cpath)
    st.dataframe(cdf, use_container_width=True)
    st.download_button("Download control_results.csv", data=cdf.to_csv(index=False).encode("utf-8"),
                       file_name=f"control_results_{res['run_id']}.csv", mime="text/csv")

with col2:
    st.subheader("Risk Register")
    rpath = os.path.join(res["evidence_dir"], "risk_register.csv")
    rdf = pd.read_csv(rpath)
    st.dataframe(rdf, use_container_width=True)
    st.download_button("Download risk_register.csv", data=rdf.to_csv(index=False).encode("utf-8"),
                       file_name=f"risk_register_{res['run_id']}.csv", mime="text/csv")

st.subheader("Evidence Artifacts")
st.code(res["evidence_dir"])
ev_files = sorted([f for f in os.listdir(res["evidence_dir"]) if os.path.isfile(os.path.join(res["evidence_dir"], f))])
st.write(ev_files)

st.subheader("Audit Pack PDF")
pdf_path = res["audit_pdf"]
pdf_name = os.path.basename(pdf_path)
with open(pdf_path, "rb") as f:
    st.download_button(f"Download {pdf_name}", data=f.read(), file_name=pdf_name, mime="application/pdf")

st.subheader("Workflow Logs (multi-agent trace)")
st.json(res.get("logs", []))
