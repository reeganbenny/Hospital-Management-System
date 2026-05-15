<template>
  <div class="auth-page d-flex min-vh-100">
    <!-- Left brand / illustration panel -->
    <div class="auth-hero d-none d-lg-flex col-lg-6 align-items-center justify-content-center text-center p-5 text-white">
      <div class="auth-hero-inner">
        <div class="auth-logo-circle mb-4">
          <i class="bi bi-heart-pulse-fill fs-3"></i>
        </div>
        <h1 class="display-6 fw-bold mb-3">Hospital Management System</h1>
        <p class="lead opacity-85 mb-4">
          Modern, streamlined tools for managing patients, doctors, and appointments in one place.
        </p>
        <div class="d-flex justify-content-center gap-3 small opacity-85">
          <div class="badge bg-light text-dark rounded-pill px-3 py-2 border-0">Secure access</div>
          <div class="badge bg-light text-dark rounded-pill px-3 py-2 border-0">Role-based dashboards</div>
          <div class="badge bg-light text-dark rounded-pill px-3 py-2 border-0">24/7 availability</div>
        </div>
      </div>
    </div>

    <!-- Right auth card -->
    <div class="flex-grow-1 d-flex align-items-center justify-content-center p-3 p-md-4">
      <div class="auth-card-wrapper w-100">
        <!-- Mobile brand -->
        <div class="d-lg-none d-flex align-items-center gap-3 mb-4 justify-content-center">
          <div class="auth-logo-circle-sm">
            <i class="bi bi-heart-pulse-fill"></i>
          </div>
          <div>
            <h1 class="h4 fw-semibold mb-0">Hospital Management System</h1>
            <p class="small text-muted mb-0">Sign in to continue</p>
          </div>
        </div>

        <div class="auth-card shadow-lg border-0">
          <div class="auth-card-header d-flex justify-content-between align-items-center mb-3">
            <div>
              <h2 class="h5 fw-semibold mb-1">
                {{ activeTab === 'login' ? 'Welcome back' : 'Create your account' }}
              </h2>
              <p class="small text-muted mb-0">
                {{ activeTab === 'login' ? 'Access your personalized dashboard' : 'Register as a new patient to get started' }}
              </p>
            </div>
          </div>

          <!-- Tabs -->
          <div class="auth-tabs mb-3">
            <button
              type="button"
              class="auth-tab"
              :class="{ 'auth-tab-active': activeTab === 'login' }"
              @click="activeTab = 'login'"
            >
              <i class="bi bi-box-arrow-in-right me-2"></i>
              Sign In
            </button>
            <button
              type="button"
              class="auth-tab"
              :class="{ 'auth-tab-active': activeTab === 'register' }"
              @click="activeTab = 'register'"
            >
              <i class="bi bi-person-plus me-2"></i>
              Register
            </button>
          </div>

          <!-- Login -->
          <transition name="fade-slide" mode="out-in">
            <div v-if="activeTab === 'login'" key="login">
              <form @submit.prevent="handleLogin" class="mt-2">
                <div class="mb-3">
                  <label for="username" class="form-label small text-muted">Username</label>
                  <div class="input-group auth-input-group">
                    <span class="input-group-text"><i class="bi bi-person"></i></span>
                    <input
                      id="username"
                      v-model="loginForm.username"
                      type="text"
                      class="form-control"
                      placeholder="Enter your username"
                      required
                    />
                  </div>
                </div>
                <div class="mb-2">
                  <label for="password" class="form-label small text-muted">Password</label>
                  <div class="input-group auth-input-group">
                    <span class="input-group-text"><i class="bi bi-lock"></i></span>
                    <input
                      id="password"
                      v-model="loginForm.password"
                      type="password"
                      class="form-control"
                      placeholder="Enter your password"
                      required
                    />
                  </div>
                </div>
                <div class="d-flex justify-content-between align-items-center mb-3 small text-muted">
                  <span>Use the demo buttons below to explore quickly.</span>
                </div>
                <div v-if="error" class="alert alert-danger py-2 small">{{ error }}</div>
                <button type="submit" class="btn btn-gradient w-100 mb-3">
                  <span class="me-1">Sign In</span>
                  <i class="bi bi-arrow-right-short"></i>
                </button>

                <div class="auth-quick-demo pt-3 mt-2 border-top">
                  <p class="small text-muted mb-2">Quick demo roles</p>
                  <div class="d-flex gap-2 flex-wrap">
                    <button
                      v-for="r in roleConfig"
                      :key="r.role"
                      type="button"
                      class="btn btn-outline-light btn-sm flex-grow-1 auth-demo-btn"
                      @click="fillDemo(r.role)"
                    >
                      {{ r.label }}
                    </button>
                  </div>
                </div>
              </form>
            </div>

            <!-- Register -->
            <div v-else key="register">
              <form @submit.prevent="handleRegister" class="mt-2">
                <div class="row g-3 mb-3">
                  <div class="col-12 col-md-6">
                    <label for="reg-name" class="form-label small text-muted">Full Name</label>
                    <input
                      id="reg-name"
                      v-model="registerForm.name"
                      type="text"
                      class="form-control"
                      placeholder="Full Name"
                      required
                    />
                  </div>
                  <div class="col-12 col-md-6">
                    <label for="reg-email" class="form-label small text-muted">Email</label>
                    <input
                      id="reg-email"
                      v-model="registerForm.email"
                      type="email"
                      class="form-control"
                      placeholder="Email address"
                      required
                    />
                  </div>
                </div>

                <div class="row g-3 mb-3">
                  <div class="col-12 col-md-6">
                    <label for="reg-password" class="form-label small text-muted">Password</label>
                    <input
                      id="reg-password"
                      v-model="registerForm.password"
                      type="password"
                      class="form-control"
                      placeholder="Create a password"
                      required
                    />
                  </div>
                  <div class="col-12 col-md-6">
                    <label for="reg-phone" class="form-label small text-muted">Phone</label>
                    <input
                      id="reg-phone"
                      v-model="registerForm.contact_number"
                      type="text"
                      class="form-control"
                      placeholder="Contact number"
                    />
                  </div>
                </div>

                <div class="mb-3">
                  <label for="reg-dob" class="form-label small text-muted">Date of Birth</label>
                  <div class="input-group auth-input-group">
                    <span class="input-group-text"><i class="bi bi-calendar3"></i></span>
                    <input
                      id="reg-dob"
                      v-model="registerForm.date_of_birth"
                      type="date"
                      class="form-control"
                    />
                  </div>
                </div>

                <div v-if="error" class="alert alert-danger py-2 small">{{ error }}</div>
                <button type="submit" class="btn btn-gradient w-100">
                  <span class="me-1">Create Account</span>
                  <i class="bi bi-person-check"></i>
                </button>
              </form>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useAuth } from '@/composables/useAuth.js';
import { toast } from '@/utils/toast.js';
import { demoCredentials } from '@/data/mockData.js';

const router = useRouter();
const { login, register } = useAuth();

const activeTab = ref('login');
const roleConfig = [
  { role: 'admin', label: 'Admin' },
  { role: 'doctor', label: 'Doctor' },
  { role: 'patient', label: 'Patient' },
];
const error = ref('');
const loginForm = reactive({ username: '', password: '' });
const registerForm = reactive({
  email: '',
  password: '',
  name: '',
  contact_number: '',
  date_of_birth: '',
});

async function handleLogin() {
  error.value = '';
  try {
    const user = await login(loginForm.username, loginForm.password);
    toast('Welcome back!');
    const path = user.role === 'admin' ? '/admin' : user.role === 'doctor' ? '/doctor' : '/patient';
    router.push(path);
  } catch (e) {
    error.value = e.response?.data?.message || 'Invalid credentials';
  }
}

function fillDemo(role) {
  const creds = demoCredentials[role];
  if (creds) {
    loginForm.username = creds.username || creds.email;
    loginForm.password = creds.password;
  }
}

async function handleRegister() {
  error.value = '';
  try {
    await register({ ...registerForm, username: registerForm.email });
    toast('Account created!');
    router.push('/patient');
  } catch (e) {
    error.value = e.response?.data?.message || 'Registration failed';
  }
}
</script>

<style scoped>
/* Navbar/sidebar colors from Layout.vue */
.auth-page {
  background: #f0f4f8;
  color: var(--bs-body-color);
}

.auth-hero {
  background: #102c48;
  box-shadow: inset 0 0 80px rgba(0, 0, 0, 0.06);
}

.auth-hero-inner {
  max-width: 30rem;
}

.auth-logo-circle,
.auth-logo-circle-sm {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(64, 224, 208, 0.2);
  color: #40e0d0;
  backdrop-filter: blur(12px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.auth-logo-circle {
  width: 4rem;
  height: 4rem;
}

.auth-logo-circle-sm {
  width: 2.5rem;
  height: 2.5rem;
  background: rgba(64, 224, 208, 0.25);
  color: #40e0d0;
}

.auth-card-wrapper {
  max-width: 30rem;
}

.auth-card {
  border-radius: 1.25rem;
  padding: 1.75rem 1.75rem 1.5rem;
  background: #ffffff;
  color: var(--bs-body-color);
  border: 1px solid rgba(16, 44, 72, 0.1);
  box-shadow: 0 10px 40px rgba(16, 44, 72, 0.08);
}

.auth-card-header h2 {
  color: var(--bs-body-color);
}

.auth-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem;
  padding: 0.35rem;
  border-radius: 999px;
  background: #f0f4f8;
  border: 1px solid rgba(16, 44, 72, 0.08);
}

.auth-tab {
  border: none;
  background: transparent;
  color: var(--bs-secondary-color);
  border-radius: 999px;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.18s ease;
}

.auth-tab-active {
  background: #102c48;
  color: #fff;
  box-shadow: 0 4px 14px rgba(16, 44, 72, 0.35);
}

.auth-input-group .input-group-text {
  background: #f8fafc;
  border-color: #e2e8f0;
  color: var(--bs-secondary-color);
}

.auth-input-group .form-control {
  background: #fff;
  border-color: #e2e8f0;
  color: var(--bs-body-color);
}

.auth-input-group .form-control::placeholder {
  color: var(--bs-secondary-color);
}

.auth-input-group .form-control:focus {
  border-color: #40e0d0;
  box-shadow: 0 0 0 0.2rem rgba(64, 224, 208, 0.25);
}

.btn-gradient {
  background: #102c48;
  border: none;
  color: #fff;
  font-weight: 600;
  box-shadow: 0 8px 20px rgba(16, 44, 72, 0.35);
}

.btn-gradient:hover {
  filter: brightness(1.08);
  color: #fff;
  background: #153a5c;
  box-shadow: 0 10px 28px rgba(16, 44, 72, 0.4);
}

.auth-demo-btn {
  border-color: rgba(16, 44, 72, 0.4) !important;
  color: #102c48;
  background: rgba(16, 44, 72, 0.06);
}

.auth-demo-btn:hover {
  background: rgba(16, 44, 72, 0.12);
  color: #102c48;
  border-color: #102c48 !important;
}

.auth-quick-demo {
  border-color: #e2e8f0 !important;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

@media (max-width: 576.98px) {
  .auth-card {
    padding: 1.5rem 1.25rem 1.25rem;
    border-radius: 1rem;
  }
}
</style>
