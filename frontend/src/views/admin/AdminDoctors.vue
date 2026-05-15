<template>
  <div class="dashboard-spacing admin-list-page doctors-page">
    <header class="dashboard-header dashboard-header-with-actions">
      <div>
        <h1 class="page-title">Manage Doctors</h1>
        <p class="page-subtitle">Add, edit, or remove doctor profiles</p>
      </div>
      <Button @click="openAddDoctorModal">
        <i class="bi bi-plus-lg me-1"></i>Add Doctor
      </Button>
    </header>

    <section class="section section-table">
      <h3 class="section-title">
        <i class="bi bi-person-badge section-icon"></i>
        Doctors list
      </h3>
      <div class="search-bar-wrapper">
        <i class="bi bi-search search-bar-icon"></i>
        <Input
          v-model="searchQuery"
          placeholder="Search doctors..."
          class="search-bar-input"
        />
      </div>
      <div class="content-card table-card">
        <div v-if="doctorsLoading" class="content-card-empty">
          <p class="mb-0">Loading...</p>
        </div>
        <div v-else-if="filteredDoctors.length === 0" class="content-card-empty">
          <i class="bi bi-person-x empty-icon"></i>
          <p class="mb-0">No doctors</p>
        </div>
        <div v-else class="table-responsive">
          <table class="admin-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Specialization</th>
                <th>Experience</th>
                <th>Phone</th>
                <th>Status</th>
                <th class="admin-table-actions">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in filteredDoctors" :key="d.id">
                <td>
                  <div class="table-cell-with-avatar">
                    <div class="doctor-avatar">
                      {{ (d.name || '').split(' ').pop()?.charAt(0) || '?' }}
                    </div>
                    <span>{{ d.name }}</span>
                  </div>
                </td>
                <td>{{ d.specialization || d.department_name || '—' }}</td>
                <td>{{ (d.experience ?? 0) }}y</td>
                <td>{{ d.phone || d.contact_number || '—' }}</td>
                <td>
                  <span
                    class="badge"
                    :class="!d.is_available ? 'badge-blocked' : 'badge-active'"
                  >
                    {{ d.is_available !== false ? 'Active' : 'Blocked' }}
                  </span>
                </td>
                <td class="admin-table-actions">
                  <div class="action-buttons">
                    <button
                      type="button"
                      class="btn-icon"
                      :class="d.is_available ? 'text-warning' : 'text-success'"
                      :title="d.is_available ? 'Block' : 'Unblock'"
                      @click="toggleBlockDoctor(d)"
                    >
                      <i class="bi" :class="d.is_available ? 'bi-lock-fill' : 'bi-unlock-fill'"></i>
                    </button>
                    <button type="button" class="btn-icon" title="Edit" @click="editDoctor(d)">
                      <i class="bi bi-pencil"></i>
                    </button>
                    <button type="button" class="btn-icon text-danger" title="Delete" @click="removeDoctor(d.id)">
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

    <div class="modal fade" id="addDoctorModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Add Doctor</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <form @submit.prevent="addDoctor">
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">Username</label>
                <input v-model="form.username" type="text" class="form-control" required />
              </div>
              <div class="mb-3">
                <label class="form-label">Email</label>
                <input v-model="form.email" type="email" class="form-control" required />
              </div>
              <div class="mb-3">
                <label class="form-label">Password</label>
                <input v-model="form.password" type="password" class="form-control" placeholder="default doctor123" />
              </div>
              <div class="mb-3">
                <label class="form-label">Full Name</label>
                <input v-model="form.name" type="text" class="form-control" required />
              </div>
              <div class="mb-3">
                <label class="form-label">Department</label>
                <select v-model="form.department_id" class="form-select" required>
                  <option v-for="dept in departments" :key="dept.id" :value="dept.id">{{ dept.name }}</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label">Contact</label>
                <input v-model="form.contact_number" type="text" class="form-control" />
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="submit" class="btn btn-primary">Add Doctor</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Edit Doctor Modal (v-if overlay) -->
    <div v-if="showEditDoctorModal" class="modal-overlay" @click.self="closeEditDoctorModal">
      <div class="modal-edit-doctor">
        <div class="modal-content">
          <div class="modal-header-custom">
            <h5 class="modal-title">Edit Doctor</h5>
            <button type="button" class="btn-close" @click="closeEditDoctorModal" aria-label="Close"></button>
          </div>
          <form v-if="editingDoctor" @submit.prevent="saveDoctorEdit">
            <div class="modal-body">
              <div class="mb-3">
                <label class="form-label">Full Name</label>
                <input v-model="editForm.name" type="text" class="form-control" required />
              </div>
              <div class="mb-3">
                <label class="form-label">Department</label>
                <select v-model="editForm.department_id" class="form-select" required>
                  <option v-for="dept in departments" :key="dept.id" :value="dept.id">{{ dept.name }}</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label">Qualification</label>
                <input v-model="editForm.qualification" type="text" class="form-control" />
              </div>
              <div class="mb-3">
                <label class="form-label">Specialization</label>
                <input v-model="editForm.specialization" type="text" class="form-control" />
              </div>
              <div class="mb-3">
                <label class="form-label">Experience (years)</label>
                <input v-model.number="editForm.experience" type="number" min="0" class="form-control" />
              </div>
              <div class="mb-3">
                <label class="form-label">Contact</label>
                <input v-model="editForm.contact_number" type="text" class="form-control" />
              </div>
              <div class="mb-3">
                <div class="form-check">
                  <input v-model="editForm.is_available" type="checkbox" class="form-check-input" id="editDoctorAvailable" />
                  <label class="form-check-label" for="editDoctorAvailable">Available for appointments</label>
                </div>
              </div>
            </div>
            <div class="modal-footer-custom">
              <button type="button" class="btn btn-secondary" @click="closeEditDoctorModal">Cancel</button>
              <button type="submit" class="btn btn-primary">Save changes</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import Button from '@/components/ui/Button.vue';
import Input from '@/components/ui/Input.vue';
import api from '@/utils/api.js';
import { toast } from '@/utils/toast.js';
// import { doctors as mockDoctors, departments as mockDepartments } from '@/data/mockData.js';
import { useDepartments } from '@/composables/useDepartments.js';
import { useDoctors } from '@/composables/useDoctors.js';

const { departments, loading, fetchDepartments } = useDepartments();
const { doctors, loading: doctorsLoading, fetchDoctors } = useDoctors({ admin: true });

onMounted(() => {
  fetchDepartments();
  fetchDoctors();
});

function openAddDoctorModal() {
  window.bootstrap?.Modal.getOrCreateInstance(document.getElementById('addDoctorModal'))?.show();
}


const searchQuery = ref('');
const form = reactive({
  username: '',
  email: '',
  password: 'doctor123',
  name: '',
  department_id: null,
  contact_number: '',
});

const editingDoctor = ref(null);
const showEditDoctorModal = ref(false);
const editForm = reactive({
  name: '',
  department_id: null,
  qualification: '',
  specialization: '',
  experience: 0,
  contact_number: '',
  is_available: true,
});

const filteredDoctors = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return doctors.value;
  return doctors.value.filter(
    (d) =>
      (d.name || '').toLowerCase().includes(q) ||
      (d.specialization || d.department_name || '').toLowerCase().includes(q) ||
      (d.phone || d.contact_number || '').includes(q)
  );
});

// onMounted(async () => {
//   try {
//     const [dRes, deptRes] = await Promise.all([
//       api.get('/api/admin/doctors'),
//       api.get('/api/admin/departments'),
//     ]);
//     doctors.value = dRes.data || [];
//     departments.value = deptRes.data || [];
//   } catch {
//     doctors.value = [...mockDoctors];
//     departments.value = mockDepartments.map((d) => ({ id: d.id, name: d.name }));
//   }
//   if (departments.value.length && !form.department_id) form.department_id = departments.value[0].id;
// });

async function addDoctor() {
  try {
    await api.post('/api/admin/doctors', form);
    toast('Doctor added');
    const { data } = await api.get('/api/admin/doctors');
    doctors.value = data || doctors.value;
    Object.assign(form, {
      username: '',
      email: '',
      password: 'doctor123',
      name: '',
      department_id: departments.value[0]?.id,
      contact_number: '',
    });
    window.bootstrap?.Modal.getInstance(document.getElementById('addDoctorModal'))?.hide();
  } catch (e) {
    toast(e.response?.data?.message || 'Failed', 'error');
  }
}

function editDoctor(d) {
  editingDoctor.value = d;
  editForm.name = d.name || '';
  editForm.department_id = d.department_id ?? null;
  editForm.qualification = d.qualification || '';
  editForm.specialization = d.specialization || d.department_name || '';
  editForm.experience = d.experience ?? 0;
  editForm.contact_number = d.contact_number || d.phone || '';
  editForm.is_available = d.is_available !== false;
  showEditDoctorModal.value = true;
}

function closeEditDoctorModal() {
  showEditDoctorModal.value = false;
  editingDoctor.value = null;
}

async function saveDoctorEdit() {
  if (!editingDoctor.value) return;
  try {
    await api.put(`/api/admin/doctors/${editingDoctor.value.id}`, {
      name: editForm.name,
      department_id: editForm.department_id,
      qualification: editForm.qualification || null,
      specialization: editForm.specialization || null,
      experience: editForm.experience,
      contact_number: editForm.contact_number || null,
      is_available: editForm.is_available,
    });
    toast('Doctor updated');
    const i = doctors.value.findIndex((x) => x.id === editingDoctor.value.id);
    if (i >= 0) {
      doctors.value[i] = {
        ...doctors.value[i],
        ...editForm,
        phone: editForm.contact_number,
      };
    }
    closeEditDoctorModal();
  } catch (e) {
    toast(e.response?.data?.message || 'Update failed', 'error');
  }
}

async function removeDoctor(id) {
  if (!confirm('Remove this doctor?')) return;
  try {
    await api.delete(`/api/admin/doctors/${id}`);
    toast('Doctor removed');
    doctors.value = doctors.value.filter((d) => d.id !== id);
  } catch (e) {
    toast(e.response?.data?.message || 'Failed', 'error');
  }
}

async function toggleBlockDoctor(d) {
  try {
    const { data } = await api.post(`/api/admin/doctors/${d.id}/block`);
    const updated = data?.doctor;
    if (updated) {
      doctors.value = doctors.value.map((x) => (x.id === updated.id ? { ...x, ...updated } : x));
    }
    toast(updated?.is_available !== false ? 'Doctor unblocked' : 'Doctor blocked');
  } catch (e) {
    toast(e.response?.data?.message || 'Failed', 'error');
  }
}
</script>

<style scoped>
.doctors-page {
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

.dashboard-header-with-actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

@media (min-width: 576px) {
  .dashboard-header-with-actions {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
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

.doctor-avatar {
  width: 2.5rem;
  height: 2.5rem;
  min-width: 2.5rem;
  border-radius: 50%;
  background: rgba(13, 110, 253, 0.12);
  color: #0d6efd;
  font-weight: 600;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  justify-content: center;
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
.modal-edit-doctor {
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.modal-edit-doctor .modal-content {
  background: var(--bs-body-bg);
  border-radius: 1rem;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.15);
  padding: 1.5rem;
  border: 1px solid rgba(0, 0, 0, 0.06);
  overflow-y: auto;
  max-height: 90vh;
}
.modal-header-custom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  flex-shrink: 0;
}
.modal-edit-doctor .modal-body {
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
</style>
