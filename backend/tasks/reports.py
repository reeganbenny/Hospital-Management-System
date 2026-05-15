"""Monthly doctor activity report: HTML report sent by email on 1st of month."""
from datetime import date
from calendar import monthrange
from celery import shared_task
from flask import current_app


@shared_task(bind=True, name="tasks.reports.send_monthly_doctor_reports")
def send_monthly_doctor_reports(self):
    """Run on 1st of month; for each doctor build HTML report and email."""
    from extensions import db
    from models import Doctor, Appointment, Treatment, STATUS_COMPLETED
    flask_app = getattr(self.app, "flask_app", None)
    if not flask_app:
        from app import create_app
        flask_app = create_app()
    with flask_app.app_context():
        # Previous month
        today = date.today()
        if today.month == 1:
            year = today.year - 1
            month = 12
        else:
            year = today.year
            month = today.month - 1
        start = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end = date(year, month, last_day)
        doctors = Doctor.query.all()
        for doctor in doctors:
            appointments = Appointment.query.filter_by(
                doctor_id=doctor.id,
                status=STATUS_COMPLETED,
            ).filter(Appointment.date >= start, Appointment.date <= end).order_by(
                Appointment.date.asc(), Appointment.time.asc()
            ).all()
            html = _build_report_html(doctor, appointments, year, month)
            if doctor.user and doctor.user.email and flask_app.config.get("MAIL_SERVER"):
                try:
                    _send_report_email(flask_app, doctor.user.email, f"Monthly Activity Report - {year}-{month:02d}", html)
                except Exception:
                    pass
        return {"doctors": len(doctors), "year": year, "month": month}


def _build_report_html(doctor, appointments, year, month):
    rows = []
    for a in appointments:
        tr = f"<tr><td>{a.date}</td><td>{a.time.strftime('%H:%M')}</td><td>{a.patient.name}</td>"
        if a.treatment:
            tr += f"<td>{a.treatment.diagnosis or '-'}</td><td>{a.treatment.prescription or '-'}</td><td>{a.treatment.notes or '-'}</td>"
        else:
            tr += "<td>-</td><td>-</td><td>-</td>"
        tr += "</tr>"
        rows.append(tr)
    table_rows = "\n".join(rows)
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Monthly Report</title></head>
<body>
<h1>Monthly Activity Report</h1>
<p><strong>Doctor:</strong> {doctor.name}</p>
<p><strong>Period:</strong> {year}-{month:02d}</p>
<p><strong>Total appointments completed:</strong> {len(appointments)}</p>
<table border="1" cellpadding="8" cellspacing="0">
<thead><tr><th>Date</th><th>Time</th><th>Patient</th><th>Diagnosis</th><th>Prescription</th><th>Notes</th></tr></thead>
<tbody>
{table_rows}
</tbody>
</table>
</body>
</html>
"""


def _send_report_email(app, to_email, subject, html_body):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = app.config.get("MAIL_DEFAULT_SENDER", "noreply@hospital.com")
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))
    use_tls = app.config.get("MAIL_USE_TLS", False)
    do_tls = use_tls in (True, "true", "True", "1")
    try:
        with smtplib.SMTP(app.config.get("MAIL_SERVER"), app.config.get("MAIL_PORT")) as s:
            if do_tls:
                s.starttls()
            if app.config.get("MAIL_USERNAME"):
                s.login(app.config["MAIL_USERNAME"], app.config.get("MAIL_PASSWORD", ""))
            s.send_message(msg)
    except Exception as e:
        print("--------------------------------Error sending report email:", e)
