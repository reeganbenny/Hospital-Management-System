"""Doctor API: recurring availability, availability slots, appointment detail, complete, cancel, patient history."""
from datetime import date, time, timedelta, datetime
from flask import request
from flask_restful import Resource, reqparse
from extensions import db
from models import (
    Doctor,
    DoctorAvailability,
    Appointment,
    Treatment,
    Patient,
    STATUS_BOOKED,
    STATUS_COMPLETED,
    STATUS_CANCELLED,
)
from .decorators import doctor_required, _get_current_user
from utils.availability import (
    day_of_week_user,
    get_merged_slots_for_doctor,
    get_slots_with_status,
)


class RecurringAvailabilityResource(Resource):
    """GET/PUT /api/doctor/recurring - Doctor.availability JSON."""

    @doctor_required
    def get(self):
        user = _get_current_user()
        doctor = user.doctor
        return {"availability": doctor.availability or []}, 200

    @doctor_required
    def put(self):
        user = _get_current_user()
        doctor = user.doctor
        data = request.get_json(force=True, silent=True) or {}
        availability = data.get("availability")
        if availability is None:
            return {"message": "availability required"}, 400
        if not isinstance(availability, list):
            return {"message": "availability must be a list"}, 400
        doctor.availability = availability
        db.session.commit()
        return {"availability": doctor.availability}, 200


class AvailabilityResource(Resource):
    """GET/POST /api/doctor/availability - merged slots for next 7 days, upsert slots."""

    @doctor_required
    def get(self):
        user = _get_current_user()
        doctor = user.doctor
        today = date.today()
        detailed = request.args.get("detailed") == "1"
        if detailed:
            slots_with_status = get_slots_with_status(doctor, today, 7)
            return {"slots_by_date": slots_with_status}, 200
        merged = get_merged_slots_for_doctor(doctor, today, 7)
        return merged, 200

    @doctor_required
    def post(self):
        user = _get_current_user()
        doctor = user.doctor
        data = request.get_json(force=True, silent=True) or {}
        slots = data.get("slots", [])
        apply_recurring = data.get("applyRecurring") or {}

        if not isinstance(slots, list):
            return {"message": "slots must be a list"}, 400

        recurring = list(doctor.availability or [])
        recurring_by_dow = {}
        for r in recurring:
            dow = r.get("day_of_week")
            if dow not in recurring_by_dow:
                recurring_by_dow[dow] = []
            recurring_by_dow[dow].append(dict(r))

        slots_by_date = {}
        for s in slots:
            date_str = s.get("date")
            start_t = s.get("start_time") or s.get("start")
            if not date_str or not start_t:
                continue
            if date_str not in slots_by_date:
                slots_by_date[date_str] = []
            slots_by_date[date_str].append(start_t)

        for date_str, times in slots_by_date.items():
            try:
                d = date.fromisoformat(date_str)
            except ValueError:
                continue
            dow = day_of_week_user(d)
            if apply_recurring.get(date_str):
                times_sorted = sorted(set(times))
                ranges = []
                i = 0
                while i < len(times_sorted):
                    t0 = times_sorted[i]
                    j = i
                    while j + 1 < len(times_sorted):
                        th, tm = map(int, times_sorted[j].split(":"))
                        th2, tm2 = map(int, times_sorted[j + 1].split(":"))
                        if (th2 * 60 + tm2) - (th * 60 + tm) == 30:
                            j += 1
                        else:
                            break
                    t1 = times_sorted[j]
                    eh, em = map(int, t1.split(":"))
                    em += 30
                    if em >= 60:
                        eh += 1
                        em -= 60
                    end_str = f"{eh:02d}:{em:02d}"
                    ranges.append({"day_of_week": dow, "start_time": t0, "end_time": end_str})
                    i = j + 1
                recurring_by_dow[dow] = ranges

        today = date.today()
        end_date = today + timedelta(days=6)
        DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.date >= today,
            DoctorAvailability.date <= end_date,
        ).delete()

        for s in slots:
            date_str = s.get("date")
            if apply_recurring.get(date_str):
                continue
            start_t = s.get("start_time") or s.get("start")
            if not date_str or not start_t:
                continue
            try:
                d = date.fromisoformat(date_str)
            except ValueError:
                continue
            end_t = s.get("end_time") or s.get("end")
            if not end_t:
                try:
                    sh, sm = map(int, str(start_t).split(":")[:2])
                    sm += 30
                    if sm >= 60:
                        sh += 1
                        sm -= 60
                    end_t = f"{sh:02d}:{sm:02d}"
                except (ValueError, AttributeError, IndexError):
                    end_t = start_t
            try:
                st_time = time(int(start_t.split(":")[0]), int(start_t.split(":")[1]))
                et_time = time(int(end_t.split(":")[0]), int(end_t.split(":")[1]))
            except (ValueError, IndexError):
                continue
            row = DoctorAvailability(doctor_id=doctor.id, date=d, start_time=st_time, end_time=et_time)
            db.session.add(row)

        if apply_recurring:
            new_list = []
            for dow in range(7):
                new_list.extend(recurring_by_dow.get(dow, []))
            doctor.availability = new_list

        db.session.commit()
        merged = get_merged_slots_for_doctor(doctor, date.today(), 7)
        return merged, 200


class DoctorAppointmentListResource(Resource):
    """GET /api/doctor/appointments - my appointments."""

    @doctor_required
    def get(self):
        user = _get_current_user()
        parser = reqparse.RequestParser()
        parser.add_argument("status", type=str, location="args")
        parser.add_argument("date", type=str, location="args")
        parser.add_argument("upcoming", type=int, location="args")
        args = parser.parse_args()
        query = Appointment.query.filter_by(doctor_id=user.doctor.id)
        if args.get("status"):
            query = query.filter_by(status=args["status"])
        if args.get("date"):
            try:
                d = datetime.strptime(args["date"], "%Y-%m-%d").date()
                query = query.filter(Appointment.date == d)
            except ValueError:
                pass
        if args.get("upcoming") == 1:
            query = query.filter(Appointment.date >= date.today(), Appointment.status == STATUS_BOOKED)
        query = query.order_by(Appointment.date.desc(), Appointment.time.desc())
        appointments = query.limit(200).all()
        return [a.to_dict() for a in appointments], 200


class DoctorAppointmentDetailResource(Resource):
    """GET /api/doctor/appointments/<id> - single appointment (doctor's own) with patient blood_group."""

    @doctor_required
    def get(self, id):
        user = _get_current_user()
        appointment = Appointment.query.filter_by(id=id, doctor_id=user.doctor.id).first()
        if not appointment:
            return {"message": "Appointment not found"}, 404
        out = appointment.to_dict()
        if appointment.patient:
            out["patient_blood_group"] = appointment.patient.blood_group or ""
        else:
            out["patient_blood_group"] = ""
        return out, 200


class DoctorAppointmentCompleteResource(Resource):
    """POST /api/doctor/appointments/<id>/complete - add diagnosis/prescription and mark completed."""

    @doctor_required
    def post(self, id):
        user = _get_current_user()
        appointment = Appointment.query.filter_by(id=id, doctor_id=user.doctor.id).first()
        if not appointment:
            return {"message": "Appointment not found"}, 404
        if appointment.status != STATUS_BOOKED:
            return {"message": "Only booked appointments can be completed"}, 400
        data = request.get_json(force=True, silent=True) or {}
        diagnosis = (data.get("diagnosis") or "").strip() or None
        prescription = (data.get("prescription") or "").strip() or None
        if appointment.treatment:
            appointment.treatment.diagnosis = diagnosis
            appointment.treatment.prescription = prescription
        else:
            treatment = Treatment(
                appointment_id=appointment.id,
                diagnosis=diagnosis,
                prescription=prescription,
            )
            db.session.add(treatment)
        appointment.status = STATUS_COMPLETED
        db.session.commit()
        db.session.refresh(appointment)
        return appointment.to_dict(), 200


class DoctorAppointmentCancelResource(Resource):
    """POST /api/doctor/appointments/<id>/cancel - cancel appointment."""

    @doctor_required
    def post(self, id):
        user = _get_current_user()
        appointment = Appointment.query.filter_by(id=id, doctor_id=user.doctor.id).first()
        if not appointment:
            return {"message": "Appointment not found"}, 404
        if appointment.status != STATUS_BOOKED:
            return {"message": "Only booked appointments can be cancelled"}, 400
        appointment.status = STATUS_CANCELLED
        db.session.commit()
        return appointment.to_dict(), 200


class DoctorPatientListResource(Resource):
    """GET /api/doctor/patients - all patients who have scheduled an appointment with the current doctor."""

    @doctor_required
    def get(self):
        user = _get_current_user()
        doctor_id = user.doctor.id
        patient_ids = (
            db.session.query(Appointment.patient_id)
            .filter(Appointment.doctor_id == doctor_id)
            .distinct()
            .all()
        )
        patient_ids = [p[0] for p in patient_ids]
        if not patient_ids:
            return [], 200
        patients = Patient.active_query().filter(Patient.id.in_(patient_ids)).order_by(Patient.name).all()
        return [p.to_dict() for p in patients], 200


class DoctorPatientHistoryResource(Resource):
    """GET /api/doctor/patients/<patient_id>/history - completed appointments with treatment for this patient."""

    @doctor_required
    def get(self, patient_id):
        user = _get_current_user()
        patient = Patient.active_query().filter_by(id=patient_id).first()
        if not patient:
            return {"message": "Patient not found"}, 404
        appointments = (
            Appointment.query.filter_by(patient_id=patient_id, status=STATUS_COMPLETED)
            .order_by(Appointment.date.desc(), Appointment.time.desc())
            .limit(100)
            .all()
        )
        out = []
        for a in appointments:
            d = a.to_dict()
            if a.treatment:
                d["treatment"] = a.treatment.to_dict()
            else:
                d["treatment"] = {"diagnosis": "", "prescription": ""}
            out.append(d)
        return out, 200


def register_doctor_api(api):
    api.add_resource(RecurringAvailabilityResource, "/recurring")
    api.add_resource(AvailabilityResource, "/availability")
    api.add_resource(DoctorAppointmentListResource, "/appointments")
    api.add_resource(DoctorAppointmentDetailResource, "/appointments/<int:id>")
    api.add_resource(DoctorAppointmentCompleteResource, "/appointments/<int:id>/complete")
    api.add_resource(DoctorAppointmentCancelResource, "/appointments/<int:id>/cancel")
    api.add_resource(DoctorPatientListResource, "/patients")
    api.add_resource(DoctorPatientHistoryResource, "/patients/<int:patient_id>/history")