"""Route registration - centralizes all API endpoints."""
from flask_restful import Api

from resources.auth import bp as auth_bp
from resources.auth import (
    register_jwt_handlers,
    LoginResource,
    RegisterPatientResource,
    MeResource,
)
from resources.common_resources import (
    DepartmentListResource,
    DoctorSearchResource,
)
from resources.admin_resources import register_admin_api
from resources.doctor_resources import register_doctor_api
from resources.patient_resources import register_patient_api
from extensions import jwt


def register_routes(app):
    """Register all blueprints and API resources."""
    register_jwt_handlers(jwt)

    api_auth = Api(auth_bp)
    api_auth.add_resource(LoginResource, "/login")
    api_auth.add_resource(RegisterPatientResource, "/register")
    api_auth.add_resource(MeResource, "/me")
    app.register_blueprint(auth_bp)

    api_common = Api(app, prefix="/api")
    api_common.add_resource(DepartmentListResource, "/departments")
    api_common.add_resource(DoctorSearchResource, "/doctors/search")

    api_admin = Api(app, prefix="/api/admin")
    api_doctor = Api(app, prefix="/api/doctor")
    api_patient = Api(app, prefix="/api/patient")
    register_admin_api(api_admin)
    register_doctor_api(api_doctor)
    register_patient_api(api_patient)
