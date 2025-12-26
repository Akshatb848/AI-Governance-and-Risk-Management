import os, json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

def write_remediation_addendum(reports_dir: str, run_id: str, timestamp: str, mitigation: dict):
    pdf_path = os.path.join(reports_dir, f"remediation_addendum_{run_id}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    def w(text, x, y, size=10):
        c.setFont("Helvetica", size)
        c.drawString(x, y, text)

    w("AEGIS – Remediation Addendum", 2*cm, height-3*cm, 16)
    w(f"Run ID: {run_id}", 2*cm, height-4*cm, 11)
    w(f"Generated: {timestamp} (UTC)", 2*cm, height-4.7*cm, 11)

    y = height-6.2*cm
    w("1) Fairness remediation", 2*cm, y, 13); y -= 0.9*cm
    w(f"- Method: {mitigation.get('method','')}", 2*cm, y, 10); y -= 0.6*cm
    after = mitigation.get("after", {})
    w(f"- Target DI: {mitigation.get('target_di','')}", 2*cm, y, 10); y -= 0.6*cm
    w(f"- After DI: {after.get('di','')}", 2*cm, y, 10); y -= 0.6*cm
    w(f"- After accuracy: {after.get('acc','')}", 2*cm, y, 10); y -= 0.6*cm
    w(f"- Thresholds: t0={after.get('t0','')} (group0), t1={after.get('t1','')} (group1)", 2*cm, y, 10)

    c.save()
    return pdf_path
