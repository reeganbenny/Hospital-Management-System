<template>
  <div class="dashboard-spacing my-appointments-page">
    <header class="dashboard-header">
      <div class="dashboard-header-inner">
        <div>
          <h1 class="page-title">My Appointments</h1>
          <p class="page-subtitle">All appointments and treatment history</p>
        </div>
        <div class="dashboard-header-actions">
          <button
            type="button"
            class="btn-header btn-export"
            :disabled="exportLoading"
            @click="triggerExport"
          >
            <i class="bi bi-download me-1"></i>{{ exportLoading ? 'Generating...' : 'Export CSV' }}
          </button>
        </div>
      </div>
    </header>

    <section class="section section-cards">
      <div class="content-card content-card-appointments">
        <h3 class="content-card-title">
          <i class="bi bi-calendar-check content-card-icon"></i>
          All Appointments
        </h3>
        <div v-if="loading" class="content-card-empty">
          <i class="bi bi-hourglass-split empty-icon"></i>
          <p class="mb-0">Loading...</p>
        </div>
        <div v-else-if="allAppointments.length === 0" class="content-card-empty">
          <i class="bi bi-calendar-x empty-icon"></i>
          <p class="mb-0">No appointments</p>
        </div>
        <div v-else class="appointment-table">
          <span class="appointment-th">Doctor</span>
          <span class="appointment-th">Date</span>
          <span class="appointment-th">Time</span>
          <span class="appointment-th">Status</span>
          <span class="appointment-th">Actions</span>
          <template v-for="a in allAppointments" :key="a.id">
            <span class="appointment-td appointment-td-doctor">{{ a.doctor_name }}</span>
            <span class="appointment-td">{{ a.date }}</span>
            <span class="appointment-td">{{ a.time }}</span>
            <span class="appointment-td">
              <span class="badge" :class="statusBadgeClass(a.status)">{{ a.status }}</span>
            </span>
            <span class="appointment-td appointment-td-actions">
              <template v-if="a.status === 'Booked'">
                <button
                  type="button"
                  class="btn-reschedule"
                  @click="openRescheduleModal(a)"
                >
                  <i class="bi bi-calendar-event me-1"></i>Reschedule
                </button>
                <button
                  type="button"
                  class="btn-cancel"
                  @click="cancel(a.id)"
                >
                  <i class="bi bi-x-lg me-1"></i>Cancel
                </button>
              </template>
              <span v-else>—</span>
            </span>
          </template>
        </div>
      </div>
    </section>

    <section class="section section-cards">
      <div class="content-card content-card-treatments">
        <h3 class="content-card-title">
          <i class="bi bi-file-medical content-card-icon"></i>
          Past & treatment history
        </h3>
        <div v-if="pastFiltered.length === 0" class="content-card-empty">
          <i class="bi bi-clipboard2-pulse empty-icon"></i>
          <p class="mb-0">No past appointments</p>
        </div>
        <div v-else class="treatment-list">
          <div class="treatment-list-header">
            <span class="th-date">Date</span>
            <span class="th-doctor">Doctor</span>
            <span class="th-diagnosis">Diagnosis</span>
            <span class="th-prescription">Prescription</span>
          </div>
          <div v-for="a in pastFiltered" :key="a.id" class="treatment-item">
            <span class="treatment-date">{{ a.date }}</span>
            <span class="treatment-doctor">{{ a.doctor_name }}</span>
            <span class="treatment-diagnosis">{{ a.treatment?.diagnosis || '—' }}</span>
            <span class="treatment-prescription">{{ a.treatment?.prescription || '—' }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Reschedule Modal -->
    <div v-if="showRescheduleModal" class="modal-overlay" @click.self="closeRescheduleModal">
      <div class="modal-dialog-book">
        <div class="modal-content">
          <div class="modal-header-custom">
            <h5 class="modal-title">Reschedule Appointment</h5>
            <button type="button" class="btn-close" @click="closeRescheduleModal" aria-label="Close"></button>
          </div>
          <div v-if="rescheduleAppointment" class="modal-body">
            <p class="modal-doctor-info">
              {{ rescheduleAppointment.doctor_name }}{{ rescheduleAppointment.specialization ? ` — ${rescheduleAppointment.specialization}` : '' }}
            </p>
            <div class="mb-3">
              <label class="form-label">New date</label>
              <div class="date-input-wrapper">
                <input
                  v-model="rescheduleDate"
                  type="date"
                  class="form-control date-input"
                  :min="minRescheduleDate"
                  :max="maxRescheduleDate"
                />
                <i class="bi bi-calendar3 date-icon"></i>
              </div>
            </div>
            <div class="mb-4">
              <label class="form-label">Available slots</label>
              <div class="slots-row">
                <button
                  v-for="slot in rescheduleSlots"
                  :key="slot"
                  type="button"
                  class="slot-btn-modal"
                  :class="{ 'slot-btn-modal-selected': rescheduleTime === slot }"
                  @click="rescheduleTime = slot"
                >
                  {{ slot }}
                </button>
              </div>
              <p v-if="rescheduleSlots.length === 0 && rescheduleDate" class="small text-body-secondary mt-2 mb-0">
                No slots available for this date
              </p>
            </div>
            <p v-if="rescheduleError" class="text-danger small mb-2">{{ rescheduleError }}</p>
          </div>
          <div class="modal-footer-custom">
            <button
              type="button"
              class="btn-secondary-modal"
              @click="closeRescheduleModal"
            >
              Cancel
            </button>
            <button
              type="button"
              class="btn-primary-modal"
              :disabled="rescheduleInProgress || !rescheduleTime"
              @click="confirmReschedule"
            >
              {{ rescheduleInProgress ? 'Updating...' : 'Reschedule' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { format, addDays } from 'date-fns';
import api from '@/utils/api.js';
import { useDoctors } from '@/composables/useDoctors.js';
import { getBookableSlotsForDate } from '@/composables/useBookingSlots.js';
import { toast } from '@/utils/toast.js';

const allAppointments = ref([]);
const past = ref([]);
const loading = ref(true);
const { doctors, fetchDoctors } = useDoctors();

const exportTaskId = ref(null);
const exportStatus = ref('');
const exportDownloadUrl = ref('');
const exportLoading = ref(false);

const showRescheduleModal = ref(false);
const rescheduleAppointment = ref(null);
const rescheduleDate = ref('');
const rescheduleTime = ref('');
const rescheduleError = ref('');
const rescheduleInProgress = ref(false);

const minRescheduleDate = format(new Date(), 'yyyy-MM-dd');
const maxRescheduleDate = format(addDays(new Date(), 14), 'yyyy-MM-dd');

const pastFiltered = computed(() =>
  past.value.filter((a) => a.status !== 'Cancelled')
);

const rescheduleDoctor = computed(() => {
  if (!rescheduleAppointment.value?.doctor_id || !doctors.value?.length) return null;
  return doctors.value.find((d) => d.id === rescheduleAppointment.value.doctor_id) || null;
});

const rescheduleSlots = computed(() => {
  const doc = rescheduleDoctor.value;
  const dateStr = rescheduleDate.value;
  if (!doc || !dateStr) return [];
  let slots = getBookableSlotsForDate(doc, dateStr) || [];
  const apt = rescheduleAppointment.value;
  if (apt && apt.date === dateStr && apt.time) {
    const timeStr = typeof apt.time === 'string' ? apt.time : `${String(apt.time?.hour ?? 0).padStart(2, '0')}:${String(apt.time?.minute ?? 0).padStart(2, '0')}`;
    if (timeStr && !slots.includes(timeStr)) slots = [timeStr, ...slots];
  }
  return slots;
});

function statusBadgeClass(status) {
  if (status === 'Booked') return 'badge-booked';
  if (status === 'Completed') return 'badge-completed';
  if (status === 'Cancelled') return 'badge-cancelled';
  return 'badge-default';
}

onMounted(async () => {
  loading.value = true;
  try {
    const [apptsRes, dashboardRes] = await Promise.all([
      api.get('/api/patient/appointments'),
      api.get('/api/patient/dashboard'),
    ]);
    allAppointments.value = apptsRes.data || [];
    past.value = dashboardRes.data?.past_appointments || [];
  } catch (_) {
    allAppointments.value = [];
    past.value = [];
  } finally {
    loading.value = false;
  }
  await fetchDoctors();
});

async function cancel(id) {
  if (!confirm('Cancel this appointment?')) return;
  try {
    await api.post(`/api/patient/appointments/${id}/cancel`);
    const a = allAppointments.value.find((x) => x.id === id);
    if (a) a.status = 'Cancelled';
    toast('Appointment cancelled');
  } catch (e) {
    toast(e.response?.data?.message || 'Failed to cancel', 'error');
  }
}

function openRescheduleModal(apt) {
  rescheduleAppointment.value = apt;
  rescheduleDate.value = apt.date || minRescheduleDate;
  rescheduleTime.value = '';
  rescheduleError.value = '';
  showRescheduleModal.value = true;
}

function closeRescheduleModal() {
  showRescheduleModal.value = false;
  rescheduleAppointment.value = null;
  rescheduleDate.value = '';
  rescheduleTime.value = '';
  rescheduleError.value = '';
}

watch(rescheduleDate, () => {
  rescheduleTime.value = '';
});

async function confirmReschedule() {
  if (!rescheduleAppointment.value || !rescheduleDate.value || !rescheduleTime.value) {
    toast('Please select date and time', 'error');
    return;
  }
  rescheduleError.value = '';
  rescheduleInProgress.value = true;
  try {
    await api.post(`/api/patient/appointments/${rescheduleAppointment.value.id}/reschedule`, {
      date: rescheduleDate.value,
      time: rescheduleTime.value,
    });
    const a = allAppointments.value.find((x) => x.id === rescheduleAppointment.value.id);
    if (a) {
      a.date = rescheduleDate.value;
      a.time = rescheduleTime.value;
    }
    toast('Appointment rescheduled');
    closeRescheduleModal();
  } catch (e) {
    rescheduleError.value = e.response?.data?.message || 'Reschedule failed';
    toast(rescheduleError.value, 'error');
  } finally {
    rescheduleInProgress.value = false;
  }
}

function triggerExport() {
  exportLoading.value = true;
  exportTaskId.value = null;
  api.post('/api/patient/export-csv')
    .then((r) => {
      exportTaskId.value = r.data.task_id;
      exportStatus.value = 'pending';
      pollExport();
    })
    .catch(() => { exportLoading.value = false; });
}

function pollExport() {
  if (!exportTaskId.value) return;
  api.get(`/api/patient/export-csv/${exportTaskId.value}`).then((r) => {
    exportStatus.value = r.data.status;
    if (r.data.status === 'completed' && r.data.result?.download_url) {
      const url = window.location.origin + r.data.result.download_url;
      exportDownloadUrl.value = url;
      exportLoading.value = false;
      const a = document.createElement('a');
      a.href = url;
      a.download = r.data.result.filename || 'appointments.csv';
      a.rel = 'noopener noreferrer';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } else if (r.data.status === 'failed') {
      exportLoading.value = false;
    } else {
      setTimeout(pollExport, 2000);
    }
  }).catch(() => { exportLoading.value = false; });
}
</script>

<style scoped>
.my-appointments-page {
  --section-radius: 1rem;
  --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  --card-shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.08);
  --border-subtle: 1px solid rgba(0, 0, 0, 0.06);
  --accent: #0d6efd;
  --accent-soft: rgba(13, 110, 253, 0.08);
}

.dashboard-header {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: var(--border-subtle);
}

.dashboard-header-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.dashboard-header-actions {
  flex-shrink: 0;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--bs-body-color);
  margin: 0 0 0.25rem 0;
}

.page-subtitle {
  font-size: 1rem;
  color: var(--bs-secondary-color);
  margin: 0;
}

.section {
  background: var(--bs-body-bg);
  border-radius: var(--section-radius);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--card-shadow);
  border: var(--border-subtle);
}

.section-cards {
  padding: 1.5rem;
}

.content-card {
  background: var(--bs-body-bg);
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: var(--border-subtle);
  box-shadow: var(--card-shadow);
}

.content-card-title {
  font-size: 1.0625rem;
  font-weight: 700;
  margin-bottom: 1.25rem;
  color: var(--bs-body-color);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.content-card-icon {
  font-size: 1.125rem;
  color: var(--accent);
}

.content-card-empty {
  text-align: center;
  padding: 2rem 1rem;
  color: var(--bs-secondary-color);
  font-size: 0.9375rem;
}

.empty-icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 0.5rem;
  opacity: 0.5;
}

.appointment-list,
.treatment-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* Single grid so header and rows share column tracks and align */
.appointment-table {
  display: grid;
  grid-template-columns: 1fr minmax(6rem, auto) minmax(5rem, auto) minmax(5rem, auto) minmax(10rem, 1fr);
  gap: 0 1rem;
  align-items: center;
}

.appointment-th {
  padding: 0.75rem 0;
  border-bottom: var(--border-subtle);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--bs-secondary-color);
}

.appointment-td {
  padding: 1rem 0;
  border-bottom: var(--border-subtle);
  font-size: 0.9375rem;
  color: var(--bs-body-color);
}

.appointment-td-doctor {
  font-weight: 600;
  color: var(--bs-body-color);
}

.appointment-td-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.appointment-td-actions .btn-reschedule,
.appointment-td-actions .btn-cancel {
  flex-shrink: 0;
}

/* Keep last row border clean */
.appointment-table .appointment-td:nth-last-child(-n+5) {
  border-bottom: none;
}

.badge-booked {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 0.5rem;
  background: var(--accent-soft);
  color: var(--accent);
}

.badge-completed {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 0.5rem;
  background: rgba(25, 135, 84, 0.12);
  color: #198754;
}

.badge-cancelled {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 0.5rem;
  background: rgba(220, 53, 69, 0.12);
  color: #dc3545;
}

.badge-default {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 0.5rem;
  background: rgba(0, 0, 0, 0.06);
  color: var(--bs-secondary-color);
}

.btn-reschedule {
  padding: 0.25rem 0.5rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--accent);
  background: var(--accent-soft);
  border: 1px solid rgba(13, 110, 253, 0.25);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.btn-reschedule:hover {
  background: rgba(13, 110, 253, 0.15);
  border-color: rgba(13, 110, 253, 0.4);
}

.btn-cancel {
  background: none;
  border: none;
  padding: 0.25rem 0.5rem;
  font-size: 0.8125rem;
  color: var(--bs-danger);
  cursor: pointer;
  text-decoration: none;
  transition: opacity 0.2s;
}

.btn-cancel:hover {
  opacity: 0.85;
  text-decoration: underline;
}

.treatment-item {
  display: grid;
  grid-template-columns: auto 1fr auto 1fr;
  gap: 0.75rem 1rem;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: var(--border-subtle);
  font-size: 0.9375rem;
  color: var(--bs-body-color);
}

.treatment-list-header {
  display: grid;
  grid-template-columns: auto 1fr auto 1fr;
  gap: 0.75rem 1rem;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: var(--border-subtle);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--bs-secondary-color);
}

.treatment-item:last-child {
  border-bottom: none;
}

@media (max-width: 767px) {
  .treatment-item {
    grid-template-columns: 1fr;
  }
  .treatment-list-header {
    grid-template-columns: 1fr;
  }
}

.treatment-date {
  font-weight: 500;
}

.treatment-doctor {
  color: var(--bs-secondary-color);
}

.treatment-diagnosis,
.treatment-prescription {
  color: var(--bs-body-color);
}

.btn-header {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  border-radius: 0.5rem;
  transition: background 0.2s, border-color 0.2s, opacity 0.2s;
}

.dashboard-header-actions .btn-export {
  border: var(--border-subtle);
  background: var(--bs-body-bg);
  color: var(--bs-body-color);
  cursor: pointer;
}

.dashboard-header-actions .btn-export:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(13, 110, 253, 0.3);
}

.dashboard-header-actions .btn-export:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.dashboard-header-actions .btn-download {
  background: #198754;
  color: #fff;
  text-decoration: none;
}

.dashboard-header-actions .btn-download:hover {
  opacity: 0.9;
  color: #fff;
}

/* Reschedule Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
  padding: 1rem;
}

.modal-dialog-book {
  width: 100%;
  max-width: 420px;
}

.modal-content {
  background: var(--bs-body-bg);
  border-radius: 1rem;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.15);
  padding: 1.5rem;
  border: var(--border-subtle);
}

.modal-header-custom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
}

.modal-doctor-info {
  font-weight: 500;
  margin-bottom: 1rem;
  font-size: 0.9375rem;
}

.date-input-wrapper {
  position: relative;
}

.date-input {
  padding-right: 2.5rem;
  border-radius: 0.5rem;
}

.date-icon {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1rem;
  color: var(--bs-secondary-color);
  pointer-events: none;
}

.slots-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.slot-btn-modal {
  padding: 0.4rem 0.75rem;
  font-size: 0.875rem;
  border-radius: 0.5rem;
  border: var(--border-subtle);
  background: var(--bs-body-bg);
  color: var(--bs-body-color);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.slot-btn-modal:hover {
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(13, 110, 253, 0.3);
}

.slot-btn-modal-selected {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.modal-footer-custom {
  display: flex;
  justify-content: center;
  gap: 0.75rem;
  padding-top: 1rem;
}

.btn-secondary-modal {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  border-radius: 0.5rem;
  border: var(--border-subtle);
  background: var(--bs-body-bg);
  color: var(--bs-body-color);
  cursor: pointer;
}

.btn-primary-modal {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  border-radius: 0.5rem;
  border: none;
  background: var(--accent);
  color: white;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-primary-modal:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-primary-modal:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
