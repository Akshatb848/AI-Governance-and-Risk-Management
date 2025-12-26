import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

def write_audit_pack(reports_dir: str, run_id: str, timestamp: str, control_df, risk_df):
    pdf_path = os.path.join(reports_dir, f"audit_pack_{run_id}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    def w(text, x, y, size=10):
        c.setFont("Helvetica", size)
        c.drawString(x, y, text)

    w("AEGIS – AI Governance & Risk Audit Pack", 2*cm, height-3*cm, 16)
    w(f"Run ID: {run_id}", 2*cm, height-4*cm, 11)
    w(f"Generated: {timestamp} (UTC)", 2*cm, height-4.7*cm, 11)

    total = len(control_df)
    p = int((control_df["status"]=="PASS").sum())
    f = int((control_df["status"]=="FAIL").sum())
    r = int((control_df["status"]=="REVIEW").sum())
    y = height-6.4*cm
    w("Executive Summary", 2*cm, y, 13); y -= 0.8*cm
    w(f"Controls: {total} | PASS: {p} | FAIL: {f} | REVIEW: {r}", 2*cm, y, 11)

    c.showPage()
    w("Risk Register (Top)", 2*cm, height-2.5*cm, 14)
    y = height-3.6*cm
    for _, row in risk_df.head(8).iterrows():
        w(f"- [{row['level']}] {row['risk_id']} | {row['title']} | Score={int(row['score'])}", 2*cm, y, 10)
        y -= 0.7*cm
        w(f"  Recommendation: {str(row['recommendation'])[:120]}", 2.2*cm, y, 9)
        y -= 0.9*cm
        if y < 3*cm:
            c.showPage()
            y = height-3.6*cm

    c.showPage()
    w("Control Results", 2*cm, height-2.5*cm, 14)
    y = height-3.6*cm
    for _, row in control_df.iterrows():
        w(f"{row['control_id']} | {row['status']} | {str(row['notes'])[:95]}", 2*cm, y, 9)
        y -= 0.55*cm
        if y < 2.5*cm:
            c.showPage()
            y = height-3.6*cm

    c.save()
    return pdf_path
