<template>
  <div class="dashboard-spacing patient-profile-page">
    <header class="dashboard-header">
      <h1 class="page-title">Profile</h1>
      <p class="page-subtitle">Update your details</p>
    </header>

    <section class="section section-profile">
      <div class="content-card profile-card profile-form-wrap">
        <h3 class="content-card-title">
          <i class="bi bi-person-circle content-card-icon"></i>
          Edit Profile
        </h3>
        <form class="profile-form" @submit.prevent="save">
          <div class="profile-form-grid">
            <div class="profile-form-field">
              <label class="form-label">Full Name</label>
              <input v-model="form.name" type="text" class="form-control profile-input" placeholder="Your full name" />
            </div>
            <div class="profile-form-field">
              <label class="form-label">Contact</label>
              <input v-model="form.contact_number" type="text" class="form-control profile-input" placeholder="Phone number" />
            </div>
            <div class="profile-form-field profile-form-field-full">
              <label class="form-label">Address</label>
              <textarea v-model="form.address" class="form-control profile-input" rows="2" placeholder="Address"></textarea>
            </div>
            <div class="profile-form-field">
              <label class="form-label">Blood group</label>
              <select v-model="form.blood_group" class="form-control profile-input profile-select">
                <option value="">Select blood group</option>
                <option v-for="bg in bloodGroups" :key="bg" :value="bg">{{ bg }}</option>
              </select>
            </div>
            <div class="profile-form-field">
              <label class="form-label">Date of birth</label>
              <input v-model="form.date_of_birth" type="date" class="form-control profile-input" />
            </div>
          </div>
          <div class="profile-form-actions">
            <button type="submit" class="btn-save">
              Save
            </button>
          </div>
        </form>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue';
import api from '@/utils/api.js';
import { toast } from '@/utils/toast.js';
import { useAuth } from '@/composables/useAuth.js';

const bloodGroups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const { user } = useAuth();
const form = reactive({
  name: user.value?.name || '',
  contact_number: user.value?.contact_number || '',
  address: user.value?.address || '',
  blood_group: user.value?.blood_group || '',
  date_of_birth: user.value?.date_of_birth || '',
});

onMounted(async () => {
  try {
    const { data } = await api.get('/api/patient/profile');
    form.name = data.name || '';
    form.contact_number = data.contact_number || '';
    form.address = data.address || '';
    form.blood_group = data.blood_group || '';
    form.date_of_birth = data.date_of_birth || '';
  } catch (_) {}
});

async function save() {
  try {
    await api.put('/api/patient/profile', form);
    user.value.name = form.name;
    toast('Profile updated');
  } catch (e) {
    toast(e.response?.data?.message || 'Failed', 'error');
  }
}
</script>

<style scoped>
.patient-profile-page {
  --section-radius: 1rem;
  --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  --border-subtle: 1px solid rgba(0, 0, 0, 0.06);
  --accent: #0d6efd;
  --accent-soft: rgba(13, 110, 253, 0.08);
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

.section-profile .content-card {
  margin-bottom: 0;
}

.profile-form-wrap {
  max-width: 32rem;
  margin-left: auto;
  margin-right: auto;
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

.profile-form-grid {
  display: grid;
  gap: 1.25rem;
  grid-template-columns: 1fr;
}

@media (min-width: 576px) {
  .profile-form-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.profile-form-field-full {
  grid-column: 1 / -1;
}

.profile-form-field .form-label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--bs-body-color);
  margin-bottom: 0.35rem;
  display: block;
}

.profile-input,
.profile-select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  font-size: 0.9375rem;
  border-radius: 0.5rem;
  border: var(--border-subtle);
  background: var(--bs-body-bg);
  color: var(--bs-body-color);
}

.profile-input:focus,
.profile-select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.profile-select {
  cursor: pointer;
  appearance: auto;
}

.profile-form-actions {
  display: flex;
  justify-content: center;
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: var(--border-subtle);
}

.btn-save {
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

.btn-save:hover {
  opacity: 0.9;
}
</style>
