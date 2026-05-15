"""Patient API: dashboard, profile, book/cancel appointments, treatment history, CSV export."""
from datetime import date, datetime, timedelta
from flask import request, send_file
from flask_restful import Api, Resource, reqparse
from extensions import db
from sqlalchemy import or_
from models import (
    Department,
    Doctor,
    DoctorAvailability,
    Appointment,
    Treatment,
    Patient,
    STATUS_BOOKED,
    STATUS_COMPLETED,
    STATUS_CANCELLED,
)
from .decorators import patient_required, _get_current_user
from utils.availability import get_available_slots_for_patient
import io
import csv


class PatientDashboardResource(Resource):
    """GET /api/patient/dashboard - departments, doctor availability (7 days), upcoming & past appointments."""

    @patient_required
    def get(self):
        user = _get_current_user()
        patient = user.patient
        # Departments (cached via decorator in common_resources)
        from resources.common_resources import get_departments_list
        departments = get_departments_list()
        # Availability next 7 days: all doctors with their slots
        start = date.today()
        end = start + timedelta(days=7)
        slots = DoctorAvailability.query.filter(
            DoctorAvailability.date >= start,
            DoctorAvailability.date <= end,
        ).order_by(DoctorAvailability.date.asc(), DoctorAvailability.start_time.asc()).all()
        by_doctor = {}
        for s in slots:
            doc = Doctor.active_query().filter(Doctor.id == s.doctor_id).first()
            if not doc or not doc.is_available:
                continue
            if doc.id not in by_doctor:
                by_doctor[doc.id] = doc.to_dict()
                by_doctor[doc.id]["availability"] = []
            by_doctor[doc.id]["availability"].append(s.to_dict())
        doctor_availability = list(by_doctor.values())
        # My appointments
        upcoming = Appointment.query.filter(
            Appointment.patient_id == patient.id,
            Appointment.date >= date.today(),
            Appointment.status == STATUS_BOOKED,
        ).order_by(Appointment.date.asc(), Appointment.time.asc()).all()
        past = Appointment.query.filter(
            Appointment.patient_id == patient.id,
            or_(
                Appointment.date < date.today(),
                Appointment.status.in_([STATUS_COMPLETED, STATUS_CANCELLED]),
            ),
        ).order_by(Appointment.date.desc(), Appointment.time.desc()).limit(50).all()
        return {
            "departments": departments,
            "doctor_availability": doctor_availability,
            "upcoming_appointments": [a.to_dict() for a in upcoming],
            "past_appointments": [a.to_dict() for a in past],
        }, 200


class PatientProfileResource(Resource):
    """GET/PUT /api/patient/profile."""

    @patient_required
    def get(self):
        user = _get_current_user()
        return user.patient.to_dict(), 200

    @patient_required
    def put(self):
        user = _get_current_user()
        patient = user.patient
        data = request.get_json(force=True, silent=True) or {}
        if "name" in data:
            patient.name = (data["name"] or "").strip() or patient.name
        if "contact_number" in data:
            patient.contact_number = (data["contact_number"] or "").strip() or None
        if "address" in data:
            patient.address = (data["address"] or "").strip() or None
        if "blood_group" in data:
            patient.blood_group = (data["blood_group"] or "").strip() or None
        if "date_of_birth" in data:
            try:
                patient.date_of_birth = datetime.strptime(data["date_of_birth"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass
        db.session.commit()
        return patient.to_dict(), 200


class PatientAppointmentListResource(Resource):
    """GET /api/patient/appointments - my appointments."""

    @patient_required
    def get(self):
        user = _get_current_user()
        parser = reqparse.RequestParser()
        parser.add_argument("status", type=str, location="args")
        parser.add_argument("upcoming", type=int, location="args")
        args = parser.parse_args()
        query = Appointment.query.filter_by(patient_id=user.patient.id)
        if args.get("status"):
            query = query.filter_by(status=args["status"])
        if args.get("upcoming") == 1:
            query = query.filter(Appointment.date >= date.today(), Appointment.status == STATUS_BOOKED)
        query = query.order_by(Appointment.date.desc(), Appointment.time.desc())
        appointments = query.limit(100).all()
        return [a.to_dict() for a in appointments], 200


class PatientAppointmentBookResource(Resource):
    """POST /api/patient/appointments - book appointment. Validates date/time, past slots, doctor availability, and slot in schedule."""

    @patient_required
    def post(self):
        user = _get_current_user()
        if getattr(user.patient, "is_blocked", False):
            return {"message": "Account is blocked"}, 403
        data = request.get_json(force=True, silent=True) or {}
        doctor_id = data.get("doctor_id")
        appt_date = data.get("date")
        appt_time = data.get("time")
        reason = (data.get("reason") or "").strip() or None
        if not doctor_id or not appt_date or not appt_time:
            return {"message": "doctor_id, date, time required"}, 400
        try:
            d = datetime.strptime(appt_date.strip(), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return {"message": "date format YYYY-MM-DD, time format HH:MM"}, 400
        try:
            parts = appt_time.strip().split(":")
            h, m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
            t = datetime.strptime(f"{h:02d}:{m:02d}", "%H:%M").time()
            normalized_time_str = f"{h:02d}:{m:02d}"
        except (ValueError, TypeError, IndexError):
            return {"message": "date format YYYY-MM-DD, time format HH:MM"}, 400
        if d < date.today():
            return {"message": "Cannot book in the past"}, 400
        if d == date.today() and t <= datetime.now().time():
            return {"message": "Cannot book a slot that has already passed"}, 400
        doctor = Doctor.active_query().filter_by(id=doctor_id).first()
        if not doctor:
            return {"message": "Doctor not found"}, 404
        if not doctor.is_available:
            return {"message": "Doctor not available"}, 400
        patient_id = user.patient.id
        avail = get_available_slots_for_patient(doctor, d, 1, patient_id)
        slots_for_date = avail.get(d.isoformat(), [])
        time_ok = any(
            (s.get("time") if isinstance(s, dict) else s) == normalized_time_str
            and not s.get("booked_by_me", False)
            for s in slots_for_date
        )
        if not time_ok:
            return {"message": "Selected slot is not available"}, 400
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor.id,
            date=d,
            time=t,
            status=STATUS_BOOKED,
            reason=reason,
        )
        db.session.add(appointment)
        db.session.commit()
        return appointment.to_dict(), 201


class PatientAppointmentCancelResource(Resource):
    """POST /api/patient/appointments/<id>/cancel."""

    @patient_required
    def post(self, id):
        user = _get_current_user()
        appointment = Appointment.query.filter_by(id=id, patient_id=user.patient.id).first()
        if not appointment:
            return {"message": "Appointment not found"}, 404
        if appointment.status != STATUS_BOOKED:
            return {"message": "Appointment cannot be cancelled"}, 400
        appointment.status = STATUS_CANCELLED
        db.session.commit()
        return appointment.to_dict(), 200


class PatientAppointmentRescheduleResource(Resource):
    """POST /api/patient/appointments/<id>/reschedule - new date/time."""

    @patient_required
    def post(self, id):
        user = _get_current_user()
        appointment = Appointment.query.filter_by(id=id, patient_id=user.patient.id).first()
        if not appointment:
            return {"message": "Appointment not found"}, 404
        if appointment.status != STATUS_BOOKED:
            return {"message": "Only booked appointments can be rescheduled"}, 400
        data = request.get_json(force=True, silent=True) or {}
        appt_date = data.get("date")
        appt_time = data.get("time")
        if not appt_date or not appt_time:
            return {"message": "date and time required"}, 400
        try:
            d = datetime.strptime(appt_date, "%Y-%m-%d").date()
            t = datetime.strptime(appt_time, "%H:%M").time()
        except (ValueError, TypeError):
            return {"message": "date format YYYY-MM-DD, time format HH:MM"}, 400
        if d < date.today():
            return {"message": "Cannot reschedule to past"}, 400
        existing = Appointment.query.filter_by(
            doctor_id=appointment.doctor_id,
            date=d,
            time=t,
        ).filter(Appointment.status == STATUS_BOOKED, Appointment.id != id).first()
        if existing:
            return {"message": "Slot already booked"}, 409
        appointment.date = d
        appointment.time = t
        db.session.commit()
        return appointment.to_dict(), 200


class PatientTreatmentHistoryResource(Resource):
    """GET /api/patient/treatments - my treatment history (completed appointments with diagnosis/prescription)."""

    @patient_required
    def get(self):
        user = _get_current_user()
        appointments = Appointment.query.filter_by(
            patient_id=user.patient.id,
            status=STATUS_COMPLETED,
        ).order_by(Appointment.date.desc(), Appointment.time.desc()).all()
        out = []
        for a in appointments:
            d = a.to_dict()
            if a.treatment:
                d["treatment"] = a.treatment.to_dict()
            out.append(d)
        return out, 200


class PatientExportCSVTriggerResource(Resource):
    """POST /api/patient/export-csv - trigger async CSV export; returns task_id. Frontend polls or gets alert when done."""

    @patient_required
    def post(self):
        from flask import current_app
        user = _get_current_user()
        celery_app = current_app.extensions.get("celery")
        if not celery_app:
            return {"message": "Export service unavailable", "error": "Celery not configured"}, 503
        task = celery_app.send_task("tasks.exports.export_patient_treatments_csv", args=[user.patient.id])
        return {"task_id": task.id, "message": "Export started. You will be notified when ready."}, 202


class PatientExportCSVStatusResource(Resource):
    """GET /api/patient/export-csv/<task_id> - check status and get download info when ready."""

    @patient_required
    def get(self, task_id):
        from flask import current_app
        from celery.result import AsyncResult
        celery_app = current_app.extensions.get("celery")
        if not celery_app:
            return {"status": "unavailable", "error": "Celery not configured"}, 503
        result = AsyncResult(task_id, app=celery_app)
        if result.ready():
            if result.failed():
                return {"status": "failed", "error": str(result.result)}, 200
            res = result.result
            if isinstance(res, dict):
                return {"status": "completed", "result": res}, 200
            return {"status": "completed", "result": {"path": res}}, 200
        return {"status": "pending"}, 200


def register_patient_api(api):
    api.add_resource(PatientDashboardResource, "/dashboard")
    api.add_resource(PatientProfileResource, "/profile")
    api.add_resource(PatientAppointmentListResource, "/appointments")
    api.add_resource(PatientAppointmentBookResource, "/appointments")
    api.add_resource(PatientAppointmentCancelResource, "/appointments/<int:id>/cancel")
    api.add_resource(PatientAppointmentRescheduleResource, "/appointments/<int:id>/reschedule")
    api.add_resource(PatientTreatmentHistoryResource, "/treatments")
    api.add_resource(PatientExportCSVTriggerResource, "/export-csv")
    api.add_resource(PatientExportCSVStatusResource, "/export-csv/<task_id>")
