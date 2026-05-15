/**
 * Auth composable - uses backend API (JWT).
 */
import { ref, computed } from 'vue';
import api from '@/utils/api.js';

const user = ref(null);

function loadStoredUser() {
  try {
    const u = localStorage.getItem('user');
    if (u) user.value = JSON.parse(u);
  } catch (_) {
    user.value = null;
  }
}
loadStoredUser();

export function useAuth() {
  const isAuthenticated = computed(() => !!user.value);

  async function login(username, password) {
    const { data } = await api.post(`/api/auth/login`, { username: username.trim(), password });
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    user.value = data.user;
    return data.user;
  }

  async function register(form) {
    const { data } = await api.post(`/api/auth/register`, {
      username: (form.username || '').trim(),
      email: (form.email || '').trim().toLowerCase(),
      password: form.password,
      name: (form.name || '').trim(),
      contact_number: (form.contact_number || '').trim() || undefined,
      address: (form.address || '').trim() || undefined,
      date_of_birth: form.date_of_birth || undefined,
    });
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    user.value = data.user;
    return data.user;
  }

  function logout() {
    user.value = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  return {
    user,
    isAuthenticated,
    login,
    register,
    logout,
  };
}

export { user as authUser };
