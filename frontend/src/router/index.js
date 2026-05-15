import { createRouter, createWebHistory } from 'vue-router';
import { authUser } from '@/composables/useAuth.js';
import Layout from '@/components/Layout.vue';

const routes = [
    // {
    //     path: '/',
    //     name: 'index',
    //     redirect: () => (!authUser.value ? '/login' : authUser.value.role === 'admin' ? '/admin' : authUser.value.role === 'doctor' ? '/doctor' : '/patient'),
    // },
    {
        path: '/login',
        name: 'login',
        component: () => import('@/views/LoginPage.vue'),
        meta: { public: true },
    },
    {
        path: '/admin',
        component: Layout,
        meta: { roles: ['admin'] },
        children: [
            { path: '', name: 'admin', component: () => import('@/views/AdminDashboard.vue') },
            { path: 'doctors', name: 'admin-doctors', component: () => import('@/views/admin/AdminDoctors.vue') },
            { path: 'patients', name: 'admin-patients', component: () => import('@/views/admin/AdminPatients.vue') },
            { path: 'appointments', name: 'admin-appointments', component: () => import('@/views/admin/AdminAppointments.vue') },
            { path: 'search', name: 'admin-search', component: () => import('@/views/admin/AdminSearch.vue') },
        ],
    },
    {
        path: '/doctor',
        component: Layout,
        meta: { roles: ['doctor'] },
        children: [
            { path: '', name: 'doctor', component: () => import('@/views/DoctorDashboard.vue') },
            { path: 'appointments', name: 'doctor-appointments', component: () => import('@/views/doctor/DoctorAppointments.vue') },
            { path: 'appointments/:id', name: 'doctor-appointment-detail', component: () => import('@/views/doctor/DoctorAppointmentDetail.vue') },
            { path: 'patients', name: 'doctor-patients', component: () => import('@/views/doctor/DoctorPatients.vue') },
            { path: 'availability', name: 'doctor-availability', component: () => import('@/views/doctor/DoctorAvailability.vue') },
        ],
    },
    {
        path: '/patient',
        component: Layout,
        meta: { roles: ['patient'] },
        children: [
            { path: '', name: 'patient', component: () => import('@/views/PatientDashboard.vue') },
            { path: 'book', name: 'patient-book', component: () => import('@/views/patient/BookAppointment.vue') },
            { path: 'appointments', name: 'patient-appointments', component: () => import('@/views/patient/MyAppointments.vue') },
            { path: 'profile', name: 'patient-profile', component: () => import('@/views/patient/PatientProfile.vue') },
        ],
    },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

router.beforeEach((to) => {
    const isPublic = to.meta.public;
    const roles = to.meta.roles;
    const authenticated = !!authUser.value;

    if (isPublic) return true;
    if (!authenticated) return '/login';
    if (roles && !roles.includes(authUser.value.role)) return '/login';
});

export default router;
