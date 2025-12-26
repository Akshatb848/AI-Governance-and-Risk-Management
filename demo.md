# AEGIS – 5-Minute Demo Guide (Manager / Client Walkthrough)

This document explains **how to demo the AI Governance & Risk Management Platform (AEGIS)** to a non-technical stakeholder (manager, client, or partner) in **~5 minutes**.

---

## 1. Problem Statement (30 seconds)

> “Organizations are deploying Machine Learning and Generative AI systems, but governance is fragmented.  
> Technical metrics live in notebooks, while risk and compliance teams need **clear controls, risks, and audit evidence**.”

AEGIS solves this by:
- Running **automated AI audits**
- Translating results into **governance controls**
- Producing a **risk register and audit-ready reports**
- Maintaining a **traceable, auditable workflow**

---

## 2. What AEGIS Does (30 seconds)

AEGIS is an **end-to-end AI governance platform** that audits:

### Machine Learning Models
- Performance (accuracy, AUC)
- Fairness (disparate impact, group accuracy gaps)
- Explainability (SHAP)
- Operational risk (data drift)

### Generative AI / RAG Systems
- Prompt injection resistance
- Citation compliance
- Faithfulness to retrieved sources
- Policy-grounded responses

All results are **automatically converted into governance decisions**.

---

## 3. Live Demo Flow (3 minutes)

### Step 1: Open the Streamlit App
> “This is the governance dashboard.”

Explain:
- Each run is an **audit**
- Everything generated is saved as **evidence**

---

### Step 2: Run an Orchestrated Audit
Click:


Explain while it runs:
- Multiple **specialized agents** are executing:
  - ML Audit Agent
  - RAG Security Agent
  - Control Evaluation Agent
  - Risk Register Agent
  - Report Generation Agent

This is **multi-agent governance orchestration**, not a single script.

---

### Step 3: Show Control Results
Scroll to **Control Results** table.

Explain:
- Each row is a **governance control**
- Status meanings:
  - **PASS** → Meets policy thresholds
  - **FAIL** → Policy violation
  - **REVIEW** → Needs human oversight

Example explanation:
> “Here, fairness failed because the selection-rate ratio fell below the 0.80 threshold.”

---

### Step 4: Show Risk Register
Scroll to **Risk Register**.

Explain:
- Risks are derived automatically from failed/reviewed controls
- Each risk includes:
  - Domain (Fairness, Explainability, RAG Security)
  - Impact × Likelihood score
  - Overall risk level
  - Linked evidence files
  - Recommended remediation

> “This is what a risk or compliance team actually consumes.”

---

### Step 5: Show Evidence Artifacts
Point to **Evidence Files**.

Explain:
- All metrics are saved as structured artifacts
- Examples:
  - `fairness.json`
  - `drift.json`
  - `shap_global_importance.csv`
  - `rag_quality_metrics.json`

> “Nothing is hidden — everything is auditable.”

---

### Step 6: Show Audit Pack PDF
Download the **Audit Pack PDF**.

Explain:
- Executive-ready
- Can be shared with:
  - Internal governance teams
  - Auditors
  - Regulators

---

### Step 7: Show Workflow Trace (Optional but Powerful)
Open `workflow_trace.json`.

Explain:
- Each agent step is logged
- This provides:
  - Explainability
  - Accountability
  - Auditability

> “We can show exactly how a risk conclusion was reached.”

---

## 4. Automated Remediation (30 seconds)

If remediation was triggered:

Explain:
- AEGIS applies **automated mitigation**
- Re-runs the audit
- Generates a **Remediation Addendum PDF**

> “This enables closed-loop governance, not just detection.”

---

## 5. Why This Matters (30 seconds)

Summarize impact:

- Bridges **AI engineering** and **risk governance**
- Reduces manual review effort
- Creates defensible audit trails
- Scales across ML and GenAI systems
- Aligns with Responsible AI and Model Risk Management principles

---

## 6. How This Would Be Used in Practice

- **Pre-deployment AI reviews**
- **Periodic model risk assessments**
- **GenAI governance checks**
- **Internal audits**
- **Client or regulator walkthroughs**

---

## 7. Key Differentiator (Closing Line)

> “AEGIS doesn’t just measure AI models — it translates AI behavior into **governance decisions and business risk**.”

---

**End of Demo**

