import { format } from 'date-fns';

/**
 * Returns bookable slot times for a doctor on a given date.
 * Excludes slots already booked by the patient (booked_by_me).
 * When dateStr is today, excludes times that have already passed.
 *
 * @param {Object} doctor - Doctor with availability_slots: [{ date, slots: [{ time, booked_by_me }] }]
 * @param {string} dateStr - Date in yyyy-MM-dd format
 * @returns {string[]} Array of time strings e.g. ['09:30', '10:00']
 */
export function getBookableSlotsForDate(doctor, dateStr) {
  if (!doctor?.availability_slots || !dateStr) return [];
  const av = doctor.availability_slots.find((a) => a.date === dateStr);
  const list = av?.slots ?? [];
  let times = list
    .filter((s) => !s?.booked_by_me)
    .map((s) => (typeof s === 'object' ? s.time : s));
  const today = format(new Date(), 'yyyy-MM-dd');
  if (dateStr === today && times.length > 0) {
    const now = new Date();
    const nowStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
    times = times.filter((slotTime) => slotTime > nowStr);
  }
  return times;
}
