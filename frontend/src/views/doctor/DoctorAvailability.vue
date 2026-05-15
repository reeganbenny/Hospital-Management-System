<template>
  <div class="dashboard-spacing">
    <div class="availability-header">
      <div>
        <h1 class="page-title">My Availability</h1>
        <p class="page-subtitle">Manage your consultation slots for the next 7 days</p>
      </div>
      <Button @click="saveAvailability" :disabled="saving">
        <i class="bi bi-check-lg me-1"></i>{{ saving ? 'Saving...' : 'Save Availability' }}
      </Button>
    </div>

    <div
      v-for="day in next7Days"
      :key="day.dateStr"
      class="day-card"
    >
      <div class="day-card-header">
        <span class="day-label">
          <i class="bi bi-clock me-2"></i>{{ day.label }}
        </span>
        <div class="day-header-right">
          <label class="apply-checkbox">
            <input
              v-model="applyForComingWeeks[day.dateStr]"
              type="checkbox"
            />
            Apply for coming weeks
          </label>
          <span class="day-slots-count">{{ day.selectedCount }} slots</span>
        </div>
      </div>
      <div class="slots-row">
        <button
          v-for="slot in allSlots"
          :key="slot"
          type="button"
          class="slot-btn"
          :class="slotClass(day.dateStr, slot)"
          @click="toggleSlot(day.dateStr, slot)"
        >
          {{ slot }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue';
import Button from '@/components/ui/Button.vue';
import { format, addDays } from 'date-fns';
import api from '@/utils/api.js';
import { toast } from '@/utils/toast.js';

const ALL_SLOTS = [
  '08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00',
  '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00'
];

const allSlots = ALL_SLOTS;
const selectedSlots = reactive({});
const slotsByDate = reactive({});
const applyForComingWeeks = reactive(
  Object.fromEntries(
    Array.from({ length: 7 }, (_, i) => [format(addDays(new Date(), i), 'yyyy-MM-dd'), false])
  )
);
const saving = ref(false);

const next7Days = computed(() => {
  return Array.from({ length: 7 }, (_, i) => {
    const d = addDays(new Date(), i);
    const dateStr = format(d, 'yyyy-MM-dd');
    const label = format(d, 'EEEE, MMM d');
    const selected = selectedSlots[dateStr] || [];
    const selectedCount = selected.length;
    return {
      dateStr,
      label,
      date: d,
      selectedCount,
      selected,
    };
  });
});

function isSelected(dateStr, time) {
  const list = selectedSlots[dateStr];
  return list ? list.includes(time) : false;
}

function slotClass(dateStr, slot) {
  const status = slotsByDate[dateStr]?.[slot];
  if (status === 'booked') return 'slot-btn-booked';
  if (status === 'available' || isSelected(dateStr, slot)) return 'slot-btn-selected';
  return '';
}

function toggleSlot(dateStr, time) {
  const status = slotsByDate[dateStr]?.[time];
  if (status === 'booked') return;
  if (!selectedSlots[dateStr]) selectedSlots[dateStr] = [];
  const list = selectedSlots[dateStr];
  const idx = list.indexOf(time);
  if (idx >= 0) {
    list.splice(idx, 1);
  } else {
    list.push(time);
    list.sort();
  }
}

function add30Min(t) {
  const [h, m] = t.split(':').map(Number);
  const total = h * 60 + m + 30;
  const nh = Math.floor(total / 60) % 24;
  const nm = total % 60;
  return `${String(nh).padStart(2, '0')}:${String(nm).padStart(2, '0')}`;
}

function serializeSlots() {
  return next7Days.value
    .filter((d) => (selectedSlots[d.dateStr] || []).length > 0)
    .flatMap((d) =>
      (selectedSlots[d.dateStr] || []).map((t) => ({
        date: d.dateStr,
        start_time: t,
        end_time: add30Min(t),
      }))
    );
}

function buildApplyRecurring() {
  const out = {};
  for (const d of next7Days.value) {
    out[d.dateStr] = !!applyForComingWeeks[d.dateStr];
  }
  return out;
}

async function saveAvailability() {
  const slots = serializeSlots();
  if (slots.length === 0) {
    toast('Select at least one slot', 'info');
    return;
  }
  saving.value = true;
  try {
    await api.post('/api/doctor/availability', {
      slots,
      applyRecurring: buildApplyRecurring(),
    });
    toast('Availability saved');
  } catch (e) {
    toast(e.response?.data?.message || 'Failed', 'error');
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  try {
    const { data: detailed } = await api.get('/api/doctor/availability', { params: { detailed: 1 } });
    if (detailed?.slots_by_date && typeof detailed.slots_by_date === 'object') {
      for (const [dateStr, bySlot] of Object.entries(detailed.slots_by_date)) {
        slotsByDate[dateStr] = bySlot;
        const inSchedule = Object.entries(bySlot || {})
          .filter(([, status]) => status === 'available' || status === 'booked')
          .map(([t]) => t);
        selectedSlots[dateStr] = [...inSchedule].sort();
      }
    } else {
      const { data } = await api.get('/api/doctor/availability');
      if (data && typeof data === 'object') {
        for (const [dateStr, times] of Object.entries(data)) {
          if (Array.isArray(times)) {
            selectedSlots[dateStr] = [...times];
          }
        }
      }
    }
  } catch (_) {
    const today = format(new Date(), 'yyyy-MM-dd');
    selectedSlots[today] = ['09:00', '09:30', '10:00', '10:30', '14:00', '14:30'];
  }
});
</script>

<style scoped>
.availability-header {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

@media (min-width: 768px) {
  .availability-header {
    flex-direction: row;
    align-items: flex-start;
    justify-content: space-between;
  }
}

.day-card {
  background: var(--bs-body-bg);
  border: 1px solid var(--bs-border-color);
  border-radius: 0.5rem;
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.day-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.day-header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.apply-checkbox {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8125rem;
  color: var(--bs-secondary-color);
  margin-bottom: 0;
  cursor: pointer;
}

.day-label {
  font-weight: 500;
  display: flex;
  align-items: center;
}

.day-slots-count {
  font-size: 0.875rem;
  color: var(--bs-secondary-color);
}

.slots-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.slot-btn {
  padding: 0.35rem 0.75rem;
  font-size: 0.8125rem;
  border-radius: 0.375rem;
  border: 1px solid var(--bs-border-color);
  background: var(--bs-light);
  color: var(--bs-body-color);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.slot-btn:hover {
  background: #e9ecef;
  border-color: #dee2e6;
}

.slot-btn-selected {
  background: #0d6efd;
  border-color: #0d6efd;
  color: white;
}

.slot-btn-selected:hover {
  background: #0b5ed7;
  border-color: #0a58ca;
  color: white;
}

.slot-btn-booked {
  background: rgba(25, 135, 84, 0.15);
  border-color: #198754;
  color: #198754;
  cursor: default;
}

.slot-btn-booked:hover {
  background: rgba(25, 135, 84, 0.2);
  border-color: #198754;
  color: #198754;
}
</style>
