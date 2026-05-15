<template>
  <div class="dashboard-spacing admin-search-page">
    <header class="dashboard-header">
      <h1 class="page-title">Search</h1>
      <p class="page-subtitle">Search patients by name, ID, or contact</p>
    </header>

    <section class="section section-search">
      <div class="search-bar-wrapper mb-4">
        <i class="bi bi-search search-bar-icon"></i>
        <input
          v-model="query"
          type="text"
          class="form-control search-bar-input"
          placeholder="Search by name, patient ID, or contact number..."
          @keyup.enter="search"
        />
        <button type="button" class="btn btn-primary ms-2" :disabled="loading" @click="search">
          <span v-if="loading">Searching...</span>
          <span v-else><i class="bi bi-search me-1"></i>Search</span>
        </button>
      </div>

      <p v-if="error" class="text-danger small mb-3">{{ error }}</p>

      <div v-if="hasSearched && !loading" class="content-card table-card">
        <div v-if="results.length === 0" class="content-card-empty">
          <i class="bi bi-person-x empty-icon"></i>
          <p class="mb-0">No patients found</p>
          <p class="small mb-0 mt-1">Try a different name, ID, or contact number</p>
        </div>
        <div v-else class="table-responsive">
          <table class="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Username</th>
                <th>Email</th>
                <th>Contact</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in results" :key="p.id">
                <td>{{ p.id }}</td>
                <td>{{ p.name }}</td>
                <td>{{ p.username }}</td>
                <td>{{ p.email }}</td>
                <td>{{ p.contact_number || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import api from '@/utils/api.js';

const query = ref('');
const results = ref([]);
const loading = ref(false);
const error = ref('');
const hasSearched = ref(false);

async function search() {
  const q = query.value?.trim() || '';
  if (!q) return;
  error.value = '';
  loading.value = true;
  hasSearched.value = true;
  try {
    const url = `/api/admin/patients/search?q=${encodeURIComponent(q)}`;
    const { data } = await api.get(url);
    results.value = Array.isArray(data) ? data : [];
  } catch (e) {
    results.value = [];
    error.value = e.response?.data?.message || 'Search failed. Please try again.';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.admin-search-page {
  --border-subtle: 1px solid rgba(0, 0, 0, 0.06);
  --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.dashboard-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: var(--border-subtle);
}

.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0 0 0.25rem 0;
}

.page-subtitle {
  font-size: 1rem;
  color: var(--bs-secondary-color);
  margin: 0;
}

.section {
  background: var(--bs-body-bg);
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: var(--card-shadow);
  border: var(--border-subtle);
}

.search-bar-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
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
  flex: 1;
  min-width: 200px;
  padding-left: 2.75rem;
  border-radius: 0.75rem;
  border: var(--border-subtle);
}

.content-card {
  background: var(--bs-body-bg);
  border-radius: 0.75rem;
  padding: 1.25rem;
  border: var(--border-subtle);
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

.admin-table tbody tr:last-child td {
  border-bottom: none;
}

.admin-table tbody tr:hover {
  background: rgba(0, 0, 0, 0.02);
}
</style>
