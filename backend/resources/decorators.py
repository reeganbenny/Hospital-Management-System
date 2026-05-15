"""Role-based access decorators for API."""
from functools import wraps
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from models import User, ROLE_ADMIN, ROLE_DOCTOR, ROLE_PATIENT


def _get_current_user():
    verify_jwt_in_request()
    identity = get_jwt_identity()
    try:
        uid = int(identity)
        return User.query.get(uid)
    except (ValueError, TypeError):
        return None


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _get_current_user()
        if not user:
            return {"message": "Invalid token"}, 401
        if user.is_blacklisted:
            return {"message": "Account disabled"}, 403
        if user.role != ROLE_ADMIN:
            return {"message": "Admin access required"}, 403
        return fn(*args, **kwargs)
    return wrapper


def doctor_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _get_current_user()
        if not user:
            return {"message": "Invalid token"}, 401
        if user.is_blacklisted:
            return {"message": "Account disabled"}, 403
        if user.role != ROLE_DOCTOR:
            return {"message": "Doctor access required"}, 403
        if not user.doctor:
            return {"message": "Doctor profile not found"}, 403
        return fn(*args, **kwargs)
    return wrapper


def patient_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _get_current_user()
        if not user:
            return {"message": "Invalid token"}, 401
        if user.is_blacklisted:
            return {"message": "Account disabled"}, 403
        if user.role != ROLE_PATIENT:
            return {"message": "Patient access required"}, 403
        if not user.patient:
            return {"message": "Patient profile not found"}, 403
        return fn(*args, **kwargs)
    return wrapper


def patient_or_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _get_current_user()
        if not user:
            return {"message": "Invalid token"}, 401
        if user.is_blacklisted:
            return {"message": "Account disabled"}, 403
        if user.role not in (ROLE_PATIENT, ROLE_ADMIN):
            return {"message": "Access denied"}, 403
        return fn(*args, **kwargs)
    return wrapper
