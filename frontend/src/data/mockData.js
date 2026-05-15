import { format, addDays } from "date-fns";

const generateNext7DaysAvailability = () => {
    const slots = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "14:00", "14:30", "15:00", "15:30", "16:00"];
    return Array.from({ length: 7 }, (_, i) => ({
        date: format(addDays(new Date(), i + 1), "yyyy-MM-dd"),
        slots: slots.filter(() => Math.random() > 0.3),
    }));
};

export const departments = [
    { id: "dep-1", name: "Cardiology", description: "Heart and cardiovascular system", doctorCount: 3, icon: "Heart" },
    { id: "dep-2", name: "Neurology", description: "Brain and nervous system", doctorCount: 2, icon: "Brain" },
    { id: "dep-3", name: "Orthopedics", description: "Bones, joints and muscles", doctorCount: 2, icon: "Bone" },
    { id: "dep-4", name: "Dermatology", description: "Skin, hair and nails", doctorCount: 1, icon: "Scan" },
    { id: "dep-5", name: "Pediatrics", description: "Children's healthcare", doctorCount: 2, icon: "Baby" },
    { id: "dep-6", name: "General Medicine", description: "Primary care and general health", doctorCount: 3, icon: "Stethoscope" },
];

export const doctors = [
    { id: "doc-1", name: "Dr. Sarah Mitchell", email: "sarah@hospital.com", role: "doctor", phone: "555-0101", specialization: "Cardiology", departmentId: "dep-1", experience: 12, availability: generateNext7DaysAvailability(), isActive: true },
    { id: "doc-2", name: "Dr. James Wilson", email: "james@hospital.com", role: "doctor", phone: "555-0102", specialization: "Neurology", departmentId: "dep-2", experience: 15, availability: generateNext7DaysAvailability(), isActive: true },
    { id: "doc-3", name: "Dr. Emily Chen", email: "emily@hospital.com", role: "doctor", phone: "555-0103", specialization: "Orthopedics", departmentId: "dep-3", experience: 8, availability: generateNext7DaysAvailability(), isActive: true },
    { id: "doc-4", name: "Dr. Michael Brown", email: "michael@hospital.com", role: "doctor", phone: "555-0104", specialization: "Pediatrics", departmentId: "dep-5", experience: 10, availability: generateNext7DaysAvailability(), isActive: true },
    { id: "doc-5", name: "Dr. Lisa Anderson", email: "lisa@hospital.com", role: "doctor", phone: "555-0105", specialization: "Dermatology", departmentId: "dep-4", experience: 7, availability: generateNext7DaysAvailability(), isActive: true },
    { id: "doc-6", name: "Dr. Robert Taylor", email: "robert@hospital.com", role: "doctor", phone: "555-0106", specialization: "General Medicine", departmentId: "dep-6", experience: 20, availability: generateNext7DaysAvailability(), isActive: true },
];

export const patients = [
    { id: "pat-1", name: "Alice Johnson", email: "alice@email.com", role: "patient", phone: "555-1001", dateOfBirth: "1990-05-15", gender: "Female", bloodGroup: "A+", address: "123 Oak Street" },
    { id: "pat-2", name: "Bob Martinez", email: "bob@email.com", role: "patient", phone: "555-1002", dateOfBirth: "1985-08-22", gender: "Male", bloodGroup: "O+", address: "456 Elm Avenue" },
    { id: "pat-3", name: "Carol Davis", email: "carol@email.com", role: "patient", phone: "555-1003", dateOfBirth: "1978-12-03", gender: "Female", bloodGroup: "B+", address: "789 Pine Road" },
    { id: "pat-4", name: "David Lee", email: "david@email.com", role: "patient", phone: "555-1004", dateOfBirth: "1995-03-10", gender: "Male", bloodGroup: "AB-", address: "321 Cedar Lane" },
];

export const appointments = [
    { id: "apt-1", patientId: "pat-1", doctorId: "doc-1", date: format(new Date(), "yyyy-MM-dd"), time: "10:00", status: "booked", reason: "Chest pain consultation", patientName: "Alice Johnson", doctorName: "Dr. Sarah Mitchell", specialization: "Cardiology" },
    { id: "apt-2", patientId: "pat-2", doctorId: "doc-2", date: format(new Date(), "yyyy-MM-dd"), time: "11:00", status: "booked", reason: "Headache and dizziness", patientName: "Bob Martinez", doctorName: "Dr. James Wilson", specialization: "Neurology" },
    { id: "apt-3", patientId: "pat-1", doctorId: "doc-6", date: format(addDays(new Date(), 1), "yyyy-MM-dd"), time: "14:00", status: "booked", reason: "Follow-up checkup", patientName: "Alice Johnson", doctorName: "Dr. Robert Taylor", specialization: "General Medicine" },
    { id: "apt-4", patientId: "pat-3", doctorId: "doc-3", date: format(addDays(new Date(), -5), "yyyy-MM-dd"), time: "09:00", status: "completed", reason: "Knee pain", patientName: "Carol Davis", doctorName: "Dr. Emily Chen", specialization: "Orthopedics" },
    { id: "apt-5", patientId: "pat-4", doctorId: "doc-4", date: format(addDays(new Date(), -10), "yyyy-MM-dd"), time: "15:00", status: "completed", reason: "General checkup", patientName: "David Lee", doctorName: "Dr. Michael Brown", specialization: "Pediatrics" },
    { id: "apt-6", patientId: "pat-1", doctorId: "doc-5", date: format(addDays(new Date(), -3), "yyyy-MM-dd"), time: "10:30", status: "cancelled", reason: "Skin rash", patientName: "Alice Johnson", doctorName: "Dr. Lisa Anderson", specialization: "Dermatology" },
];

export const treatments = [
    { id: "trt-1", appointmentId: "apt-4", patientId: "pat-3", doctorId: "doc-3", diagnosis: "Mild ligament strain in right knee", prescription: "Ibuprofen 400mg twice daily, Ice pack application", notes: "Advised rest for 2 weeks. No heavy lifting.", nextVisit: format(addDays(new Date(), 10), "yyyy-MM-dd"), date: format(addDays(new Date(), -5), "yyyy-MM-dd") },
    { id: "trt-2", appointmentId: "apt-5", patientId: "pat-4", doctorId: "doc-4", diagnosis: "Healthy, no issues found", prescription: "Multivitamins daily", notes: "All vitals normal. Growth on track.", nextVisit: format(addDays(new Date(), 90), "yyyy-MM-dd"), date: format(addDays(new Date(), -10), "yyyy-MM-dd") },
];

export const adminUser = {
    id: "admin-1",
    name: "Admin User",
    email: "admin@hospital.com",
    role: "admin",
    phone: "8822774455",
};

export const demoCredentials = {
    admin: { username: "admin", email: "admin@hospital.com", password: "admin123" },
    doctor: { username: "sarah@hospital.com", email: "sarah@hospital.com", password: "doctor123" },
    patient: { username: "alice@email.com", email: "alice@email.com", password: "patient123" },
};
