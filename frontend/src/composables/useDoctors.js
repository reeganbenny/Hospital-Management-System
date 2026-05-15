import { ref } from 'vue';
import api from '@/utils/api.js';

export function useDoctors(options = {}) {
  const { admin = false } = options;  // admin: true → /api/admin/doctors, false → /api/doctors/search
  const doctors = ref([]);
  const loading = ref(false);

  async function fetchDoctors(params = {}) {
    loading.value = true;
    try {
      let url = admin ? '/api/admin/doctors' : '/api/doctors/search';
      if (!admin && Object.keys(params).length) {
        const qs = new URLSearchParams(params).toString();
        url += `?${qs}`;
      }
      const { data } = await api.get(url);
      doctors.value = data || [];
    } catch (error) {
      console.error('Error fetching doctors:', error);
      doctors.value = [];
    } finally {
      loading.value = false;
    }
  }

  return { doctors, loading, fetchDoctors };
}