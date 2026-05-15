<template>
  <div class="d-flex min-vh-100 overflow-hidden">
    <div
      v-if="sidebarOpen"
      class="offcanvas-backdrop fade show d-md-none"
      @click="sidebarOpen = false"
    ></div>

    <aside
      class="sidebar-nav d-flex flex-column flex-shrink-0 position-fixed start-0 top-0 bottom-0 z-50 overflow-auto"
      :class="sidebarOpen ? 'translate-0' : 'translate-n100'"
    >
      <div class="sidebar-header d-flex align-items-center gap-3 px-4 py-3">
        <div class="sidebar-logo d-flex align-items-center justify-content-center">
          <i class="bi bi-heart-fill"></i>
        </div>
        <div>
          <h1 class="sidebar-title mb-0">MediCare HMS</h1>
          <p class="sidebar-subtitle mb-0 text-capitalize">{{ user?.role }} Portal</p>
        </div>
      </div>
      <nav class="sidebar-nav-links flex-grow-1 px-3 py-4">
        <button
          v-for="item in navItems"
          :key="item.path"
          type="button"
          class="sidebar-link d-flex align-items-center gap-3 w-100 text-start text-decoration-none rounded py-2 px-3 mb-1"
          :class="{ active: isActive(item.path) }"
          @click="go(item.path)"
        >
          <i :class="item.icon"></i>
          {{ item.label }}
        </button>
      </nav>
      <div class="sidebar-footer p-3 mt-auto">
        <div class="d-flex align-items-center gap-3 mb-3 px-2">
          <div class="sidebar-avatar rounded-circle d-flex align-items-center justify-content-center small fw-semibold">
            {{ (user?.name || user?.username || '?').charAt(0).toUpperCase() }}
          </div>
          <div class="flex-grow-1 min-w-0">
            <p class="small fw-medium text-truncate mb-0">{{ user?.name || user?.username || 'User' }}</p>
            <p class="small sidebar-muted text-truncate mb-0">{{ user?.email || '' }}</p>
          </div>
        </div>
        <button
          type="button"
          class="sidebar-signout d-flex align-items-center justify-content-center gap-2 w-100 py-2 text-decoration-none border-0 bg-transparent"
          @click="handleLogout"
        >
          <i class="bi bi-box-arrow-right"></i>
          Sign Out
        </button>
      </div>
    </aside>

    <main class="flex-grow-1 d-flex flex-column overflow-hidden main-content">
      <header class="d-flex align-items-center border-bottom bg-white px-4" style="height: 4rem;">
        <button
          type="button"
          class="btn btn-link d-md-none me-3 p-0"
          @click="sidebarOpen = !sidebarOpen"
        >
          <i :class="sidebarOpen ? 'bi bi-x-lg' : 'bi bi-list'"></i>
        </button>
      </header>
      <div class="flex-grow-1 overflow-auto p-4 p-md-5 layout-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuth } from '@/composables/useAuth.js';

const router = useRouter();
const route = useRoute();
const { user, logout } = useAuth();
const sidebarOpen = ref(false);

const navItemsByRole = {
  admin: [
    { label: 'Dashboard', icon: 'bi bi-grid', path: '/admin' },
    { label: 'Doctors', icon: 'bi bi-heart-pulse', path: '/admin/doctors' },
    { label: 'Patients', icon: 'bi bi-people', path: '/admin/patients' },
    { label: 'Appointments', icon: 'bi bi-calendar3', path: '/admin/appointments' },
    { label: 'Search', icon: 'bi bi-search', path: '/admin/search' },
  ],
  doctor: [
    { label: 'Dashboard', icon: 'bi bi-grid', path: '/doctor' },
    { label: 'Appointments', icon: 'bi bi-calendar3', path: '/doctor/appointments' },
    { label: 'Patients', icon: 'bi bi-people', path: '/doctor/patients' },
    { label: 'Availability', icon: 'bi bi-clipboard-check', path: '/doctor/availability' },
  ],
  patient: [
    { label: 'Dashboard', icon: 'bi bi-grid', path: '/patient' },
    { label: 'Book Appointment', icon: 'bi bi-calendar3', path: '/patient/book' },
    { label: 'My Appointments', icon: 'bi bi-list-ul', path: '/patient/appointments' },
    { label: 'Profile', icon: 'bi bi-gear', path: '/patient/profile' },
  ],
};

const navItems = computed(() => (user.value ? navItemsByRole[user.value.role] || [] : []));

function isActive(path) {
  return route.path === path;
}

function go(path) {
  router.push(path);
  sidebarOpen.value = false;
}

function handleLogout() {
  logout();
  router.push('/login');
}
</script>

<style scoped>
.sidebar-nav {
  width: 16rem;
  background-color: #102c48;
  color: #e8edf2;
  transition: transform 0.2s;
}

.sidebar-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-logo {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.5rem;
  background: rgba(64, 224, 208, 0.2);
  color: #40e0d0;
  font-size: 1rem;
}

.sidebar-title {
  font-size: 1rem;
  font-weight: 700;
  color: #fff;
}

.sidebar-subtitle {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
}

.sidebar-link {
  color: rgba(255, 255, 255, 0.75);
  background: transparent;
  border: none;
  transition: all 0.15s;
}
.sidebar-link:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.05);
}
.sidebar-link.active {
  color: #40e0d0;
  background: rgba(32, 64, 96, 0.8);
}
.sidebar-link i {
  font-size: 1.1rem;
}

.sidebar-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-avatar {
  width: 2rem;
  height: 2rem;
  background: rgba(64, 224, 208, 0.25);
  color: #40e0d0;
  font-size: 0.75rem;
}

.sidebar-muted {
  color: rgba(255, 255, 255, 0.6) !important;
}

.sidebar-signout {
  color: rgba(255, 255, 255, 0.75) !important;
}
.sidebar-signout:hover {
  color: #fff !important;
}

.main-content {
  min-width: 0;
}
@media (min-width: 768px) {
  .main-content {
    margin-left: 16rem;
  }
}

.translate-n100 {
  transform: translateX(-100%);
}
@media (min-width: 768px) {
  .translate-n100 {
    transform: none;
  }
}
</style>
