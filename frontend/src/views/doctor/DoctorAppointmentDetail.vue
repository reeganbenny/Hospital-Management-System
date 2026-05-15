<template>
  <div class="dashboard-spacing doctor-appointment-detail">
    <header class="dashboard-header">
      <div class="dashboard-header-inner">
        <div>
          <h1 class="page-title">Appointment</h1>
          <p class="page-subtitle">{{ appointment ? `${appointment.date} · ${appointment.time}` : 'Loading...' }}</p>
        </div>
        <router-link v-if="appointment" to="/doctor" class="btn-back">
          <i class="bi bi-arrow-left me-1"></i>Back to Dashboard
        </router-link>
      </div>
    </header>

    <template v-if="loading">
      <section class="section">
        <div class="content-card">
          <div class="content-card-empty">
            <i class="bi bi-hourglass-split empty-icon"></i>
            <p class="mb-0">Loading...</p>
          </div>
        </div>
      </section>
    </template>

    <template v-else-if="appointment">
      <section class="section section-detail">
        <div class="content-card">
          <div class="detail-header">
            <div class="detail-patient-info">
              <p class="detail-patient-name">Patient: {{ appointment.patient_name }}</p>
              <p class="detail-patient-meta">Blood Group: {{ appointment.patient_blood_group || '—' }}</p>
            </div>
            <button type="button" class="btn-history" @click="openHistoryModal">
              <i class="bi bi-clock-history me-1"></i>History
            </button>
          </div>

          <div class="detail-field">
            <label class="detail-label">Reason:</label>
            <div class="detail-reason-box">
              {{ appointment.reason || 'No reason provided' }}
            </div>
          </div>

          <div class="detail-row">
            <div class="detail-field detail-field-half">
              <label class="detail-label">Diagnosis:</label>
              <textarea
                v-model="diagnosis"
                class="detail-input"
                rows="4"
                placeholder="Enter diagnosis"
              ></textarea>
            </div>
            <div class="detail-field detail-field-half">
              <label class="detail-label">Prescription:</label>
              <textarea
                v-model="prescription"
                class="detail-input"
                rows="4"
                placeholder="Enter prescription"
              ></textarea>
            </div>
          </div>

          <p v-if="error" class="detail-error">{{ error }}</p>

          <div class="detail-actions">
            <button
              type="button"
              class="btn-cancel-apt"
              :disabled="actionInProgress || isCompletedOrCancelled"
              @click="cancelAppointment"
            >
              Cancel Appointment
            </button>
            <button
              type="button"
              class="btn-complete-apt"
              :disabled="actionInProgress || isCompletedOrCancelled"
              @click="completeAppointment"
            >
              <i class="bi bi-check-lg me-1"></i>Complete
            </button>
          </div>
        </div>
      </section>
    </template>

    <template v-else>
      <section class="section">
        <div class="content-card">
          <div class="content-card-empty">
            <i class="bi bi-exclamation-circle empty-icon"></i>
            <p class="mb-0">Appointment not found</p>
            <router-link to="/doctor" class="btn-back mt-3 d-inline-block">Back to Dashboard</router-link>
          </div>
        </div>
      </section>
    </template>

    <!-- History Modal -->
    <div v-if="showHistoryModal" class="modal-overlay" @click.self="closeHistoryModal">
      <div class="modal-history">
        <div class="modal-content">
          <div class="modal-header-custom">
            <h5 class="modal-title">History</h5>
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
                :class="{ 'history-row-expanded': expandedHistoryId === item.id }"
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

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '@/utils/api.js';
import { toast } from '@/utils/toast.js';

const route = useRoute();
const router = useRouter();
const appointment = ref(null);
const loading = ref(true);
const error = ref('');
const actionInProgress = ref(false);
const diagnosis = ref('');
const prescription = ref('');

const showHistoryModal = ref(false);
const patientHistory = ref([]);
const historyLoading = ref(false);
const expandedHistoryId = ref(null);

const isCompletedOrCancelled = computed(() => {
  const s = (appointment.value?.status || '').toLowerCase();
  return s === 'completed' || s === 'cancelled';
});

onMounted(async () => {
  await fetchAppointment();
});

watch(() => route.params.id, () => {
  fetchAppointment();
});

async function fetchAppointment() {
  const id = route.params.id;
  if (!id) return;
  loading.value = true;
  error.value = '';
  try {
    const { data } = await api.get(`/api/doctor/appointments/${id}`);
    appointment.value = data;
    diagnosis.value = data.treatment?.diagnosis || '';
    prescription.value = data.treatment?.prescription || '';
  } catch (_) {
    appointment.value = null;
  } finally {
    loading.value = false;
  }
}

function openHistoryModal() {
  showHistoryModal.value = true;
  expandedHistoryId.value = null;
  if (appointment.value?.patient_id) {
    fetchPatientHistory();
  }
}

function closeHistoryModal() {
  showHistoryModal.value = false;
  patientHistory.value = [];
}

async function fetchPatientHistory() {
  if (!appointment.value?.patient_id) return;
  historyLoading.value = true;
  try {
    const { data } = await api.get(`/api/doctor/patients/${appointment.value.patient_id}/history`);
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

async function completeAppointment() {
  if (!appointment.value || isCompletedOrCancelled.value) return;
  error.value = '';
  actionInProgress.value = true;
  try {
    await api.post(`/api/doctor/appointments/${appointment.value.id}/complete`, {
      diagnosis: diagnosis.value?.trim() || '',
      prescription: prescription.value?.trim() || '',
    });
    toast('Appointment completed');
    await fetchAppointment();
  } catch (e) {
    error.value = e.response?.data?.message || 'Failed to complete';
    toast(error.value, 'error');
  } finally {
    actionInProgress.value = false;
  }
}

async function cancelAppointment() {
  if (!appointment.value || isCompletedOrCancelled.value) return;
  if (!confirm('Cancel this appointment?')) return;
  error.value = '';
  actionInProgress.value = true;
  try {
    await api.post(`/api/doctor/appointments/${appointment.value.id}/cancel`);
    toast('Appointment cancelled');
    await fetchAppointment();
  } catch (e) {
    error.value = e.response?.data?.message || 'Failed to cancel';
    toast(error.value, 'error');
  } finally {
    actionInProgress.value = false;
  }
}
</script>

<style scoped>
.doctor-appointment-detail {
  --section-radius: 1rem;
  --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  --border-subtle: 1px solid rgba(0, 0, 0, 0.06);
  --accent: #0d6efd;
  --accent-soft: rgba(13, 110, 253, 0.08);
  --teal: #0d9488;
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

.btn-back {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--accent);
  text-decoration: none;
  border-radius: 0.5rem;
  border: 1px solid rgba(13, 110, 253, 0.3);
  background: var(--accent-soft);
}

.btn-back:hover {
  background: rgba(13, 110, 253, 0.15);
  color: var(--accent);
}

.section {
  background: var(--bs-body-bg);
  border-radius: var(--section-radius);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--card-shadow);
  border: var(--border-subtle);
}

.content-card {
  background: var(--bs-body-bg);
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: var(--border-subtle);
  box-shadow: var(--card-shadow);
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

.detail-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.detail-patient-name {
  font-weight: 600;
  font-size: 1.0625rem;
  margin: 0 0 0.25rem 0;
  color: var(--bs-body-color);
}

.detail-patient-meta {
  font-size: 0.9375rem;
  color: var(--bs-secondary-color);
  margin: 0;
}

.btn-history {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  border-radius: 0.5rem;
  border: var(--border-subtle);
  background: var(--bs-body-bg);
  color: var(--bs-body-color);
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.btn-history:hover {
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(13, 110, 253, 0.3);
}

.detail-field {
  margin-bottom: 1.25rem;
}

.detail-label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--bs-body-color);
  margin-bottom: 0.35rem;
  display: block;
}

.detail-reason-box {
  padding: 1rem;
  border-radius: 0.5rem;
  border: var(--border-subtle);
  background: rgba(0, 0, 0, 0.02);
  font-size: 0.9375rem;
  color: var(--bs-body-color);
}

.detail-row {
  display: grid;
  gap: 1.25rem;
  grid-template-columns: 1fr 1fr;
  margin-bottom: 1.25rem;
}

@media (max-width: 767px) {
  .detail-row {
    grid-template-columns: 1fr;
  }
}

.detail-field-half {
  margin-bottom: 0;
}

.detail-input {
  width: 100%;
  padding: 0.75rem;
  font-size: 0.9375rem;
  border-radius: 0.5rem;
  border: var(--border-subtle);
  background: var(--bs-body-bg);
  color: var(--bs-body-color);
  resize: vertical;
}

.detail-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.detail-error {
  font-size: 0.875rem;
  color: var(--bs-danger);
  margin-bottom: 1rem;
}

.detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  padding-top: 1.25rem;
  border-top: var(--border-subtle);
}

.btn-cancel-apt {
  padding: 0.5rem 1.25rem;
  font-size: 0.9375rem;
  font-weight: 600;
  border-radius: 0.5rem;
  border: 1px solid var(--bs-border-color);
  background: var(--bs-body-bg);
  color: var(--bs-body-color);
  cursor: pointer;
  transition: background 0.2s;
}

.btn-cancel-apt:hover:not(:disabled) {
  background: rgba(220, 53, 69, 0.08);
  border-color: rgba(220, 53, 69, 0.4);
  color: var(--bs-danger);
}

.btn-cancel-apt:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-complete-apt {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 1.25rem;
  font-size: 0.9375rem;
  font-weight: 600;
  border-radius: 0.5rem;
  border: none;
  background: var(--accent);
  color: #fff;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-complete-apt:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-complete-apt:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* History Modal */
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
