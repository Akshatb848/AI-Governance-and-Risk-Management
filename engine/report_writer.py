import os
import textwrap

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm


def write_audit_pack(reports_dir: str, run_id: str, timestamp: str, control_df, risk_df, redteam: dict | None = None) -> str:
    pdf_path = os.path.join(reports_dir, f"audit_pack_{run_id}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    def w(text, x, y, size=10):
        c.setFont("Helvetica", size)
        c.drawString(x, y, text)

    w("AEGIS: AI Governance & Risk Audit Pack", 2 * cm, height - 3 * cm, 16)
    w(f"Run ID: {run_id}", 2 * cm, height - 4 * cm, 11)
    w(f"Generated: {timestamp[:19].replace('T', ' ')} UTC", 2 * cm, height - 4.7 * cm, 11)

    total = len(control_df)
    p = int((control_df["status"] == "PASS").sum())
    f = int((control_df["status"] == "FAIL").sum())
    r = int((control_df["status"] == "REVIEW").sum())
    y = height - 6.4 * cm
    w("Executive Summary", 2 * cm, y, 13); y -= 0.8 * cm
    w(f"Controls: {total} | PASS: {p} | FAIL: {f} | REVIEW: {r}", 2 * cm, y, 11); y -= 0.7 * cm
    w(f"Risks raised: {len(risk_df)}", 2 * cm, y, 11); y -= 0.7 * cm
    if redteam:
        w(f"Red-team: blocked {redteam.get('attacks_blocked', 0)}/{redteam.get('attacks', 0)} attacks, "
          f"false refusals {redteam.get('false_refusals', 0)}", 2 * cm, y, 11)

    c.showPage()
    w("Control Results", 2 * cm, height - 2.5 * cm, 14)
    y = height - 3.6 * cm
    for _, row in control_df.iterrows():
        w(f"{row['control_id']} {row.get('control', '')} | {row['status']}", 2 * cm, y, 10); y -= 0.5 * cm
        for line in textwrap.wrap(str(row["notes"]), 110):
            w(f"  {line}", 2.2 * cm, y, 8); y -= 0.45 * cm
        y -= 0.25 * cm
        if y < 2.5 * cm:
            c.showPage()
            y = height - 3.6 * cm

    c.showPage()
    w("Risk Register", 2 * cm, height - 2.5 * cm, 14)
    y = height - 3.6 * cm
    if len(risk_df) == 0:
        w("No risks raised: all controls passed.", 2 * cm, y, 10)
    for _, row in risk_df.iterrows():
        w(f"[{row['level']}] {row['risk_id']} | {row['title']} | Score={int(row['score'])}", 2 * cm, y, 10)
        y -= 0.6 * cm
        for line in textwrap.wrap(f"Recommendation: {row['recommendation']}", 110):
            w(f"  {line}", 2.2 * cm, y, 8); y -= 0.45 * cm
        y -= 0.45 * cm
        if y < 3 * cm:
            c.showPage()
            y = height - 3.6 * cm

    c.save()
    return pdf_path
