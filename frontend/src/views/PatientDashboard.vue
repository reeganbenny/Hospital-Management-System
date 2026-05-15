<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import StatCard from '@/components/StatCard.vue';
import Input from '@/components/ui/Input.vue';
import Button from '@/components/ui/Button.vue';
import { useAuth } from '@/composables/useAuth.js';
import { appointments, patients } from '@/data/mockData';
import { format, addDays } from 'date-fns';
import { useDepartments } from '@/composables/useDepartments.js';
import { useDoctors } from '@/composables/useDoctors.js';
import { getBookableSlotsForDate } from '@/composables/useBookingSlots.js';
import { useAppointments } from '@/composables/useAppointments.js';
import api from '@/utils/api.js';
import { toast } from '@/utils/toast.js';

const router = useRouter();
const { user } = useAuth();
const { departments, loading: departmentsLoading, fetchDepartments } = useDepartments();
const { doctors, loading: doctorsLoading, fetchDoctors } = useDoctors();
const searchQuery = ref('');
const doctorSearchQuery = ref('');
const patientName = computed(() => user.value?.name || 'Patient');
const { upcomingAppointments, treatments, fetchUpcomingAppointments, fetchTreatments } = useAppointments();

const today = format(new Date(), 'yyyy-MM-dd');

onMounted(async () => {
  await fetchDepartments();
  await fetchDoctors();
  await fetchUpcomingAppointments();
  await fetchTreatments();
  console.log(upcomingAppointments.value);
  console.log(treatments.value);
});

console.log(user.value);
const upcomingAppointmentsList = computed(() =>
  upcomingAppointments.value.filter(
    (a) =>
      a.patient_id === user.value?.patient_id &&
      a.date >= today &&
      a.status === 'Booked'
  )
);

const upcomingCount = computed(() => upcomingAppointmentsList.value.length);

const patientTreatments = computed(() => {
  const p = patients.find((x) => x.name === patientName.value);
  if (!p) return [];
  return treatments.value.filter((t) => t.patientId === p.id);
});

const profileData = computed(() => {
  const p = patients.find((x) => x.email === user.value?.email) || patients.find((x) => x.name === patientName.value);
  return {
    name: user.value?.name || p?.name || '—',
    email: user.value?.email || p?.email || '—',
    phone: p?.phone || user.value?.phone || '—',
    role: (user.value?.role || 'patient').charAt(0).toUpperCase() + (user.value?.role || 'patient').slice(1),
  };
});

function cancelAppointment(id) {
  if (confirm('Cancel this appointment?')) {
    // Demo: would call API
  }
}

function goToEditProfile() {
  router.push('/patient/profile');
}

const pastVisitsCount = computed(() =>
  appointments.filter(
    (a) =>
      a.patientName === patientName.value &&
      a.status === 'completed'
  ).length
);

const filteredDepartments = computed(() => {
  const list = departments?.value ?? [];
  const q = searchQuery.value?.toLowerCase?.()?.trim() || '';
  if (!q) return list;
  return list.filter(
    (d) =>
      d.name.toLowerCase().includes(q) ||
      d.description.toLowerCase().includes(q)
  );
});

const filteredDoctors = computed(() => {
  const list = doctors?.value ?? [];
  const q = doctorSearchQuery.value?.toLowerCase?.()?.trim() || '';
  if (!q) return list;
  return list.filter(
    (d) =>
      (d.name || '').toLowerCase().includes(q) ||
      (d.department_name || d.specialization || d.department?.name || '').toLowerCase().includes(q)
  );
});

const DOCTORS_LIMIT = 4;
const DEPARTMENTS_LIMIT = 4;
/** Show "View more" for departments when there are more than this many */
const DEPARTMENTS_VIEW_MORE_THRESHOLD = 4;

const doctorsExpanded = ref(false);
const departmentsExpanded = ref(false);

const showDoctorsViewMore = computed(() => filteredDoctors.value.length > DOCTORS_LIMIT);
const displayedDoctors = computed(() =>
  doctorsExpanded.value ? filteredDoctors.value : filteredDoctors.value.slice(0, DOCTORS_LIMIT)
);

const showDepartmentsViewMore = computed(() => filteredDepartments.value.length > DEPARTMENTS_VIEW_MORE_THRESHOLD);
const displayedDepartments = computed(() =>
  departmentsExpanded.value ? filteredDepartments.value : filteredDepartments.value.slice(0, DEPARTMENTS_LIMIT)
);

function goToBook() {
  router.push('/patient/book');
}

const showBookingModal = ref(false);
const selectedDoctor = ref(null);
const modalDate = ref('');
const modalSelectedSlot = ref('');
const modalReason = ref('');
const bookingInProgress = ref(false);

const modalSlotsForDate = computed(() =>
  getBookableSlotsForDate(selectedDoctor.value, modalDate.value)
);

function openBookingModal(doc) {
  selectedDoctor.value = doc;
  const slots = doc.availability_slots ?? [];
  modalDate.value = slots[0]?.date || format(new Date(), 'yyyy-MM-dd');
  modalSelectedSlot.value = '';
  modalReason.value = '';
  showBookingModal.value = true;
}

function closeBookingModal() {
  showBookingModal.value = false;
  selectedDoctor.value = null;
  modalDate.value = '';
  modalSelectedSlot.value = '';
  modalReason.value = '';
}

watch(modalDate, () => {
  modalSelectedSlot.value = '';
});

async function confirmBooking() {
  if (!selectedDoctor.value || !modalDate.value || !modalSelectedSlot.value) {
    toast('Please select date and time slot', 'error');
    return;
  }
  bookingInProgress.value = true;
  try {
    await api.post('/api/patient/appointments', {
      doctor_id: selectedDoctor.value.id,
      date: modalDate.value,
      time: modalSelectedSlot.value,
      reason: modalReason.value?.trim() || undefined,
    });
    toast('Appointment booked successfully');
    await fetchDoctors();
    await fetchUpcomingAppointments();
    closeBookingModal();
  } catch (e) {
    toast(e.response?.data?.message || 'Booking failed', 'error');
  } finally {
    bookingInProgress.value = false;
  }
}
</script>

<template>
  <div class="dashboard-spacing patient-dashboard">
    <header class="dashboard-header">
      <h1 class="page-title">Welcome, {{ patientName }}</h1>
      <p class="page-subtitle">Manage your health and appointments</p>
    </header>

    <section class="section section-stats">
      <div class="dashboard-grid patient-stat-cards">
        <StatCard
          title="Upcoming Appointments"
          :value="upcomingCount"
          icon="bi bi-calendar3"
          accent="stat-icon-primary"
        />
        <StatCard
          title="Past Visits"
          :value="pastVisitsCount"
          icon="bi bi-clock-history"
          accent="stat-icon-success"
        />
        <StatCard
          title="Departments"
          :value="(departments ?? []).length"
          icon="bi bi-bandaid"
          accent="stat-icon-teal"
        />
      </div>
    </section>

    <section class="section section-departments">
      <h3 class="section-title">
        <i class="bi bi-building section-icon"></i>
        Specializations & Departments
      </h3>
      <div class="departments-grid patient-departments">
        <div
          v-for="dept in displayedDepartments"
          :key="dept.id"
          class="department-card patient-dept-card"
        >
          <h4 class="dept-name">{{ dept.name }}</h4>
          <p class="dept-desc">{{ dept.description }}</p>
          <p class="dept-doctor-count">
            {{ dept.doctors_count ?? dept.doctorCount ?? 0 }} {{ (dept.doctors_count ?? dept.doctorCount ?? 0) === 1 ? 'doctor' : 'doctors' }} available
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
          Find & Book a Doctor
        </h3>
      </div>
      <div class="search-bar-wrapper">
        <i class="bi bi-search search-bar-icon"></i>
        <Input
          v-model="doctorSearchQuery"
          placeholder="Search by name or specialization..."
          class="search-bar-input"
        />
      </div>
      <div class="doctors-grid">
        <div
          v-for="doc in displayedDoctors"
          :key="doc.id"
          class="doctor-card doctor-card-clickable"
          role="button"
          tabindex="0"
          @click="openBookingModal(doc)"
          @keydown.enter="openBookingModal(doc)"
          @keydown.space.prevent="openBookingModal(doc)"
        >
          <div class="doctor-card-body">
            <div class="doctor-card-avatar">
              {{ doc.name.split(' ').pop().charAt(0) }}
            </div>
            <div class="doctor-card-info">
              <p class="doctor-card-name">{{ doc.name }}</p>
              <p class="doctor-card-meta">
                {{ doc.department_name || doc.qualification }} · {{ doc.experience ?? 0 }}y exp
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
      <div class="dashboard-cards-row patient-cards-row">
        <div class="content-card content-card-appointments">
          <h3 class="content-card-title">
            <i class="bi bi-calendar-check content-card-icon"></i>
            Upcoming Appointments
          </h3>
          <div v-if="upcomingAppointmentsList.length === 0" class="content-card-empty">
            <i class="bi bi-calendar-x empty-icon"></i>
            <p class="mb-0">No upcoming appointments</p>
          </div>
          <div v-else class="appointment-list">
            <div
              v-for="apt in upcomingAppointmentsList"
              :key="apt.id"
              class="appointment-item"
            >
              <div class="appointment-item-main">
                <p class="appointment-doctor">{{ apt.doctor_name }}</p>
                <p class="appointment-meta">{{ apt.date }} · {{ apt.time }} — {{ apt.specialization }}</p>
              </div>
              <div class="appointment-item-actions">
                <span class="badge badge-booked">Booked</span>
                <button
                  type="button"
                  class="btn-cancel"
                  @click="cancelAppointment(apt.id)"
                >
                  <i class="bi bi-x-lg me-1"></i>Cancel
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="content-card content-card-treatments">
          <h3 class="content-card-title">
            <i class="bi bi-file-medical content-card-icon"></i>
            Treatment History
          </h3>
          <div v-if="patientTreatments.length === 0" class="content-card-empty">
            <i class="bi bi-clipboard2-pulse empty-icon"></i>
            <p class="mb-0">No treatment records</p>
          </div>
          <div v-else class="treatment-list">
            <div v-for="t in patientTreatments" :key="t.id" class="treatment-item">
              {{ t.diagnosis }} · {{ t.date }}
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="section section-profile">
      <div class="content-card profile-card">
        <div class="profile-card-header">
          <h3 class="content-card-title mb-0">
            <i class="bi bi-person-circle content-card-icon"></i>
            My Profile
          </h3>
          <Button variant="outline" size="sm" class="btn-edit-profile" @click="goToEditProfile">
            <i class="bi bi-pencil me-1"></i>Edit Profile
          </Button>
        </div>
        <div class="profile-grid">
          <div class="profile-field">
            <p class="profile-label">Name</p>
            <p class="profile-value">{{ profileData.name }}</p>
          </div>
          <div class="profile-field">
            <p class="profile-label">Email</p>
            <p class="profile-value">{{ profileData.email }}</p>
          </div>
          <div class="profile-field">
            <p class="profile-label">Phone</p>
            <p class="profile-value">{{ profileData.phone }}</p>
          </div>
          <div class="profile-field">
            <p class="profile-label">Role</p>
            <p class="profile-value">{{ profileData.role }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Confirm Booking Modal -->
    <div v-if="showBookingModal" class="modal-overlay" @click.self="closeBookingModal">
      <div class="modal-dialog-book">
        <div class="modal-content">
          <div class="modal-header-custom">
            <h5 class="modal-title">Confirm Booking</h5>
            <button type="button" class="btn-close" @click="closeBookingModal" aria-label="Close"></button>
          </div>
          <div v-if="selectedDoctor" class="modal-body">
            <p class="modal-doctor-info">
              {{ selectedDoctor.name }} — {{ selectedDoctor.department_name || selectedDoctor.qualification || 'General Medicine' }}
            </p>
            <div class="mb-3">
              <label class="form-label">Select Date:</label>
              <div class="date-input-wrapper">
                <input
                  v-model="modalDate"
                  type="date"
                  class="form-control date-input"
                  :min="format(new Date(), 'yyyy-MM-dd')"
                  :max="format(addDays(new Date(), 6), 'yyyy-MM-dd')"
                />
                <i class="bi bi-calendar3 date-icon"></i>
              </div>
            </div>
            <div class="mb-4">
              <label class="form-label">Available Slots</label>
              <div class="slots-row">
                <button
                  v-for="slot in modalSlotsForDate"
                  :key="slot"
                  type="button"
                  class="slot-btn-modal"
                  :class="{ 'slot-btn-modal-selected': modalSelectedSlot === slot }"
                  @click="modalSelectedSlot = slot"
                >
                  {{ slot }}
                </button>
              </div>
              <p v-if="modalSlotsForDate.length === 0 && modalDate" class="small text-body-secondary mt-2 mb-0">
                No slots available for this date
              </p>
            </div>
            <div class="mb-4">
              <label class="form-label">Reason (optional)</label>
              <input v-model="modalReason" type="text" class="form-control" placeholder="Reason for visit" />
            </div>
          </div>
          <div class="modal-footer-custom">
            <Button
              :disabled="bookingInProgress || !modalSelectedSlot"
              @click="confirmBooking"
            >
              {{ bookingInProgress ? 'Booking...' : 'Book Appointment' }}
            </Button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.patient-dashboard {
  --section-radius: 1rem;
  --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  --card-shadow-hover: 0 8px 24px rgba(0, 0, 0, 0.08);
  --border-subtle: 1px solid rgba(0, 0, 0, 0.06);
  --accent: #0d6efd;
  --accent-soft: rgba(13, 110, 253, 0.08);
  --teal: #0d9488;
  --teal-soft: rgba(13, 148, 136, 0.1);
}

/* Header */
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

/* Sections */
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

/* Stats */
.section-stats {
  padding: 1.25rem;
}

.patient-stat-cards {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
}

@media (min-width: 768px) {
  .patient-stat-cards {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Departments */
.section-departments .departments-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}

.patient-dept-card {
  background: var(--bs-body-bg);
  border-radius: 0.75rem;
  padding: 1.25rem;
  border: var(--border-subtle);
  box-shadow: var(--card-shadow);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.patient-dept-card:hover {
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

/* Find & Book */
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

.book-appt-btn {
  flex-shrink: 0;
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
  transition: box-shadow 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

.doctor-card-body {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
}

.doctor-card-clickable {
  cursor: pointer;
}

.doctor-card-clickable:hover {
  box-shadow: var(--card-shadow-hover);
  border-color: rgba(13, 110, 253, 0.25);
}

.doctor-card-avatar {
  width: 3.25rem;
  height: 3.25rem;
  border-radius: 0.75rem;
  background: linear-gradient(135deg, var(--accent) 0%, #0a58ca 100%);
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

.doctor-card-clickable:hover .doctor-card-arrow {
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
  border: 1px solid rgba(13, 110, 253, 0.2);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
}

.btn-view-more:hover {
  background: rgba(13, 110, 253, 0.15);
  border-color: rgba(13, 110, 253, 0.35);
}

.btn-view-more:disabled,
.btn-view-more--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-view-more:disabled:hover,
.btn-view-more--disabled:hover {
  background: var(--accent-soft);
  border-color: rgba(13, 110, 253, 0.2);
}

/* Content cards row */
.section-cards {
  padding: 1.5rem;
}

.patient-cards-row {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: 1fr;
}

@media (min-width: 768px) {
  .patient-cards-row {
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
.treatment-list {
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
  padding: 0.75rem 0;
  border-bottom: var(--border-subtle);
  font-size: 0.9375rem;
  color: var(--bs-body-color);
}

.treatment-item:last-child {
  border-bottom: none;
}

/* Profile */
.section-profile .content-card {
  margin-bottom: 0;
}

.profile-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.profile-grid {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(1, 1fr);
}

@media (min-width: 576px) {
  .profile-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 768px) {
  .profile-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.profile-field {
  min-width: 0;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 0.5rem;
  border: var(--border-subtle);
}

.profile-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--bs-secondary-color);
  margin: 0 0 0.35rem 0;
}

.profile-value {
  font-size: 0.9375rem;
  font-weight: 500;
  margin: 0;
  color: var(--bs-body-color);
}

.btn-edit-profile {
  flex-shrink: 0;
}

/* Modal */
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
  padding-top: 1rem;
}
</style>
