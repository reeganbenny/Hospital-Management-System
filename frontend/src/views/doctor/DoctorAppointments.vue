<template>
  <div class="dashboard-spacing">
    <div class="page-header">
      <h1 class="page-title">My Appointments</h1>
      <p class="page-subtitle">View and manage your patient appointments</p>
    </div>

    <div class="stat-cards-grid">
      <div class="stat-card-simple">
        <p class="stat-card-simple-title">Today</p>
        <p class="stat-card-simple-value">{{ todayCount }}</p>
      </div>
      <div class="stat-card-simple">
        <p class="stat-card-simple-title">Upcoming</p>
        <p class="stat-card-simple-value">{{ upcomingCount }}</p>
      </div>
      <div class="stat-card-simple">
        <p class="stat-card-simple-title">Completed</p>
        <p class="stat-card-simple-value">{{ completedCount }}</p>
      </div>
      <div class="stat-card-simple">
        <p class="stat-card-simple-title">Cancelled</p>
        <p class="stat-card-simple-value">{{ cancelledCount }}</p>
      </div>
    </div>

    <section class="all-appointments">
      <h3 class="section-title">All Appointments</h3>
      <div v-if="displayedAppointments.length === 0" class="empty-state">
        No appointments
      </div>
      <div
        v-for="apt in displayedAppointments"
        :key="apt.id"
        class="appointment-card appointment-card-clickable"
        role="button"
        tabindex="0"
        @click="goToAppointmentDetail(apt.id)"
        @keydown.enter="goToAppointmentDetail(apt.id)"
        @keydown.space.prevent="goToAppointmentDetail(apt.id)"
      >
        <div class="appointment-info">
          <p class="appointment-patient">{{ apt.patientName || apt.patient_name }}</p>
          <p class="appointment-details">
            {{ apt.date }} • {{ apt.time }} – {{ apt.reason || 'No reason' }}
          </p>
        </div>
        <div class="appointment-actions" @click.stop>
          <span
            class="badge"
            :class="
              isCompleted(apt)
                ? 'badge-completed'
                : (apt.status || '').toLowerCase() === 'cancelled'
                ? 'badge-cancelled'
                : 'badge-booked'
            "
          >
            {{ isCompleted(apt) ? 'completed' : (apt.status || 'booked').toLowerCase() }}
          </span>
          <Button
            v-if="(apt.status || '').toLowerCase() === 'booked' && !isCompleted(apt)"
            size="sm"
            variant="outline"
            @click="completeAppointment(apt.id)"
          >
            <i class="bi bi-check-lg me-1"></i>Complete
          </Button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import Button from '@/components/ui/Button.vue';
import { useAuth } from '@/composables/useAuth.js';
import { appointments as mockAppointments } from '@/data/mockData';
import api from '@/utils/api.js';
import { format } from 'date-fns';

const { user } = useAuth();
const router = useRouter();
const doctorName = computed(() => user.value?.name || 'Doctor');
const today = format(new Date(), 'yyyy-MM-dd');
const appointments = ref([]);
const completedIds = ref(new Set());
const useMockData = ref(false);

const myAppointments = computed(() => {
  const list = useMockData.value
    ? mockAppointments.filter(
        (a) =>
          a.doctorName === doctorName.value
      )
    : appointments.value;
  return list;
});

const todayCount = computed(() =>
  myAppointments.value.filter((a) => a.date === today).length
);

const isCompleted = (a) =>
  (a.status || '').toLowerCase() === 'completed' || completedIds.value.has(a.id);

const upcomingCount = computed(() =>
  myAppointments.value.filter(
    (a) => a.date >= today && (a.status || '').toLowerCase() === 'booked' && !isCompleted(a)
  ).length
);

const completedCount = computed(() => {
  const fromData = myAppointments.value.filter((a) => (a.status || '').toLowerCase() === 'completed');
  return fromData.length + completedIds.value.size;
});

const cancelledCount = computed(() =>
  myAppointments.value.filter((a) => (a.status || '').toLowerCase() === 'cancelled').length
);

const displayedAppointments = computed(() =>
  [...myAppointments.value].sort((a, b) => {
    const d = a.date.localeCompare(b.date);
    return d !== 0 ? d : (a.time || '').localeCompare(b.time || '');
  })
);

onMounted(async () => {
  try {
    const { data } = await api.get('/api/doctor/appointments');
    appointments.value = Array.isArray(data) ? data : [];
  } catch (_) {
    useMockData.value = true;
  }
});

function completeAppointment(id) {
  completedIds.value = new Set([...completedIds.value, id]);
}

function goToAppointmentDetail(id) {
  router.push(`/doctor/appointments/${id}`);
}
</script>

<style scoped>
.stat-cards-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

@media (min-width: 768px) {
  .stat-cards-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.stat-card-simple {
  background: var(--bs-body-bg);
  border: 1px solid var(--bs-border-color);
  border-radius: 0.5rem;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.stat-card-simple-title {
  font-size: 0.875rem;
  color: var(--bs-secondary-color);
  margin-bottom: 0.25rem;
}

.stat-card-simple-value {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.all-appointments {
  margin-top: 0.5rem;
}

.appointment-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bs-body-bg);
  border: 1px solid var(--bs-border-color);
  border-radius: 0.5rem;
  padding: 1rem 1.25rem;
  margin-bottom: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.appointment-card-clickable {
  cursor: pointer;
  transition: background 0.15s, box-shadow 0.15s;
}

.appointment-card-clickable:hover {
  background: rgba(0, 0, 0, 0.02);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.appointment-patient {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.appointment-details {
  font-size: 0.875rem;
  color: var(--bs-secondary-color);
  margin-bottom: 0;
}

.appointment-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.badge-booked {
  background: rgba(13, 110, 253, 0.15);
  color: #0d6efd;
  padding: 0.35em 0.65em;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
}

.badge-completed {
  background: rgba(25, 135, 84, 0.15);
  color: #198754;
  padding: 0.35em 0.65em;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
}

.badge-cancelled {
  background: rgba(108, 117, 125, 0.15);
  color: #6c757d;
  padding: 0.35em 0.65em;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
}

.empty-state {
  color: var(--bs-secondary-color);
  padding: 2rem;
  text-align: center;
}
</style>
