<script setup>
import { ref, computed, onMounted, onActivated } from 'vue';
import { useRouter } from 'vue-router';
import StatCard from '@/components/StatCard.vue';
import { patients } from '@/data/mockData';
import Button from '@/components/ui/Button.vue';
import { useAuth } from '@/composables/useAuth.js';
import { useAppointments } from '@/composables/useAppointments.js';
import { format } from 'date-fns';
import api from '@/utils/api.js';
import { toast } from '@/utils/toast.js';

const router = useRouter();
const { user } = useAuth();
const doctorName = computed(() => user.value?.name || 'Doctor');
const { upcomingDoctorAppointments, loadingDoctorAppointments, fetchDoctorAppointments } = useAppointments();
const doctorPatients = ref([]);

const today = format(new Date(), 'yyyy-MM-dd');

onMounted(async () => {
  await fetchDoctorAppointments();
  try {
    const { data } = await api.get('/api/doctor/patients');
    doctorPatients.value = Array.isArray(data) ? data : [];
  } catch (_) {
    doctorPatients.value = [];
  }
});


const myAppointments = computed(() =>
  upcomingDoctorAppointments.value.filter(
    (a) =>
      a.doctor_name === doctorName.value &&
      (a.status || '').toLowerCase() !== 'cancelled'
  )
);

const todayAppointments = computed(() =>
  myAppointments.value.filter((a) => a.date === today)
);

const isBooked = (a) => (a.status || '').toLowerCase() === 'booked';
const isCompleted = (a) => (a.status || '').toLowerCase() === 'completed';

const upcomingAppointments = computed(() =>
  myAppointments.value.filter(
    (a) => a.date >= today && isBooked(a)
  )
);

const completedAppointments = computed(() =>
  myAppointments.value.filter(isCompleted).length
);

const displayedAppointments = computed(() => {
  const list = myAppointments.value.filter(
    (a) => a.date >= today && isBooked(a)
  );
  return [...list].sort((a, b) => {
    const dateCompare = (a.date || '').localeCompare(b.date || '');
    if (dateCompare !== 0) return dateCompare;
    return (a.time || '').localeCompare(b.time || '');
  });
});

const myPatients = computed(() => {
  if (doctorPatients.value.length > 0) return doctorPatients.value;
  const patientIds = [...new Set(myAppointments.value.map((a) => a.patient_id))];
  return patients.filter((p) => patientIds.includes(p.id));
});

const PATIENTS_DISPLAY_LIMIT = 5;
const displayedPatientsOnDashboard = computed(() =>
  myPatients.value.slice(0, PATIENTS_DISPLAY_LIMIT)
);
const showViewMorePatients = computed(() => myPatients.value.length > PATIENTS_DISPLAY_LIMIT);

async function completeAppointment(id) {
  try {
    await api.post(`/api/doctor/appointments/${id}/complete`, {
      diagnosis: '',
      prescription: '',
    });
    toast('Appointment completed');
    await fetchDoctorAppointments();
  } catch (e) {
    toast(e.response?.data?.message || 'Failed to complete', 'error');
  }
}

function goToAppointmentDetail(id) {
  router.push(`/doctor/appointments/${id}`);
}

function goToPatientsPage() {
  router.push('/doctor/patients');
}

const showHistoryModal = ref(false);
const selectedPatientForHistory = ref(null);
const patientHistory = ref([]);
const historyLoading = ref(false);
const expandedHistoryId = ref(null);

function openHistoryModal(patient) {
  selectedPatientForHistory.value = patient;
  showHistoryModal.value = true;
  expandedHistoryId.value = null;
  if (patient?.id) fetchPatientHistory(patient.id);
}

function closeHistoryModal() {
  showHistoryModal.value = false;
  selectedPatientForHistory.value = null;
  patientHistory.value = [];
}

async function fetchPatientHistory(patientId) {
  historyLoading.value = true;
  try {
    const { data } = await api.get(`/api/doctor/patients/${patientId}/history`);
    patientHistory.value = data || [];
  } catch (_) {
    patientHistory.value = [];
  } finally {
    historyLoading.value = false;
  }
}

function toggleHistoryRow(id) {
  expandedHistoryId.value = expandedHistoryId.value === id ? null : id;
}
</script>

<template>
  <div class="dashboard-spacing doctor-dashboard">
    <header class="dashboard-header">
      <h1 class="page-title">Welcome, {{ doctorName }}</h1>
      <p class="page-subtitle">Your schedule and patient overview</p>
    </header>

    <section class="section section-stats">
      <div class="dashboard-grid doctor-stat-cards">
        <StatCard
          title="Today's Appointments"
          :value="todayAppointments.length"
          icon="bi bi-calendar3"
          accent="stat-icon-primary"
        />
        <StatCard
          title="Upcoming"
          :value="upcomingAppointments.length"
          icon="bi bi-clock"
          accent="stat-icon-warning"
        />
        <StatCard
          title="My Patients"
          :value="myPatients.length"
          icon="bi bi-people"
          accent="stat-icon-teal"
        />
        <StatCard
          title="Completed"
          :value="completedAppointments"
          icon="bi bi-check2-circle"
          accent="stat-icon-success"
        />
      </div>
    </section>

    <section class="section section-cards">
      <div class="dashboard-cards-row doctor-cards-row">
        <div class="content-card content-card-appointments">
          <h3 class="content-card-title">
            <i class="bi bi-calendar-check content-card-icon"></i>
            My Appointments
          </h3>
          <div v-if="displayedAppointments.length === 0" class="content-card-empty">
            <i class="bi bi-calendar-x empty-icon"></i>
            <p class="mb-0">No appointments</p>
          </div>
          <div v-else class="appointment-list">
            <div
              v-for="apt in displayedAppointments"
              :key="apt.id"
              class="appointment-item appointment-item-clickable"
              role="button"
              tabindex="0"
              @click="goToAppointmentDetail(apt.id)"
              @keydown.enter="goToAppointmentDetail(apt.id)"
              @keydown.space.prevent="goToAppointmentDetail(apt.id)"
            >
              <div class="appointment-item-main">
                <p class="appointment-doctor">{{ apt.patient_name }}</p>
                <p class="appointment-meta">{{ apt.date }} · {{ apt.time }}</p>
                <p class="appointment-reason">{{ apt.reason || 'No reason' }}</p>
              </div>
              <div class="appointment-item-actions" @click.stop>
                <span class="badge badge-booked">Booked</span>
                <Button size="sm" variant="outline" class="btn-complete" @click="completeAppointment(apt.id)">
                  <i class="bi bi-check-lg me-1"></i>Complete
                </Button>
              </div>
            </div>
          </div>
        </div>

        <div class="content-card content-card-patients">
          <h3 class="content-card-title">
            <i class="bi bi-people content-card-icon"></i>
            My Patients
          </h3>
          <div v-if="myPatients.length === 0" class="content-card-empty">
            <i class="bi bi-person-x empty-icon"></i>
            <p class="mb-0">No patients yet</p>
          </div>
          <div v-else>
            <div class="patient-list">
              <div
                v-for="p in displayedPatientsOnDashboard"
                :key="p.id"
                class="patient-item patient-item-clickable"
                role="button"
                tabindex="0"
                @click="openHistoryModal(p)"
                @keydown.enter="openHistoryModal(p)"
                @keydown.space.prevent="openHistoryModal(p)"
              >
                <div class="patient-item-main">
                  <div class="patient-avatar">
                    {{ (p.name || '?').charAt(0) }}
                  </div>
                  <div class="patient-item-info">
                    <p class="patient-name">{{ p.name }}</p>
                    <p class="patient-meta">{{ (p.blood_group || p.bloodGroup) || '—' }} · {{ (p.contact_number || p.phone) || '—' }}</p>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="showViewMorePatients" class="view-more-wrap">
              <button type="button" class="btn-view-more" @click="goToPatientsPage">
                View more
                <i class="bi bi-chevron-right ms-1"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- History modal -->
    <div v-if="showHistoryModal" class="modal-overlay" @click.self="closeHistoryModal">
      <div class="modal-history">
        <div class="modal-content">
          <div class="modal-header-custom">
            <h5 class="modal-title">History — {{ selectedPatientForHistory?.name }}</h5>
            <button type="button" class="btn-close" @click="closeHistoryModal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div v-if="historyLoading" class="history-loading">Loading...</div>
            <div v-else-if="patientHistory.length === 0" class="history-empty">No past records</div>
            <div v-else class="history-list">
              <div
                v-for="item in patientHistory"
                :key="item.id"
                class="history-row"
              >
                <button
                  type="button"
                  class="history-row-header"
                  @click="toggleHistoryRow(item.id)"
                >
                  <span class="history-row-reason">{{ item.reason || 'No reason' }}</span>
                  <i class="bi history-row-chevron" :class="expandedHistoryId === item.id ? 'bi-chevron-up' : 'bi-chevron-down'"></i>
                </button>
                <div v-show="expandedHistoryId === item.id" class="history-row-content">
                  <div class="history-detail-box">
                    <span class="history-detail-label">Diagnosis:</span>
                    <p class="history-detail-text">{{ item.treatment?.diagnosis || '—' }}</p>
                  </div>
                  <div class="history-detail-box">
                    <span class="history-detail-label">Prescription:</span>
                    <p class="history-detail-text">{{ item.treatment?.prescription || '—' }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.doctor-dashboard {
  --section-radius: 1rem;
  --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  --card-shadow-hover: 0 8px 24px rgba(0, 0, 0, 0.08);
  --border-subtle: 1px solid rgba(0, 0, 0, 0.06);
  --accent: #0d6efd;
  --accent-soft: rgba(13, 110, 253, 0.08);
  --teal: #0d9488;
  --teal-soft: rgba(13, 148, 136, 0.1);
}

.dashboard-header {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: var(--border-subtle);
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

.section-stats {
  padding: 1.25rem;
}

.doctor-stat-cards {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
}

@media (min-width: 768px) {
  .doctor-stat-cards {
    grid-template-columns: repeat(4, 1fr);
  }
}

.section-cards {
  padding: 1.5rem;
}

.doctor-cards-row {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: 1fr;
}

@media (min-width: 768px) {
  .doctor-cards-row {
    grid-template-columns: 1fr 1fr;
  }
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
.patient-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.appointment-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 0;
  border-bottom: var(--border-subtle);
  gap: 1rem;
}

.appointment-item-clickable {
  cursor: pointer;
  transition: background 0.15s;
}

.appointment-item-clickable:hover {
  background: rgba(0, 0, 0, 0.02);
  margin: 0 -1rem;
  padding: 1rem;
  border-radius: 0.5rem;
}

.appointment-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.appointment-item:first-child {
  padding-top: 0;
}

.appointment-item-main {
  min-width: 0;
}

.appointment-doctor {
  font-weight: 600;
  font-size: 0.9375rem;
  margin: 0 0 0.2rem 0;
  color: var(--bs-body-color);
}

.appointment-meta {
  font-size: 0.8125rem;
  color: var(--bs-secondary-color);
  margin: 0;
}

.appointment-reason {
  font-size: 0.8125rem;
  color: var(--bs-secondary-color);
  margin: 0.25rem 0 0 0;
  font-style: italic;
}

.appointment-item-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
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

.btn-complete {
  flex-shrink: 0;
}

.patient-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 0;
  border-bottom: var(--border-subtle);
  gap: 1rem;
}

.patient-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.patient-item:first-child {
  padding-top: 0;
}

.patient-item-main {
  display: flex;
  align-items: center;
  gap: 1rem;
  min-width: 0;
}

.patient-avatar {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.75rem;
  background: linear-gradient(135deg, var(--teal) 0%, #0f766e 100%);
  color: #fff;
  font-weight: 700;
  font-size: 0.9375rem;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.patient-item-info {
  min-width: 0;
}

.patient-name {
  font-weight: 600;
  font-size: 0.9375rem;
  margin: 0 0 0.2rem 0;
  color: var(--bs-body-color);
}

.patient-meta {
  font-size: 0.8125rem;
  color: var(--bs-secondary-color);
  margin: 0;
}

.patient-item-clickable {
  cursor: pointer;
  padding: 5px;
  transition: background 0.15s;
  border: 1px solid transparent;
}

.patient-item-clickable:hover {
  background: rgba(106, 174, 247, 0.02);
  border: 1px solid rgba(165, 204, 245, 0.2);
  border-radius: 0.5rem;
}

.view-more-wrap {
  display: flex;
  justify-content: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: var(--border-subtle);
}

.btn-view-more {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--accent);
  background: var(--accent-soft);
  border: 1px solid rgba(13, 110, 253, 0.2);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
}

.btn-view-more:hover {
  background: rgba(13, 110, 253, 0.15);
  border-color: rgba(13, 110, 253, 0.35);
}

/* History modal */
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

.modal-history {
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-history .modal-content {
  background: var(--bs-body-bg);
  border-radius: 1rem;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.15);
  padding: 1.5rem;
  border: var(--border-subtle);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.modal-header-custom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  flex-shrink: 0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
}

.modal-body {
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.history-loading,
.history-empty {
  text-align: center;
  padding: 2rem;
  color: var(--bs-secondary-color);
  font-size: 0.9375rem;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.history-row {
  border-radius: 0.5rem;
  border: var(--border-subtle);
  overflow: hidden;
  background: var(--bs-body-bg);
}

.history-row-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  font-size: 0.9375rem;
  text-align: left;
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--bs-body-color);
  transition: background 0.2s;
}

.history-row-header:hover {
  background: rgba(0, 0, 0, 0.03);
}

.history-row-reason {
  font-weight: 500;
  flex: 1;
}

.history-row-chevron {
  font-size: 1rem;
  color: var(--bs-secondary-color);
  flex-shrink: 0;
  margin-left: 0.5rem;
}

.history-row-content {
  padding: 0 1rem 1rem;
  border-top: var(--border-subtle);
}

.history-detail-box {
  margin-top: 0.75rem;
  padding: 0.75rem;
  border-radius: 0.5rem;
  background: rgba(0, 0, 0, 0.02);
  border: var(--border-subtle);
}

.history-detail-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--bs-secondary-color);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.history-detail-text {
  font-size: 0.875rem;
  margin: 0.35rem 0 0 0;
  color: var(--bs-body-color);
  white-space: pre-wrap;
}
</style>
