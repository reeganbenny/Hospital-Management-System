"""Shared availability helpers for doctor slots, appointments."""
from datetime import date, timedelta

from models import Doctor, DoctorAvailability, Appointment
from models import STATUS_BOOKED

ALL_SLOTS = [
    "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00",
    "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00",
]


def expand_range_to_slots(start_str, end_str):
    """Expand a time range to 30-min slot start times. E.g. 09:00-12:00 -> [09:00, 09:30, ...]"""
    slots = []
    try:
        sh, sm = map(int, start_str.split(":"))
        eh, em = map(int, end_str.split(":"))
        start_mins = sh * 60 + sm
        end_mins = eh * 60 + em
        t = start_mins
        while t < end_mins:
            h, m = divmod(t, 60)
            slots.append(f"{h:02d}:{m:02d}")
            t += 30
    except (ValueError, AttributeError):
        pass
    return slots


def day_of_week_user(d):
    """Convert Python weekday (0=Mon, 6=Sun) to user convention (0=Sun, 1=Mon, ..., 6=Sat)."""
    return (d.weekday() + 1) % 7


def get_merged_slots_for_doctor(doctor, start_date, num_days=7):
    """Return { dateStr: [time, ...] } for next num_days from start_date."""
    recurring = doctor.availability or []
    result = {}
    for i in range(num_days):
        d = start_date + timedelta(days=i)
        date_str = d.isoformat()
        dow = day_of_week_user(d)
        base_slots = []
        for r in recurring:
            if r.get("day_of_week") == dow:
                st = r.get("start_time") or r.get("start")
                et = r.get("end_time") or r.get("end")
                if st and et:
                    base_slots.extend(expand_range_to_slots(st, et))
        overrides = DoctorAvailability.query.filter_by(doctor_id=doctor.id, date=d).all()
        if overrides:
            slot_set = set()
            for s in overrides:
                if s.start_time:
                    slot_set.add(s.start_time.strftime("%H:%M"))
            slots = sorted(slot_set)
        else:
            slots = sorted(list(set(base_slots)))
        result[date_str] = slots
    return result


def get_booked_slots_by_date(doctor_id, start_date, num_days=7):
    """Return { dateStr: [time_str, ...] } for booked appointments."""
    result = {}
    for i in range(num_days):
        d = start_date + timedelta(days=i)
        date_str = d.isoformat()
        apps = Appointment.query.filter_by(
            doctor_id=doctor_id,
            date=d,
            status=STATUS_BOOKED,
        ).all()
        times = sorted({a.time.strftime("%H:%M") for a in apps if a.time})
        result[date_str] = times
    return result


def get_booked_slots_with_patient(doctor_id, start_date, num_days=7):
    """Return { dateStr: { "09:00": patient_id or None } } for booked appointments."""
    result = {}
    for i in range(num_days):
        d = start_date + timedelta(days=i)
        date_str = d.isoformat()
        apps = Appointment.query.filter_by(
            doctor_id=doctor_id,
            date=d,
            status=STATUS_BOOKED,
        ).all()
        by_time = {}
        for a in apps:
            if a.time:
                by_time[a.time.strftime("%H:%M")] = a.patient_id
        result[date_str] = by_time
    return result


def get_slots_with_status(doctor, start_date, num_days=7):
    """Return { dateStr: { "09:00": "available"|"booked"|"not_selected", ... } } for admin/doctor view."""
    merged = get_merged_slots_for_doctor(doctor, start_date, num_days)
    booked = get_booked_slots_by_date(doctor.id, start_date, num_days)
    result = {}
    for i in range(num_days):
        d = start_date + timedelta(days=i)
        date_str = d.isoformat()
        merged_set = set(merged.get(date_str, []))
        booked_set = set(booked.get(date_str, []))
        by_slot = {}
        for slot in ALL_SLOTS:
            if slot not in merged_set:
                by_slot[slot] = "not_selected"
            elif slot in booked_set:
                by_slot[slot] = "booked"
            else:
                by_slot[slot] = "available"
        result[date_str] = by_slot
    return result


def get_available_slots_for_patient(doctor, start_date, num_days=7, patient_id=None):
    """
    Return availability_slots for patient view.
    { dateStr: [{ "time": "09:00", "booked_by_me": bool }, ...] }
    Slots = (merged minus others' booked) union (slots booked by this patient with booked_by_me=True)
    """
    merged = get_merged_slots_for_doctor(doctor, start_date, num_days)
    booked_by_patient = get_booked_slots_with_patient(doctor.id, start_date, num_days)
    result = {}
    for i in range(num_days):
        d = start_date + timedelta(days=i)
        date_str = d.isoformat()
        merged_list = merged.get(date_str, [])
        by_patient = booked_by_patient.get(date_str, {})
        slots_out = []
        seen = set()
        for t in merged_list:
            pid = by_patient.get(t)
            if pid is None:
                slots_out.append({"time": t, "booked_by_me": False})
            elif patient_id and pid == patient_id:
                slots_out.append({"time": t, "booked_by_me": True})
            else:
                continue
            seen.add(t)
        result[date_str] = slots_out
    return result


def availability_slots_to_list(slots_by_date):
    """Convert { dateStr: [...] } to [{ date, slots }, ...] for API response."""
    return [
        {"date": d, "slots": slots}
        for d, slots in sorted(slots_by_date.items())
    ]
