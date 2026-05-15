import { ref } from 'vue';
import api from '@/utils/api.js';

export function useDepartments() {
    const departments = ref([]);
    const loading = ref(false);
  
    async function fetchDepartments() {
      loading.value = true;
      try {
        const { data } = await api.get(`/api/departments`);
        departments.value = data || [];
      } catch (error) {
        console.error('Error fetching departments:', error);
        departments.value = [];
      } finally {
        loading.value = false;
      }
    }
  
    return { departments, loading, fetchDepartments };  // ← add this
  }