"""Flask application factory - API only (no frontend templates)."""
import os
from flask import Flask
from config import Config
from extensions import db, jwt, cors, cache
from models import (
    User,
    Department,
    Doctor,
    Patient,
    ROLE_ADMIN,
    ROLE_DOCTOR,
    ROLE_PATIENT,
)
from routes import register_routes


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="static")
    app.config.from_object(config_class)

    # Ensure instance directory exists and is writable (avoids SQLite "readonly database" errors)
    from config import _default_db_path
    _instance_dir = os.path.dirname(_default_db_path)
    os.makedirs(_instance_dir, exist_ok=True)
    try:
        os.chmod(_instance_dir, 0o755)
        if os.path.isfile(_default_db_path):
            os.chmod(_default_db_path, 0o664)
    except OSError:
        pass  # ignore if we can't chmod (e.g. permission or Windows)

    app.config["CACHE_TYPE"] = "RedisCache"
    app.config["CACHE_REDIS_URL"] = app.config.get("REDIS_URL", "redis://localhost:6379/0")
    app.config["CACHE_DEFAULT_TIMEOUT"] = getattr(config_class, "CACHE_DEFAULT_TIMEOUT", 300)
    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    register_routes(app)

    from celery_app import make_celery
    celery_app = make_celery(app)
    app.extensions["celery"] = celery_app

    with app.app_context():
        db.create_all()
        _migrate_add_doctor_availability()
        _migrate_add_doctor_specialization_experience()
        _seed_admin_and_departments()

    return app


def _migrate_add_doctor_availability():
    """Add availability column to doctors table if it does not exist (for existing DBs)."""
    from sqlalchemy import inspect, text
    import json
    inspector = inspect(db.engine)
    cols = [c["name"] for c in inspector.get_columns("doctors")]
    if "availability" not in cols:
        db.session.execute(text("ALTER TABLE doctors ADD COLUMN availability TEXT"))
        db.session.commit()
        default_avail = json.dumps([{"day_of_week": d, "start_time": "09:00", "end_time": "12:00"} for d in [1, 2, 3, 4, 5]])
        db.session.execute(text("UPDATE doctors SET availability = :avail WHERE availability IS NULL"), {"avail": default_avail})
        db.session.commit()


def _migrate_add_doctor_specialization_experience():
    """Add specialization and experience columns to doctors table if they do not exist."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    cols = [c["name"] for c in inspector.get_columns("doctors")]
    if "specialization" not in cols:
        db.session.execute(text("ALTER TABLE doctors ADD COLUMN specialization VARCHAR(100)"))
        db.session.commit()
        db.session.execute(text("""
            UPDATE doctors SET specialization = (
                SELECT name FROM departments WHERE departments.id = doctors.department_id
            ) WHERE specialization IS NULL
        """))
        db.session.commit()
    if "experience" not in cols:
        db.session.execute(text("ALTER TABLE doctors ADD COLUMN experience INTEGER"))
        db.session.commit()
        db.session.execute(text("UPDATE doctors SET experience = 0 WHERE experience IS NULL"))
        db.session.commit()


def _seed_admin_and_departments():
    if User.query.filter_by(role=ROLE_ADMIN).first():
        return
    admin = User(
        username=os.environ.get("ADMIN_USERNAME", "admin"),
        email=os.environ.get("ADMIN_EMAIL", "admin@hospital.com"),
        role=ROLE_ADMIN,
    )
    admin.set_password(os.environ.get("ADMIN_PASSWORD", "admin123"))
    db.session.add(admin)
    default_departments = [
        ("General Medicine", "General health and common ailments"),
        ("Cardiology", "Heart and cardiovascular system"),
        ("Orthopedics", "Bones, joints, and muscles"),
        ("Pediatrics", "Child health"),
        ("Dermatology", "Skin conditions"),
    ]
    for name, desc in default_departments:
        if not Department.query.filter_by(name=name).first():
            db.session.add(Department(name=name, description=desc))
    
    # Seed 1 demo doctor (department maps to specialization)
    if not User.query.filter_by(role=ROLE_DOCTOR).first():
        dept = Department.query.filter_by(name="General Medicine").first()
        if dept:
            doc_user = User(username="sarah@hospital.com", email="sarah@hospital.com", role=ROLE_DOCTOR)
            doc_user.set_password("doctor123")
            db.session.add(doc_user)
            db.session.flush()
            doctor = Doctor(
                user_id=doc_user.id,
                name="Dr. Sarah Mitchell",
                department_id=dept.id,
                qualification="MBBS, MD",
                specialization=dept.name,
                experience=12,
                contact_number="555-0101",
            )
            doctor.availability = [{"day_of_week": dow, "start_time": "09:00", "end_time": "12:00"} for dow in [1, 2, 3, 4, 5]]
            db.session.add(doctor)

    # Seed 1 demo patient
    if not User.query.filter_by(role=ROLE_PATIENT).first():
        from models import Patient
        pat_user = User(username="alice@email.com", email="alice@email.com", role=ROLE_PATIENT)
        pat_user.set_password("patient123")
        db.session.add(pat_user)
        db.session.flush()
        patient = Patient(
            user_id=pat_user.id,
            name="Alice Johnson",
            contact_number="555-1001",
        )
        db.session.add(patient)

    db.session.commit()
