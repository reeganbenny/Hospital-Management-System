<template>
  <div class="dashboard-spacing admin-list-page patients-page">
    <header class="dashboard-header">
      <h1 class="page-title">Manage Patients</h1>
      <p class="page-subtitle">View and manage patient records</p>
    </header>

    <section class="section section-table">
      <h3 class="section-title">
        <i class="bi bi-people section-icon"></i>
        Patients list
      </h3>
      <div class="search-bar-wrapper">
        <i class="bi bi-search search-bar-icon"></i>
        <Input
          v-model="searchQuery"
          placeholder="Search by name, email, or phone..."
          class="search-bar-input"
        />
      </div>
      <div class="content-card table-card">
        <div v-if="loading" class="content-card-empty">
          <p class="mb-0">Loading...</p>
        </div>
        <div v-else-if="filteredPatients.length === 0" class="content-card-empty">
          <i class="bi bi-person-x empty-icon"></i>
          <p class="mb-0">No patients</p>
        </div>
        <div v-else class="table-responsive">
          <table class="admin-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Gender</th>
                <th>Blood Group</th>
                <th>Status</th>
                <th class="admin-table-actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(p, idx) in filteredPatients" :key="p.id">
                <td>
                  <div class="table-cell-with-avatar">
                    <div class="patient-avatar" :class="idx % 2 === 0 ? 'patient-avatar-green' : 'patient-avatar-blue'">
                      {{ (p.name || '?').charAt(0).toUpperCase() }}
                    </div>
                    <span>{{ p.name }}</span>
                  </div>
                </td>
                <td>{{ p.email || '—' }}</td>
                <td>{{ p.phone || p.contact_number || '—' }}</td>
                <td>{{ p.gender || '—' }}</td>
                <td>{{ p.bloodGroup || p.blood_group || '—' }}</td>
                <td>
                  <span
                    class="badge"
                    :class="p.is_blocked ? 'badge-blocked' : 'badge-active'"
                  >
                    {{ p.is_blocked ? 'Blocked' : 'Active' }}
                  </span>
                </td>
                <td class="admin-table-actions">
                  <div class="action-buttons">
                    <button
                      type="button"
                      class="btn-icon"
                      :class="p.is_blocked ? 'text-success' : 'text-warning'"
                      :title="p.is_blocked ? 'Unblock' : 'Block'"
                      @click="toggleBlockPatient(p)"
                    >
                      <i class="bi" :class="p.is_blocked ? 'bi-unlock-fill' : 'bi-lock-fill'"></i>
                    </button>
                    <button type="button" class="btn-icon" title="View details" @click="viewPatient(p)">
                      <i class="bi bi-eye"></i>
                    </button>
                    <button type="button" class="btn-icon text-danger" title="Delete" @click="deletePatient(p.id)">
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- View Patient Modal (v-if overlay - no Bootstrap JS dependency) -->
    <div v-if="showViewPatientModal" class="modal-overlay" @click.self="closeViewPatientModal">
      <div class="modal-view-patient">
        <div class="modal-content">
          <div class="modal-header-custom">
            <h5 class="modal-title">Patient Details</h5>
            <button type="button" class="btn-close" @click="closeViewPatientModal" aria-label="Close"></button>
          </div>
          <div v-if="viewingPatient" class="modal-body">
            <div class="patient-detail-grid">
              <div class="patient-detail-item">
                <span class="patient-detail-label">Name</span>
                <span class="patient-detail-value">{{ viewingPatient.name || '—' }}</span>
              </div>
              <div class="patient-detail-item">
                <span class="patient-detail-label">Username</span>
                <span class="patient-detail-value">{{ viewingPatient.username || '—' }}</span>
              </div>
              <div class="patient-detail-item">
                <span class="patient-detail-label">Email</span>
                <span class="patient-detail-value">{{ viewingPatient.email || '—' }}</span>
              </div>
              <div class="patient-detail-item">
                <span class="patient-detail-label">Phone</span>
                <span class="patient-detail-value">{{ viewingPatient.phone || viewingPatient.contact_number || '—' }}</span>
              </div>
              <div class="patient-detail-item">
                <span class="patient-detail-label">Blood Group</span>
                <span class="patient-detail-value">{{ viewingPatient.bloodGroup || viewingPatient.blood_group || '—' }}</span>
              </div>
              <div class="patient-detail-item">
                <span class="patient-detail-label">Date of birth</span>
                <span class="patient-detail-value">{{ viewingPatient.date_of_birth || '—' }}</span>
              </div>
              <div class="patient-detail-item patient-detail-item-full">
                <span class="patient-detail-label">Address</span>
                <span class="patient-detail-value">{{ viewingPatient.address || '—' }}</span>
              </div>
              <div class="patient-detail-item">
                <span class="patient-detail-label">Status</span>
                <span
                  class="badge"
                  :class="viewingPatient.is_blocked ? 'badge-blocked' : 'badge-active'"
                >
                  {{ viewingPatient.is_blocked ? 'Blocked' : 'Active' }}
                </span>
              </div>
            </div>
          </div>
          <div class="modal-footer-custom">
            <button type="button" class="btn btn-secondary" @click="closeViewPatientModal">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import Input from '@/components/ui/Input.vue';
import api from '@/utils/api.js';
import { toast } from '@/utils/toast.js';
import { patients as mockPatients } from '@/data/mockData.js';

const patients = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const viewingPatient = ref(null);
const showViewPatientModal = ref(false);

const filteredPatients = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return patients.value;
  return patients.value.filter(
    (p) =>
      (p.name || '').toLowerCase().includes(q) ||
      (p.email || '').toLowerCase().includes(q) ||
      (p.phone || p.contact_number || '').includes(q)
  );
});

onMounted(async () => {
  loading.value = true;
  try {
    const { data } = await api.get('/api/admin/patients');
    patients.value = data || [];
  } catch {
    patients.value = [...mockPatients];
  } finally {
    loading.value = false;
  }
});

function viewPatient(p) {
  viewingPatient.value = { ...p };
  showViewPatientModal.value = true;
}

function closeViewPatientModal() {
  showViewPatientModal.value = false;
}

async function deletePatient(id) {
  if (!confirm('Remove this patient?')) return;
  try {
    await api.delete(`/api/admin/patients/${id}`);
    toast('Patient removed');
    patients.value = patients.value.filter((p) => p.id !== id);
  } catch (e) {
    toast(e.response?.data?.message || 'Failed', 'error');
  }
}

async function toggleBlockPatient(p) {
  try {
    const { data } = await api.post(`/api/admin/patients/${p.id}/block`);
    const updated = data?.patient;
    if (updated) {
      patients.value = patients.value.map((x) => (x.id === updated.id ? { ...x, ...updated } : x));
    }
    toast(updated?.is_blocked ? 'Patient blocked' : 'Patient unblocked');
  } catch (e) {
    toast(e.response?.data?.message || 'Failed', 'error');
  }
}
</script>

<style scoped>
.patients-page {
  --section-radius: 1rem;
  --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  --border-subtle: 1px solid rgba(0, 0, 0, 0.06);
  --accent: #102c48;
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

.section-title {
  font-size: 1.125rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: var(--bs-body-color);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-icon {
  font-size: 1.25rem;
  color: var(--accent);
  opacity: 0.9;
}

.search-bar-wrapper {
  position: relative;
  margin-bottom: 1.25rem;
}

.search-bar-wrapper .search-bar-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1rem;
  color: var(--bs-secondary-color);
  pointer-events: none;
}

.search-bar-input {
  padding-left: 2.75rem;
  border-radius: 0.75rem;
  border: var(--border-subtle);
}

.content-card {
  background: var(--bs-body-bg);
  border-radius: 0.75rem;
  padding: 1.5rem;
  border: var(--border-subtle);
  box-shadow: var(--card-shadow);
}

.table-card {
  padding: 1.25rem;
  overflow-x: auto;
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

.admin-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.admin-table th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  color: var(--bs-body-color);
  border-bottom: var(--border-subtle);
}

.admin-table td {
  padding: 0.75rem 1rem;
  border-bottom: var(--border-subtle);
  color: var(--bs-body-color);
}

.admin-table th.admin-table-actions,
.admin-table td.admin-table-actions {
  text-align: right;
}

.admin-table tbody tr:last-child td {
  border-bottom: none;
}

.admin-table tbody tr:hover {
  background: rgba(0, 0, 0, 0.02);
}

.table-cell-with-avatar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.patient-avatar {
  width: 2.5rem;
  height: 2.5rem;
  min-width: 2.5rem;
  border-radius: 50%;
  font-weight: 600;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.patient-avatar-green {
  background: rgba(25, 135, 84, 0.15);
  color: #198754;
}

.patient-avatar-blue {
  background: rgba(13, 110, 253, 0.15);
  color: #0d6efd;
}

.badge-active {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 0.5rem;
  background: rgba(25, 135, 84, 0.12);
  color: #198754;
}

.badge-blocked {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 0.5rem;
  background: rgba(220, 53, 69, 0.12);
  color: #dc3545;
}

.action-buttons {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.5rem;
}

.btn-icon {
  padding: 0.25rem;
  border: none;
  background: none;
  color: var(--bs-secondary-color);
  cursor: pointer;
  border-radius: 0.375rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: color 0.15s, background 0.15s;
}

.btn-icon:hover {
  background: rgba(0, 0, 0, 0.06);
  color: var(--bs-body-color);
}

.btn-icon.text-warning:hover { color: #fd7e14; }
.btn-icon.text-success:hover { color: #198754; }
.btn-icon.text-danger:hover { color: #dc3545; }

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
.modal-view-patient {
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.modal-view-patient .modal-content {
  background: var(--bs-body-bg);
  border-radius: 1rem;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.15);
  padding: 1.5rem;
  border: 1px solid rgba(0, 0, 0, 0.06);
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
.modal-view-patient .modal-body {
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}
.modal-footer-custom {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding-top: 1rem;
  margin-top: 1rem;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}
.patient-detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem 1.5rem;
}
.patient-detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.patient-detail-item-full {
  grid-column: 1 / -1;
}
.patient-detail-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--bs-secondary-color);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.patient-detail-value {
  font-size: 0.9375rem;
  color: var(--bs-body-color);
}
</style>
