import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm


def write_remediation_addendum(reports_dir: str, run_id: str, timestamp: str, before_di: float, mitigation: dict) -> str:
    pdf_path = os.path.join(reports_dir, f"remediation_addendum_{run_id}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    def w(text, x, y, size=10):
        c.setFont("Helvetica", size)
        c.drawString(x, y, text)

    after = mitigation.get("after", {})
    thresholds = after.get("thresholds", {})

    w("AEGIS: Remediation Addendum", 2 * cm, height - 3 * cm, 16)
    w(f"Run ID: {run_id}", 2 * cm, height - 4 * cm, 11)
    w(f"Generated: {timestamp[:19].replace('T', ' ')} UTC", 2 * cm, height - 4.7 * cm, 11)

    y = height - 6.2 * cm
    w("1) Fairness remediation (F-01)", 2 * cm, y, 13); y -= 0.9 * cm
    w(f"- Method: {mitigation.get('method', '')}", 2 * cm, y, 10); y -= 0.6 * cm
    w(f"- Target DI: >= {mitigation.get('target_di', '')}", 2 * cm, y, 10); y -= 0.6 * cm
    w(f"- DI before: {before_di:.3f}", 2 * cm, y, 10); y -= 0.6 * cm
    w(f"- DI after: {after.get('di', 0):.3f}", 2 * cm, y, 10); y -= 0.6 * cm
    w(f"- Accuracy before: {mitigation.get('before', {}).get('acc', 0):.3f}", 2 * cm, y, 10); y -= 0.6 * cm
    w(f"- Accuracy after: {after.get('acc', 0):.3f}", 2 * cm, y, 10); y -= 0.6 * cm
    w(f"- Target met: {'yes' if after.get('target_met') else 'no (fairest achievable setting shown)'}", 2 * cm, y, 10); y -= 0.6 * cm
    for group, t in thresholds.items():
        w(f"- Decision threshold for group {group}: {t:.3f}", 2 * cm, y, 10); y -= 0.6 * cm

    y -= 0.4 * cm
    w("Thresholds were tuned on held-out scores; validate on fresh data before deployment.", 2 * cm, y, 9)

    c.save()
    return pdf_path
