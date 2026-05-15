<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import Input from '@/components/ui/Input.vue';
import Button from '@/components/ui/Button.vue';
import { useDoctors } from '@/composables/useDoctors.js';
import { useDepartments } from '@/composables/useDepartments.js';
import { getBookableSlotsForDate } from '@/composables/useBookingSlots.js';
import { format, addDays } from 'date-fns';
import api from '@/utils/api.js';
import { toast } from '@/utils/toast.js';

const doctorSearchQuery = ref('');
const { departments, loading: departmentsLoading, fetchDepartments } = useDepartments();
const { doctors, loading: doctorsLoading, fetchDoctors } = useDoctors();
const showBookingModal = ref(false);
const selectedDoctor = ref(null);
const modalDate = ref('');
const modalSelectedSlot = ref('');
const modalReason = ref('');
const error = ref('');
const bookingInProgress = ref(false);

const filteredDoctors = computed(() => {
  const list = doctors?.value ?? [];
  const q = doctorSearchQuery.value?.toLowerCase?.()?.trim() || '';
  if (!q) return list;
  return list.filter(
    (d) =>
      (d.name || '').toLowerCase().includes(q) ||
      (d.department_name || d.specialization || '').toLowerCase().includes(q)
  );
});

const DOCTORS_LIMIT = 4;
const DEPARTMENTS_LIMIT = 4;
const DEPARTMENTS_VIEW_MORE_THRESHOLD = 4;

const doctorsExpanded = ref(false);
const departmentsExpanded = ref(false);

const showDoctorsViewMore = computed(() => filteredDoctors.value.length > DOCTORS_LIMIT);
const displayedDoctors = computed(() =>
  doctorsExpanded.value ? filteredDoctors.value : filteredDoctors.value.slice(0, DOCTORS_LIMIT)
);

const filteredDepartments = computed(() => departments?.value ?? []);
const showDepartmentsViewMore = computed(() => filteredDepartments.value.length > DEPARTMENTS_VIEW_MORE_THRESHOLD);
const displayedDepartments = computed(() =>
  departmentsExpanded.value ? filteredDepartments.value : filteredDepartments.value.slice(0, DEPARTMENTS_LIMIT)
);

const modalSlotsForDate = computed(() =>
  getBookableSlotsForDate(selectedDoctor.value, modalDate.value)
);

onMounted(async () => {
  await fetchDepartments();
  await fetchDoctors();
});

function openBookingModal(doc) {
  selectedDoctor.value = doc;
  const slots = doc.availability_slots ?? [];
  modalDate.value = slots[0]?.date || format(new Date(), 'yyyy-MM-dd');
  modalSelectedSlot.value = '';
  modalReason.value = '';
  error.value = '';
  showBookingModal.value = true;
}

function closeBookingModal() {
  showBookingModal.value = false;
  selectedDoctor.value = null;
  modalDate.value = '';
  modalSelectedSlot.value = '';
  modalReason.value = '';
  error.value = '';
}

watch(modalDate, () => {
  modalSelectedSlot.value = '';
});

async function confirmBooking() {
  error.value = '';
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
    closeBookingModal();
  } catch (e) {
    error.value = e.response?.data?.message || 'Booking failed';
    toast(error.value, 'error');
  } finally {
    bookingInProgress.value = false;
  }
}
</script>

<template>
  <div class="dashboard-spacing book-appointment-page">
    <header class="dashboard-header">
      <h1 class="page-title">Book Appointment</h1>
      <p class="page-subtitle">Find a doctor and schedule your visit.</p>
    </header>

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
                {{ doc.department_name || doc.qualification || doc.specialization }} · {{ doc.experience ?? 0 }}y exp
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
              {{ selectedDoctor.name }} — {{ selectedDoctor.department_name || selectedDoctor.specialization || 'General Medicine' }}
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
            <div class="mb-3">
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
            <p v-if="error" class="text-danger small mb-2">{{ error }}</p>
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
/* Design tokens – match PatientDashboard */
.book-appointment-page {
  --section-radius: 1rem;
  --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  --card-shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.08);
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

/* Confirm Booking Modal */
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
