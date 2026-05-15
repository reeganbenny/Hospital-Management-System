<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import StatCard from '@/components/StatCard.vue';
import Button from '@/components/ui/Button.vue';
import Input from '@/components/ui/Input.vue';
import { useDepartments } from '@/composables/useDepartments.js';
import { useDoctors } from '@/composables/useDoctors.js';
import api from '@/utils/api.js';
import { patients } from '@/data/mockData';

const router = useRouter();
const { departments, fetchDepartments } = useDepartments();
const { doctors, fetchDoctors } = useDoctors();

const dashboardStats = ref({
  doctors_count: 0,
  patients_count: 0,
  appointments_count: 0,
  upcoming_appointments: 0,
});
const dashboardLoading = ref(false);
const appointmentsLoading = ref(false);
const appointmentsList = ref([]);
const searchQuery = ref('');

const today = new Date().toISOString().split('T')[0];

onMounted(async () => {
  await fetchDepartments();
  await fetchDoctors();
  dashboardLoading.value = true;
  try {
    const { data } = await api.get('/api/admin/dashboard');
    dashboardStats.value = data || dashboardStats.value;
  } catch (err) {
    dashboardStats.value = {
      doctors_count: doctors.value?.length ?? 0,
      patients_count: patients?.length ?? 0,
      appointments_count: appointmentsList.value?.length ?? 0,
      upcoming_appointments: 0,
    };
  } finally {
    dashboardLoading.value = false;
  }

  appointmentsLoading.value = true;
  try {
    const { data } = await api.get('/api/admin/appointments');
    appointmentsList.value = Array.isArray(data) ? data : [];
  } catch (_) {
    appointmentsList.value = [];
  } finally {
    appointmentsLoading.value = false;
  }
});

const todayAppointments = computed(() =>
  (appointmentsList.value || []).filter((a) => a.date === today)
);

const filteredDoctors = computed(() => {
  const list = doctors?.value ?? [];
  const q = searchQuery.value?.toLowerCase?.()?.trim() || '';
  if (!q) return list;
  return list.filter(
    (d) =>
      (d.name || '').toLowerCase().includes(q) ||
      (d.specialization || d.department_name || '').toLowerCase().includes(q)
  );
});

const DOCTORS_LIMIT = 4;
const doctorsExpanded = ref(false);
const showDoctorsViewMore = computed(() => filteredDoctors.value.length > DOCTORS_LIMIT);
const displayedDoctors = computed(() =>
  doctorsExpanded.value ? filteredDoctors.value : filteredDoctors.value.slice(0, DOCTORS_LIMIT)
);

const DEPARTMENTS_LIMIT = 4;
const departmentsExpanded = ref(false);
const displayedDepartments = computed(() =>
  departmentsExpanded.value
    ? (departments?.value ?? [])
    : (departments?.value ?? []).slice(0, DEPARTMENTS_LIMIT)
);
const showDepartmentsViewMore = computed(() => (departments?.value ?? []).length > DEPARTMENTS_LIMIT);

function statusClass(s) {
  if (s === 'booked' || s === 'Booked') return 'badge-booked';
  if (s === 'completed' || s === 'Completed') return 'badge-completed';
  return 'badge-cancelled';
}

function goToDoctors() {
  router.push('/admin/doctors');
}

function goToPatients() {
  router.push('/admin/patients');
}

function goToAppointments() {
  router.push('/admin/appointments');
}
</script>

<template>
  <div class="dashboard-spacing admin-dashboard">
    <header class="dashboard-header">
      <h1 class="page-title">Admin Dashboard</h1>
      <p class="page-subtitle">Hospital overview and management</p>
    </header>

    <section class="section section-stats">
      <div class="dashboard-grid admin-stat-cards">
        <StatCard
          v-if="!dashboardLoading"
          title="Total Doctors"
          :value="dashboardStats.doctors_count"
          icon="bi bi-heart-pulse"
          accent="stat-icon-primary"
        />
        <StatCard
          v-if="!dashboardLoading"
          title="Total Patients"
          :value="dashboardStats.patients_count"
          icon="bi bi-people"
          accent="stat-icon-primary"
        />
        <StatCard
          v-if="!dashboardLoading"
          title="Active Appointments"
          :value="dashboardStats.appointments_count"
          icon="bi bi-calendar3"
          accent="stat-icon-warning"
        />
        <StatCard
          v-if="!dashboardLoading"
          title="Upcoming"
          :value="dashboardStats.upcoming_appointments"
          icon="bi bi-graph-up-arrow"
          accent="stat-icon-success"
        />
      </div>
    </section>

    <section class="section section-departments">
      <h3 class="section-title">
        <i class="bi bi-building section-icon"></i>
        Departments
      </h3>
      <div class="departments-grid admin-departments">
        <div
          v-for="dept in displayedDepartments"
          :key="dept.id"
          class="department-card admin-dept-card"
        >
          <h4 class="dept-name">{{ dept.name }}</h4>
          <p class="dept-desc">{{ dept.description }}</p>
          <p class="dept-doctor-count">
            {{ dept.doctors_count ?? 0 }} {{ (dept.doctors_count ?? 0) === 1 ? 'doctor' : 'doctors' }}
          </p>
        </div>
      </div>
      <div class="view-more-wrap">
        <button
          type="button"
          class="btn-view-more"
          :class="{ 'btn-view-more--disabled': !showDepartmentsViewMore }"
          :disabled="!showDepartmentsViewMore"
          @click="showDepartmentsViewMore && (departmentsExpanded = !departmentsExpanded)"
        >
          {{ departmentsExpanded ? 'View less' : 'View more' }}
          <i class="bi" :class="departmentsExpanded ? 'bi-chevron-up' : 'bi-chevron-down'" style="margin-left: 0.25rem;"></i>
        </button>
      </div>
    </section>

    <section class="section section-doctors">
      <div class="find-book-header">
        <h3 class="section-title mb-0">
          <i class="bi bi-person-badge section-icon"></i>
          Doctors
        </h3>
        <Button size="sm" class="book-appt-btn" @click="goToDoctors">
          <i class="bi bi-plus-lg me-1"></i>Add Doctor
        </Button>
      </div>
      <div class="search-bar-wrapper">
        <i class="bi bi-search search-bar-icon"></i>
        <Input
          v-model="searchQuery"
          placeholder="Search by name or specialization..."
          class="search-bar-input"
        />
      </div>
      <div class="doctors-grid">
        <div
          v-for="doc in displayedDoctors"
          :key="doc.id"
          class="doctor-card doctor-card-admin"
          role="button"
          tabindex="0"
          @click="goToDoctors"
          @keydown.enter="goToDoctors"
          @keydown.space.prevent="goToDoctors"
        >
          <div class="doctor-card-body">
            <div class="doctor-card-avatar">
              {{ (doc.name || '?').split(' ').pop().charAt(0) }}
            </div>
            <div class="doctor-card-info">
              <p class="doctor-card-name">{{ doc.name }}</p>
              <p class="doctor-card-meta">
                {{ doc.specialization || doc.department_name || '—' }} · {{ doc.experience ?? 0 }}y exp
              </p>
            </div>
            <i class="bi bi-chevron-right doctor-card-arrow"></i>
          </div>
        </div>
      </div>
      <div class="view-more-wrap">
        <button
          type="button"
          class="btn-view-more"
          :class="{ 'btn-view-more--disabled': !showDoctorsViewMore }"
          :disabled="!showDoctorsViewMore"
          @click="showDoctorsViewMore && (doctorsExpanded = !doctorsExpanded)"
        >
          {{ doctorsExpanded ? 'View less' : 'View more' }}
          <i class="bi" :class="doctorsExpanded ? 'bi-chevron-up' : 'bi-chevron-down'" style="margin-left: 0.25rem;"></i>
        </button>
      </div>
    </section>

    <section class="section section-cards">
      <div class="dashboard-cards-row admin-cards-row">
        <div class="content-card content-card-appointments">
          <h3 class="content-card-title">
            <i class="bi bi-calendar-check content-card-icon"></i>
            Today's Appointments
          </h3>
          <div v-if="appointmentsLoading" class="content-card-empty">
            <p class="mb-0">Loading...</p>
          </div>
          <div v-else-if="todayAppointments.length === 0" class="content-card-empty">
            <i class="bi bi-calendar-x empty-icon"></i>
            <p class="mb-0">No appointments today</p>
          </div>
          <div v-else class="appointment-list">
            <div
              v-for="apt in todayAppointments"
              :key="apt.id"
              class="appointment-item"
            >
              <div class="appointment-item-main">
                <p class="appointment-doctor">{{ apt.patientName || apt.patient_name }}</p>
                <p class="appointment-meta">{{ apt.doctorName || apt.doctor_name }} · {{ apt.time }}</p>
              </div>
              <span class="badge" :class="statusClass(apt.status)">{{ apt.status }}</span>
            </div>
          </div>
          <Button variant="outline" size="sm" class="mt-3 w-100" @click="goToAppointments">
            View all appointments
          </Button>
        </div>

        <div class="content-card content-card-quick">
          <h3 class="content-card-title">
            <i class="bi bi-link-45deg content-card-icon"></i>
            Quick actions
          </h3>
          <div class="quick-actions-list">
            <button type="button" class="quick-action-item" @click="goToDoctors">
              <i class="bi bi-heart-pulse"></i>
              <span>Manage Doctors</span>
              <i class="bi bi-chevron-right"></i>
            </button>
            <button type="button" class="quick-action-item" @click="goToPatients">
              <i class="bi bi-people"></i>
              <span>Manage Patients</span>
              <i class="bi bi-chevron-right"></i>
            </button>
            <button type="button" class="quick-action-item" @click="goToAppointments">
              <i class="bi bi-calendar3"></i>
              <span>Appointments</span>
              <i class="bi bi-chevron-right"></i>
            </button>
            <button type="button" class="quick-action-item" @click="router.push('/admin/search')">
              <i class="bi bi-search"></i>
              <span>Search</span>
              <i class="bi bi-chevron-right"></i>
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="section section-table">
      <h3 class="section-title">
        <i class="bi bi-list-ul section-icon"></i>
        All Appointments
      </h3>
      <div class="content-card table-card">
        <div v-if="appointmentsLoading" class="content-card-empty">
          <p class="mb-0">Loading...</p>
        </div>
        <div v-else-if="!appointmentsList.length" class="content-card-empty">
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
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="apt in appointmentsList.slice(0, 10)" :key="apt.id">
                <td>{{ apt.patientName || apt.patient_name }}</td>
                <td>{{ apt.doctorName || apt.doctor_name }}</td>
                <td>{{ apt.date }}</td>
                <td>{{ apt.time }}</td>
                <td><span class="badge" :class="statusClass(apt.status)">{{ apt.status }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
        <Button v-if="appointmentsList.length > 10" variant="outline" size="sm" class="mt-3 w-100" @click="goToAppointments">
          View all {{ appointmentsList.length }} appointments
        </Button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.admin-dashboard {
  --section-radius: 1rem;
  --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  --card-shadow-hover: 0 8px 24px rgba(0, 0, 0, 0.08);
  --border-subtle: 1px solid rgba(0, 0, 0, 0.06);
  --accent: #102c48;
  --accent-soft: rgba(16, 44, 72, 0.08);
  --teal: #40e0d0;
  --teal-soft: rgba(64, 224, 208, 0.12);
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
  margin-bottom: 1.25rem;
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
    grid-template-columns: repeat(4, 1fr);
  }
}

.section-departments .departments-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}

.admin-dept-card {
  background: var(--bs-body-bg);
  border-radius: 0.75rem;
  padding: 1.25rem;
  border: var(--border-subtle);
  box-shadow: var(--card-shadow);
  transition: box-shadow 0.2s ease;
}

.admin-dept-card:hover {
  box-shadow: var(--card-shadow-hover);
}

.dept-name {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.35rem 0;
  color: var(--bs-body-color);
}

.dept-desc {
  font-size: 0.875rem;
  color: var(--bs-secondary-color);
  margin: 0 0 0.75rem 0;
  line-height: 1.4;
}

.dept-doctor-count {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--teal);
  margin: 0;
}

.section-doctors .find-book-header {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

@media (min-width: 576px) {
  .section-doctors .find-book-header {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
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

.doctors-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: 1fr;
}

@media (min-width: 768px) {
  .doctors-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.doctor-card {
  background: var(--bs-body-bg);
  border-radius: 0.75rem;
  border: var(--border-subtle);
  box-shadow: var(--card-shadow);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.doctor-card-body {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
}

.doctor-card-admin {
  cursor: pointer;
}

.doctor-card-admin:hover {
  box-shadow: var(--card-shadow-hover);
  border-color: rgba(16, 44, 72, 0.2);
}

.doctor-card-avatar {
  width: 3.25rem;
  height: 3.25rem;
  border-radius: 0.75rem;
  background: var(--accent);
  color: #fff;
  font-weight: 700;
  font-size: 1.125rem;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.doctor-card-info {
  flex: 1;
  min-width: 0;
}

.doctor-card-name {
  font-weight: 600;
  font-size: 1rem;
  margin: 0 0 0.2rem 0;
  color: var(--bs-body-color);
}

.doctor-card-meta {
  font-size: 0.8125rem;
  color: var(--bs-secondary-color);
  margin: 0;
}

.doctor-card-arrow {
  font-size: 1.25rem;
  color: var(--bs-secondary-color);
  opacity: 0.6;
  flex-shrink: 0;
}

.doctor-card-admin:hover .doctor-card-arrow {
  color: var(--accent);
  opacity: 1;
}

.view-more-wrap {
  display: flex;
  justify-content: center;
  margin-top: 1.25rem;
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
  border: 1px solid rgba(16, 44, 72, 0.2);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
}

.btn-view-more:hover:not(:disabled) {
  background: rgba(16, 44, 72, 0.12);
  border-color: rgba(16, 44, 72, 0.3);
}

.btn-view-more:disabled,
.btn-view-more--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.section-cards {
  padding: 1.5rem;
}

.admin-cards-row {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: 1fr;
}

@media (min-width: 768px) {
  .admin-cards-row {
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

.appointment-list {
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

.appointment-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.appointment-item:first-child {
  padding-top: 0;
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

.quick-actions-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.quick-action-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 1rem 0;
  border: none;
  border-bottom: var(--border-subtle);
  background: none;
  text-align: left;
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--bs-body-color);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.quick-action-item:last-child {
  border-bottom: none;
}

.quick-action-item i:first-child {
  font-size: 1.25rem;
  color: var(--accent);
  opacity: 0.9;
}

.quick-action-item span {
  flex: 1;
}

.quick-action-item i:last-child {
  font-size: 1rem;
  color: var(--bs-secondary-color);
  opacity: 0.7;
}

.quick-action-item:hover {
  background: rgba(0, 0, 0, 0.03);
  color: var(--accent);
}

.quick-action-item:hover i:last-child {
  color: var(--accent);
  opacity: 1;
}

.section-table .section-title {
  margin-bottom: 1rem;
}

.table-card {
  padding: 1.25rem;
  overflow-x: auto;
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
</style>
