<template>
  <div class="dashboard-spacing admin-list-page appointments-page">
    <header class="dashboard-header">
      <h1 class="page-title">All Appointments</h1>
      <p class="page-subtitle">View and manage hospital appointments</p>
    </header>

    <section class="section section-stats">
      <div class="dashboard-grid admin-stat-cards">
        <StatCard title="Booked" :value="bookedCount" icon="bi bi-calendar-check" accent="stat-icon-primary" />
        <StatCard title="Completed" :value="completedCount" icon="bi bi-check-circle" accent="stat-icon-success" />
        <StatCard title="Cancelled" :value="cancelledCount" icon="bi bi-x-circle" accent="stat-icon-danger" />
      </div>
    </section>

    <section class="section section-table">
      <h3 class="section-title">
        <i class="bi bi-list-ul section-icon"></i>
        Appointments list
      </h3>
      <div class="search-bar-wrapper">
        <i class="bi bi-search search-bar-icon"></i>
        <Input
          v-model="searchQuery"
          placeholder="Search by patient, doctor, or date..."
          class="search-bar-input"
        />
      </div>
      <div class="content-card table-card">
        <div v-if="loading" class="content-card-empty">
          <p class="mb-0">Loading...</p>
        </div>
        <div v-else-if="filteredAppointments.length === 0" class="content-card-empty">
          <i class="bi bi-calendar-x empty-icon"></i>
          <p class="mb-0">No appointments</p>
        </div>
        <div v-else class="table-responsive">
          <table class="admin-table">
            <thead>
              <tr>
                <th>Patient</th>
                <th>Doctor</th>
                <th>Date</th>
                <th>Time</th>
                <th>Reason</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in filteredAppointments" :key="a.id">
                <td>{{ a.patientName || a.patient_name || '—' }}</td>
                <td>{{ a.doctorName || a.doctor_name || '—' }}</td>
                <td>{{ a.date || '—' }}</td>
                <td>{{ a.time || '—' }}</td>
                <td>{{ a.reason || '—' }}</td>
                <td>
                  <span class="badge" :class="statusBadgeClass(a.status)">{{ normalizeStatus(a.status) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import StatCard from '@/components/StatCard.vue';
import Input from '@/components/ui/Input.vue';
import api from '@/utils/api.js';
import { appointments as mockAppointments } from '@/data/mockData.js';

const appointments = ref([]);
const loading = ref(false);
const searchQuery = ref('');

const bookedCount = computed(() =>
  appointments.value.filter((a) => normalizeStatus(a.status) === 'booked').length
);
const completedCount = computed(() =>
  appointments.value.filter((a) => normalizeStatus(a.status) === 'completed').length
);
const cancelledCount = computed(() =>
  appointments.value.filter((a) => normalizeStatus(a.status) === 'cancelled').length
);

const filteredAppointments = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return appointments.value;
  const patient = (a) => (a.patientName || a.patient_name || '').toLowerCase();
  const doctor = (a) => (a.doctorName || a.doctor_name || '').toLowerCase();
  const date = (a) => (a.date || '').toString();
  return appointments.value.filter(
    (a) => patient(a).includes(q) || doctor(a).includes(q) || date(a).includes(q)
  );
});

function normalizeStatus(s) {
  if (!s) return '';
  return String(s).toLowerCase();
}

function statusBadgeClass(s) {
  const status = normalizeStatus(s);
  if (status === 'booked') return 'badge-booked';
  if (status === 'completed') return 'badge-completed';
  if (status === 'cancelled') return 'badge-cancelled';
  return 'badge-cancelled';
}

onMounted(async () => {
  loading.value = true;
  try {
    const { data } = await api.get('/api/admin/appointments');
    appointments.value = data || [];
  } catch {
    appointments.value = [...mockAppointments];
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.appointments-page {
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

.section-stats {
  padding: 1.25rem;
}

.admin-stat-cards {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
}

@media (min-width: 768px) {
  .admin-stat-cards {
    grid-template-columns: repeat(3, 1fr);
  }
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

.table-card {
  padding: 1.25rem;
  overflow-x: auto;
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

.admin-table tbody tr:last-child td {
  border-bottom: none;
}

.admin-table tbody tr:hover {
  background: rgba(0, 0, 0, 0.02);
}

.badge-booked {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 0.5rem;
  background: rgba(13, 110, 253, 0.12);
  color: #0d6efd;
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
</style>
