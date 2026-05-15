"""Admin API: dashboard, doctors CRUD, appointments, search, blacklist."""
from datetime import date
from flask import request
from flask_restful import Resource, reqparse
from extensions import db
from sqlalchemy import or_
from models import User, Department, Doctor, Patient, Appointment, STATUS_BOOKED
from .decorators import admin_required
from utils.availability import get_slots_with_status


def invalidate_departments_cache():
    from flask import current_app
    from resources.common_resources import CACHE_KEY_DEPARTMENTS
    c = getattr(current_app, "cache", None)
    if c:
        c.delete(CACHE_KEY_DEPARTMENTS)


class AdminDashboardResource(Resource):
    @admin_required
    def get(self):
        doctors_count = Doctor.active_query().count()
        patients_count = Patient.active_query().count()
        appointments_count = Appointment.query.count()
        upcoming = Appointment.query.filter(Appointment.date >= date.today(), Appointment.status == STATUS_BOOKED).count()
        return {"doctors_count": doctors_count, "patients_count": patients_count, "appointments_count": appointments_count, "upcoming_appointments": upcoming}, 200


class DoctorListCreateResource(Resource):
    @admin_required
    def get(self):
        doctors = Doctor.active_query().all()
        return [d.to_dict() for d in doctors], 200

    @admin_required
    def post(self):
        data = request.get_json(force=True, silent=True) or {}
        username = (data.get("username") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or "doctor123"
        name = (data.get("name") or "").strip()
        department_id = data.get("department_id")
        qualification = (data.get("qualification") or "").strip() or None
        specialization = (data.get("specialization") or "").strip() or None
        experience = data.get("experience")
        contact_number = (data.get("contact_number") or "").strip() or None
        if not username or not email or not name or not department_id:
            return {"message": "username, email, name, department_id required"}, 400
        if User.query.filter_by(username=username).first():
            return {"message": "Username already taken"}, 409
        if User.query.filter_by(email=email).first():
            return {"message": "Email already registered"}, 409
        dept = Department.query.get(department_id)
        if not dept:
            return {"message": "Invalid department_id"}, 400
        spec = specialization if specialization else dept.name
        exp = int(experience) if experience is not None and experience != "" else 0
        from models import ROLE_DOCTOR
        user = User(username=username, email=email, role=ROLE_DOCTOR)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        doctor = Doctor(
            user_id=user.id, name=name, department_id=department_id,
            qualification=qualification, specialization=spec, experience=exp,
            contact_number=contact_number,
        )
        default_avail = [{"day_of_week": dow, "start_time": "09:00", "end_time": "12:00"} for dow in [1, 2, 3, 4, 5]]
        doctor.availability = default_avail
        db.session.add(doctor)
        db.session.commit()
        return doctor.to_dict(), 201


class DoctorDetailResource(Resource):
    """GET /api/admin/doctors/<id> - doctor details for admin."""
    @admin_required
    def get(self, id):
        doctor = Doctor.query.get(id)
        if not doctor:
            return {"message": "Doctor not found"}, 404
        return doctor.to_dict(), 200

    @admin_required
    def put(self, id):
        doctor = Doctor.query.get(id)
        if not doctor:
            return {"message": "Doctor not found"}, 404
        data = request.get_json(force=True, silent=True) or {}
        if "name" in data:
            doctor.name = (data["name"] or "").strip() or doctor.name
        if "department_id" in data:
            dept = Department.query.get(data["department_id"])
            if dept:
                doctor.department_id = data["department_id"]
        if "qualification" in data:
            doctor.qualification = (data["qualification"] or "").strip() or None
        if "specialization" in data:
            doctor.specialization = (data["specialization"] or "").strip() or None
        if "experience" in data:
            v = data["experience"]
            doctor.experience = int(v) if v is not None and v != "" else 0
        if "contact_number" in data:
            doctor.contact_number = (data["contact_number"] or "").strip() or None
        if "is_available" in data:
            doctor.is_available = bool(data["is_available"])
        db.session.commit()
        invalidate_departments_cache()
        return doctor.to_dict(), 200

    @admin_required
    def delete(self, id):
        doctor = Doctor.query.get(id)
        if not doctor:
            return {"message": "Doctor not found"}, 404
        user = doctor.user
        if user:
            db.session.delete(user)  # cascades to doctor -> appointments, availability_slots, treatments
        else:
            db.session.delete(doctor)
        db.session.commit()
        invalidate_departments_cache()
        return {"message": "Doctor removed"}, 200


class AdminDoctorAvailabilityResource(Resource):
    """GET /api/admin/doctors/<id>/availability - slot status for admin (detailed)."""

    @admin_required
    def get(self, id):
        doctor = Doctor.query.get(id)
        if not doctor:
            return {"message": "Doctor not found"}, 404
        today = date.today()
        slots_with_status = get_slots_with_status(doctor, today, 7)
        return {"slots_by_date": slots_with_status}, 200


class DoctorBlockResource(Resource):
    """POST /api/admin/doctors/<id>/block - block doctor/ unblock doctor: is_available=False, user.is_blacklisted=True."""

    @admin_required
    def post(self, id):
        doctor = Doctor.query.get(id)
        if not doctor:
            return {"message": "Doctor not found"}, 404
        doctor.is_available = not doctor.is_available
        if doctor.user:
            doctor.user.is_blacklisted = not doctor.user.is_blacklisted
        db.session.commit()
        invalidate_departments_cache()
        return {"message": "Doctor blocked", "doctor": doctor.to_dict()}, 200


class AppointmentListResource(Resource):
    @admin_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("status", type=str, location="args")
        parser.add_argument("upcoming", type=int, location="args")
        args = parser.parse_args()
        query = Appointment.query
        if args.get("status"):
            query = query.filter_by(status=args["status"])
        if args.get("upcoming") == 1:
            query = query.filter(Appointment.date >= date.today(), Appointment.status == STATUS_BOOKED)
        query = query.order_by(Appointment.date.desc(), Appointment.time.desc())
        appointments = query.limit(500).all()
        return [a.to_dict() for a in appointments], 200


class PatientSearchResource(Resource):
    @admin_required
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument("q", type=str, location="args", required=True)
        args = parser.parse_args()
        q = (args.get("q") or "").strip()
        if not q:
            return [], 200
        try:
            pid = int(q)
            patients = Patient.active_query().filter(Patient.id == pid).all()
        except ValueError:
            patients = Patient.active_query().filter(or_(Patient.name.ilike(f"%{q}%"), Patient.contact_number.ilike(f"%{q}%"))).all()
        out = []
        for p in patients:
            d = p.to_dict()
            d["username"] = p.user.username if p.user else ""
            d["email"] = p.user.email if p.user else ""
            out.append(d)
        return out, 200


class PatientListResource(Resource):
    @admin_required
    def get(self):
        patients = Patient.active_query().all()
        return [{**p.to_dict(), "username": p.user.username if p.user else "", "email": p.user.email if p.user else ""} for p in patients], 200


class PatientDetailResource(Resource):
    """GET /api/admin/patients/<id> - patient details for admin."""
    @admin_required
    def get(self, id):
        patient = Patient.query.get(id)
        if not patient:
            return {"message": "Patient not found"}, 404
        d = patient.to_dict()
        d["username"] = patient.user.username if patient.user else ""
        d["email"] = patient.user.email if patient.user else ""
        return d, 200

    @admin_required
    def put(self, id):
        patient = Patient.query.get(id)
        if not patient:
            return {"message": "Patient not found"}, 404
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
            patient.date_of_birth = data["date_of_birth"]
        db.session.commit()
        return patient.to_dict(), 200

    @admin_required
    def delete(self, id):
        patient = Patient.query.get(id)
        if not patient:
            return {"message": "Patient not found"}, 404
        user = patient.user
        if user:
            db.session.delete(user)  # cascades to patient -> appointments -> treatments
        else:
            db.session.delete(patient)
        db.session.commit()
        return {"message": "Patient removed"}, 200


class PatientBlockResource(Resource):
    """POST /api/admin/patients/<id>/block - block patient/ unblock Patient: is_blocked=True, user.is_blacklisted=True."""

    @admin_required
    def post(self, id):
        patient = Patient.query.get(id)
        if not patient:
            return {"message": "Patient not found"}, 404
        patient.is_blocked = not patient.is_blocked
        if patient.user:
            patient.user.is_blacklisted = not patient.user.is_blacklisted
        db.session.commit()
        return {"message": "Patient blocked", "patient": patient.to_dict()}, 200


class DepartmentListCreateResource(Resource):
    @admin_required
    def get(self):
        depts = Department.query.order_by(Department.name).all()
        return [d.to_dict() for d in depts], 200

    @admin_required
    def post(self):
        data = request.get_json(force=True, silent=True) or {}
        name = (data.get("name") or "").strip()
        description = (data.get("description") or "").strip() or None
        if not name:
            return {"message": "name required"}, 400
        if Department.query.filter_by(name=name).first():
            return {"message": "Department already exists"}, 409
        dept = Department(name=name, description=description)
        db.session.add(dept)
        db.session.commit()
        invalidate_departments_cache()
        return dept.to_dict(), 201


def register_admin_api(api):
    api.add_resource(AdminDashboardResource, "/dashboard")
    api.add_resource(DoctorListCreateResource, "/doctors")
    api.add_resource(AdminDoctorAvailabilityResource, "/doctors/<int:id>/availability")
    api.add_resource(DoctorBlockResource, "/doctors/<int:id>/block")
    api.add_resource(DoctorDetailResource, "/doctors/<int:id>")
    api.add_resource(AppointmentListResource, "/appointments")
    api.add_resource(PatientSearchResource, "/patients/search")
    api.add_resource(PatientListResource, "/patients")
    api.add_resource(PatientBlockResource, "/patients/<int:id>/block")
    api.add_resource(PatientDetailResource, "/patients/<int:id>")
    api.add_resource(DepartmentListCreateResource, "/departments")
