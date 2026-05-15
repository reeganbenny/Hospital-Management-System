import { ref } from 'vue';
import api from '@/utils/api.js';

/**
 * Composable for patient treatments and upcoming appointments.
 * Use in patient views to fetch treatment history and upcoming appointments.
 */
export function useAppointments() {
  const treatments = ref([]);
  const upcomingAppointments = ref([]);
  const upcomingDoctorAppointments = ref([]);
  const loadingTreatments = ref(false);
  const loadingUpcoming = ref(false);
  const loadingDoctorAppointments = ref(false);

  async function fetchTreatments() {
    loadingTreatments.value = true;
    try {
      const { data } = await api.get('/api/patient/treatments');
      treatments.value = data || [];
    } catch (error) {
      console.error('Error fetching treatments:', error);
      treatments.value = [];
    } finally {
      loadingTreatments.value = false;
    }
  }

  async function fetchUpcomingAppointments() {
    loadingUpcoming.value = true;
    try {
      const { data } = await api.get('/api/patient/appointments', {
        params: { upcoming: 1 },
      });
      upcomingAppointments.value = data || [];
    } catch (error) {
      console.error('Error fetching upcoming appointments:', error);
      upcomingAppointments.value = [];
    } finally {
      loadingUpcoming.value = false;
    }
  }

  async function fetchDoctorAppointments() {
    loadingDoctorAppointments.value = true;
    try {
      const { data } = await api.get('/api/doctor/appointments');
      upcomingDoctorAppointments.value = data || [];
    } catch (error) {
      console.error('Error fetching upcoming appointments:', error);
      upcomingDoctorAppointments.value = [];
    } finally {
      loadingDoctorAppointments.value = false;
    }
  }

  return {
    treatments,
    upcomingAppointments,
    upcomingDoctorAppointments,
    loadingTreatments,
    loadingDoctorAppointments,
    loadingUpcoming,
    fetchTreatments,
    fetchUpcomingAppointments,
    fetchDoctorAppointments,
  };
}
