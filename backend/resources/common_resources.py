"""Common API: departments list, search doctors, patient appointment booking."""
from datetime import date, datetime

from flask import current_app, request
from flask_restful import Resource, reqparse
from extensions import db
from models import Department, Doctor, Patient, Appointment, ROLE_ADMIN, ROLE_PATIENT, STATUS_BOOKED
from .decorators import patient_or_admin_required, patient_required, _get_current_user
from utils.availability import get_available_slots_for_patient, availability_slots_to_list
from utils.cache_decorators import cached

CACHE_KEY_DEPARTMENTS = "hms:departments:all"


@cached(CACHE_KEY_DEPARTMENTS, timeout=600)
def get_departments_list():
    """Return list of department dicts; result is cached."""
    departments = Department.query.order_by(Department.name).all()
    return [d.to_dict() for d in departments]


class DepartmentListResource(Resource):
    def get(self):
        data = get_departments_list()
        return data, 200


class DoctorSearchResource(Resource):
    @patient_or_admin_required
    def get(self):
        from .decorators import _get_current_user
        user = _get_current_user()
        parser = reqparse.RequestParser()
        parser.add_argument("q", type=str, location="args")
        parser.add_argument("specialization", type=str, location="args")
        parser.add_argument("department_id", type=int, location="args")
        args = parser.parse_args()
        q = (args.get("q") or "").strip()
        spec = (args.get("specialization") or "").strip()
        dept_id = args.get("department_id")
        query = Doctor.active_query()
        if user.role != ROLE_ADMIN:
            query = query.filter_by(is_available=True)
        if dept_id:
            query = query.filter_by(department_id=dept_id)
        if spec:
            query = query.join(Department).filter(Department.name.ilike(f"%{spec}%"))
        if q:
            query = query.filter(Doctor.name.ilike(f"%{q}%"))
        doctors = query.all()
        today = date.today()
        patient_id = user.patient.id if user.role == ROLE_PATIENT and user.patient else None
        out = []
        for d in doctors:
            doc_dict = d.to_dict()
            avail = get_available_slots_for_patient(d, today, 7, patient_id)
            doc_dict["availability_slots"] = availability_slots_to_list(avail)
            out.append(doc_dict)
        return out, 200


# class PatientAppointmentBookResource(Resource):
#     """POST /api/patient/appointments - patient books an appointment."""

#     @patient_required
#     def post(self):
#         user = _get_current_user()
#         patient = user.patient
#         data = request.get_json(force=True, silent=True) or {}
#         doctor_id = data.get("doctor_id")
#         date_str = data.get("date")
#         time_str = data.get("time")
#         reason = (data.get("reason") or "").strip() or None
#         if not doctor_id or not date_str or not time_str:
#             return {"message": "doctor_id, date, and time are required"}, 400
#         try:
#             apt_date = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
#         except ValueError:
#             return {"message": "Invalid date format (use YYYY-MM-DD)"}, 400
#         try:
#             parts = time_str.strip().split(":")
#             h, m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
#             apt_time = datetime.strptime(f"{h:02d}:{m:02d}", "%H:%M").time()
#         except (ValueError, IndexError):
#             return {"message": "Invalid time format (use HH:MM)"}, 400
#         doctor = Doctor.query.get(doctor_id)
#         if not doctor:
#             return {"message": "Doctor not found"}, 404
#         avail = get_available_slots_for_patient(doctor, apt_date, 1, patient.id)
#         slots_for_date = avail.get(apt_date.isoformat(), [])
#         time_ok = any(
#             (s.get("time") if isinstance(s, dict) else s) == time_str
#             for s in slots_for_date
#         )
#         if not time_ok:
#             return {"message": "Selected slot is not available"}, 400
#         apt = Appointment(
#             patient_id=patient.id,
#             doctor_id=doctor.id,
#             date=apt_date,
#             time=apt_time,
#             status=STATUS_BOOKED,
#             reason=reason,
#         )
#         db.session.add(apt)
#         db.session.commit()
#         return apt.to_dict(), 201
