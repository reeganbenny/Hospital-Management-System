"""Authentication: login and patient registration."""
from datetime import datetime
from flask import Blueprint, request
from flask_restful import Resource
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from extensions import db
from models import User, Patient, ROLE_DOCTOR, ROLE_PATIENT

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _get_user_by_identity(identity):
    try:
        uid = int(identity)
        return User.query.get(uid)
    except (ValueError, TypeError):
        return None


def register_jwt_handlers(jwt):
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return str(user.id) if user else None

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data.get("sub")
        return _get_user_by_identity(identity)


class LoginResource(Resource):
    def post(self):
        data = request.get_json(force=True, silent=True) or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return {"message": "Username and password required"}, 400

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            return {"message": "Invalid credentials"}, 401

        if user.is_blacklisted:
            return {"message": "Account is disabled"}, 403

        access_token = create_access_token(identity=user, additional_claims={"role": user.role})
        refresh_token = create_refresh_token(identity=user)
        role_payload = {"id": user.id, "username": user.username, "email": user.email, "role": user.role}

        if user.role == ROLE_DOCTOR and user.doctor:
            role_payload["doctor_id"] = user.doctor.id
            role_payload["name"] = user.doctor.name
        elif user.role == ROLE_PATIENT and user.patient:
            role_payload["patient_id"] = user.patient.id
            role_payload["name"] = user.patient.name

        return {"access_token": access_token, "refresh_token": refresh_token, "user": role_payload}, 200


class RegisterPatientResource(Resource):
    def post(self):
        data = request.get_json(force=True, silent=True) or {}
        username = (data.get("username") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        name = (data.get("name") or "").strip()
        if not username or not email or not password or not name:
            return {"message": "Username, email, password and name are required"}, 400

        if User.query.filter_by(username=username).first():
            return {"message": "Username already taken"}, 409

        if User.query.filter_by(email=email).first():
            return {"message": "Email already registered"}, 409
            
        user = User(username=username, email=email, role=ROLE_PATIENT)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        patient = Patient(user_id=user.id, name=name)
        patient.contact_number = data.get("contact_number", "").strip() or None
        patient.address = (data.get("address") or "").strip() or None
        dob_raw = data.get("date_of_birth")
        if dob_raw:
            try:
                patient.date_of_birth = datetime.strptime(dob_raw.strip(), "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass
        db.session.add(patient)
        db.session.commit()
        access_token = create_access_token(identity=user, additional_claims={"role": user.role})
        return {
            "access_token": access_token,
            "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role, "patient_id": patient.id, "name": patient.name},
        }, 201


class MeResource(Resource):
    @jwt_required()
    def get(self):
        user = _get_user_by_identity(get_jwt_identity())
        if not user:
            return {"message": "User not found"}, 404
        if user.is_blacklisted:
            return {"message": "Account disabled"}, 403
        out = user.to_dict()
        if user.role == ROLE_DOCTOR and user.doctor:
            out["doctor"] = user.doctor.to_dict()
        elif user.role == ROLE_PATIENT and user.patient:
            out["patient"] = user.patient.to_dict()
        return out, 200
