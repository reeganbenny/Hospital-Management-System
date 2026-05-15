"""Daily reminder task: hospital space (webhook) + per-patient email (HTML)."""
from datetime import date
import requests
from celery import shared_task


@shared_task(bind=True, name="tasks.reminders.send_daily_reminders")
def send_daily_reminders(self):
    """Run daily; find appointments for today. Post to hospital Chat space + email each patient."""
    from extensions import db
    from models import Appointment, Patient, STATUS_BOOKED
    flask_app = getattr(self.app, "flask_app", None)
    if not flask_app:
        from app import create_app
        flask_app = create_app()
    with flask_app.app_context():
        today = date.today()
        appointments = Appointment.query.filter_by(
            date=today,
            status=STATUS_BOOKED,
        ).all()
        sent = 0
        webhook_url = flask_app.config.get("GOOGLE_CHAT_WEBHOOK_URL")

        for a in appointments:
            patient = Patient.query.get(a.patient_id)
            if not patient:
                continue

            # Hospital space (webhook): one message per appointment
            chat_msg = (
                f"Reminder: {patient.name} has an appointment today ({a.date}) "
                f"at {a.time.strftime('%H:%M')} with Dr. {a.doctor.name}."
            )
            if webhook_url:
                try:
                    requests.post(webhook_url, json={"text": chat_msg}, timeout=5)
                    sent += 1
                except Exception:
                    pass

            # Per-patient email (HTML)
            if flask_app.config.get("MAIL_SERVER") and patient.user and patient.user.email:
                try:
                    _send_reminder_email(
                        flask_app,
                        to_email=patient.user.email,
                        patient_name=patient.name,
                        appt_date=a.date,
                        appt_time=a.time,
                        doctor_name=a.doctor.name,
                    )
                    sent += 1
                except Exception:
                    pass

        return {"appointments": len(appointments), "reminders_sent": sent}


def _html_reminder_body(patient_name, appt_date, appt_time, doctor_name):
    """Modern HTML email body for appointment reminder."""
    time_str = appt_time.strftime("%I:%M %p") if hasattr(appt_time, "strftime") else str(appt_time)
    date_str = appt_date.isoformat() if hasattr(appt_date, "isoformat") else str(appt_date)
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Appointment Reminder</title>
</head>
<body style="margin:0; padding:0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f0f4f8;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f0f4f8; padding: 24px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 520px; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); overflow: hidden;">
          <tr>
            <td style="background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%); padding: 28px 32px; text-align: center;">
              <h1 style="margin:0; color: #ffffff; font-size: 20px; font-weight: 600; letter-spacing: 0.5px;">Appointment Reminder</h1>
              <p style="margin: 8px 0 0; color: rgba(255,255,255,0.9); font-size: 14px;">We look forward to seeing you</p>
            </td>
          </tr>
          <tr>
            <td style="padding: 32px;">
              <p style="margin: 0 0 16px; color: #1e293b; font-size: 16px;">Hello <strong>{patient_name}</strong>,</p>
              <p style="margin: 0 0 24px; color: #475569; font-size: 15px; line-height: 1.6;">This is a friendly reminder of your upcoming appointment.</p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                <tr>
                  <td style="padding: 20px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                      <tr>
                        <td style="color: #64748b; font-size: 13px; padding-bottom: 6px;">Date</td>
                        <td style="color: #1e293b; font-size: 15px; font-weight: 600; padding-bottom: 6px;">{date_str}</td>
                      </tr>
                      <tr>
                        <td style="color: #64748b; font-size: 13px; padding-bottom: 6px;">Time</td>
                        <td style="color: #1e293b; font-size: 15px; font-weight: 600; padding-bottom: 6px;">{time_str}</td>
                      </tr>
                      <tr>
                        <td style="color: #64748b; font-size: 13px;">Doctor</td>
                        <td style="color: #1e293b; font-size: 15px; font-weight: 600;">Dr. {doctor_name}</td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
              <p style="margin: 24px 0 0; color: #475569; font-size: 14px; line-height: 1.6;">Please arrive at the hospital at the scheduled time. If you need to reschedule or cancel, please contact us in advance.</p>
              <p style="margin: 16px 0 0; color: #1e293b; font-size: 14px;">Thank you,<br><strong>Hospital Team</strong></p>
            </td>
          </tr>
          <tr>
            <td style="padding: 16px 32px; background: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center;">
              <p style="margin: 0; color: #94a3b8; font-size: 12px;">This is an automated reminder. Please do not reply to this email.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _send_reminder_email(app, to_email, patient_name, appt_date, appt_time, doctor_name):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Appointment Reminder – See You Soon"
    msg["From"] = app.config.get("MAIL_DEFAULT_SENDER", "noreply@hospital.com")
    msg["To"] = to_email

    plain = (
        f"Hello {patient_name},\n\n"
        f"Reminder: You have an appointment on {appt_date} at {appt_time.strftime('%H:%M')} with Dr. {doctor_name}.\n\n"
        "Please visit the hospital at the scheduled time.\n\nThank you,\nHospital Team"
    )
    html = _html_reminder_body(patient_name, appt_date, appt_time, doctor_name)

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html.strip(), "html"))

    use_tls = app.config.get("MAIL_USE_TLS", False)
    do_tls = use_tls in (True, "true", "True", "1")

    with smtplib.SMTP(app.config.get("MAIL_SERVER"), app.config.get("MAIL_PORT")) as s:
        if do_tls:
            s.starttls()
        if app.config.get("MAIL_USERNAME"):
            s.login(app.config["MAIL_USERNAME"], app.config.get("MAIL_PASSWORD", ""))
        s.send_message(msg)