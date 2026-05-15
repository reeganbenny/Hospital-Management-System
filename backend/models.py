"""Database models for Hospital Management System."""
from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

ROLE_ADMIN = "admin"
ROLE_DOCTOR = "doctor"
ROLE_PATIENT = "patient"
STATUS_BOOKED = "Booked"
STATUS_COMPLETED = "Completed"
STATUS_CANCELLED = "Cancelled"


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.Index("ix_users_role", "role"),)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == ROLE_ADMIN

    @property
    def is_doctor(self):
        return self.role == ROLE_DOCTOR

    @property
    def is_patient(self):
        return self.role == ROLE_PATIENT

    def to_dict(self):
        return {"id": self.id, "username": self.username, "email": self.email, "role": self.role, "is_blacklisted": self.is_blacklisted}


class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    doctors = db.relationship("Doctor", backref="department", lazy="dynamic")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description or "", "doctors_count": self.doctors.count()}


class Doctor(db.Model):
    __tablename__ = "doctors"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(200))  # Degree (e.g. MBBS, MD)
    specialization = db.Column(db.String(100))  # Specialization (e.g. General Medicine, Cardiology)
    experience = db.Column(db.Integer)  # Years of experience
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    contact_number = db.Column(db.String(20))
    is_available = db.Column(db.Boolean, default=True)
    is_deleted = db.Column(db.Boolean, default=False)
    availability = db.Column(db.JSON, nullable=True)  # [{ "day_of_week": 1, "start_time": "09:00", "end_time": "12:00" }, ...]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("doctor", uselist=False, cascade="all, delete-orphan"))
    appointments = db.relationship("Appointment", backref="doctor", lazy="dynamic", cascade="all, delete-orphan")
    availability_slots = db.relationship("DoctorAvailability", backref="doctor", lazy="dynamic", cascade="all, delete-orphan")

    @classmethod
    def active_query(cls):
        """Return query excluding soft-deleted doctors (is_deleted=False)."""
        return cls.query.filter(cls.is_deleted == False)

    def to_dict(self):
        dept_name = self.department.name if self.department else ""
        spec = self.specialization or dept_name
        return {
            "id": self.id, "user_id": self.user_id, "name": self.name,
            "qualification": self.qualification or "",
            "specialization": spec,
            "experience": self.experience if self.experience is not None else 0,
            "department_id": self.department_id, "department_name": dept_name,
            "contact_number": self.contact_number or "", "is_available": self.is_available,
            "is_deleted": bool(self.is_deleted),
            "availability": self.availability,
        }


class Patient(db.Model):
    __tablename__ = "patients"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    contact_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    blood_group = db.Column(db.String(10))
    is_deleted = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("patient", uselist=False, cascade="all, delete-orphan"))
    appointments = db.relationship("Appointment", backref="patient", lazy="dynamic", cascade="all, delete-orphan")

    @classmethod
    def active_query(cls):
        """Return query excluding soft-deleted patients (is_deleted=False)."""
        return cls.query.filter(cls.is_deleted == False)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id, "name": self.name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "contact_number": self.contact_number or "", "address": self.address or "", "blood_group": self.blood_group or "",
            "is_deleted": bool(self.is_deleted), "is_blocked": bool(self.is_blocked),
        }


class DoctorAvailability(db.Model):
    __tablename__ = "doctor_availability"
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("doctor_id", "date", "start_time", name="uq_doctor_date_time"),)

    def to_dict(self):
        return {
            "id": self.id, "doctor_id": self.doctor_id,
            "date": self.date.isoformat() if self.date else None,
            "start_time": self.start_time.strftime("%H:%M") if self.start_time else None,
            "end_time": self.end_time.strftime("%H:%M") if self.end_time else None,
        }


class Appointment(db.Model):
    __tablename__ = "appointments"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default=STATUS_BOOKED)
    reason = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    treatment = db.relationship("Treatment", backref="appointment", uselist=False, cascade="all, delete-orphan")


    def to_dict(self):
        return {
            "id": self.id, "patient_id": self.patient_id, "doctor_id": self.doctor_id,
            "patient_name": self.patient.name if self.patient else "",
            "doctor_name": self.doctor.name if self.doctor else "",
            "specialization": self.doctor.specialization if self.doctor else "",
            "date": self.date.isoformat() if self.date else None,
            "time": self.time.strftime("%H:%M") if self.time else None,
            "status": self.status, "reason": self.reason or "",
            "treatment": self.treatment.to_dict() if self.treatment else None,
        }


class Treatment(db.Model):
    __tablename__ = "treatments"
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id"), nullable=False, unique=True)
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    next_visit_suggested = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "appointment_id": self.appointment_id, "diagnosis": self.diagnosis or "",
            "prescription": self.prescription or "", "notes": self.notes or "",
            "next_visit_suggested": self.next_visit_suggested.isoformat() if self.next_visit_suggested else None,
        }
