"""User-triggered CSV export of patient treatments."""
from datetime import datetime
from celery import shared_task
import os
import csv
import io
import re
import html as html_module


def _strip_html(text):
    """Return plain text with HTML tags and entities removed."""
    if not text:
        return ""
    s = re.sub(r"<[^>]+>", "", str(text))
    return html_module.unescape(s).strip()


@shared_task(bind=True, name="tasks.exports.export_patient_treatments_csv")
def export_patient_treatments_csv(self, patient_id):
    """Generate CSV of treatments for patient; store in static/exports and return path or content."""
    from extensions import db
    from models import Patient, Appointment, Treatment, STATUS_COMPLETED, STATUS_CANCELLED
    flask_app = getattr(self.app, "flask_app", None)
    if not flask_app:
        from app import create_app
        flask_app = create_app()
    with flask_app.app_context():
        patient = Patient.query.get(patient_id)
        if not patient:
            return {"error": "Patient not found"}
        appointments = (
            Appointment.query.filter_by(patient_id=patient_id)
             .filter(
                (Appointment.status == STATUS_COMPLETED) | (Appointment.treatment.has(Treatment.diagnosis.isnot(None)))
           )
           .order_by(Appointment.date.asc(), Appointment.time.asc())
           .all()
        )
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "user_id", "username", "consulting_doctor", "appointment_date", "diagnosis",
            "treatment", "next_visit_suggested"
        ])
        for a in appointments:
            row = [
                patient.user_id,
                patient.user.username if patient.user else "",
                a.doctor.name if a.doctor else "",
                a.date.isoformat() if a.date else "",
                "",
                "",
                "",
            ]
            if a.treatment:
                row[4] = _strip_html(a.treatment.diagnosis)
                row[5] = _strip_html(a.treatment.prescription)
                row[6] = (a.treatment.next_visit_suggested.isoformat() if a.treatment.next_visit_suggested else "")
            writer.writerow(row)
        csv_content = output.getvalue()
        # Save to file so frontend can download
        export_dir = os.path.join(flask_app.static_folder or "static", "exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = f"treatments_{patient_id}_{self.request.id}.csv"
        filepath = os.path.join(export_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            f.write(csv_content)
        # Return relative URL for download
        return {"filename": filename, "download_url": f"/static/exports/{filename}"}
