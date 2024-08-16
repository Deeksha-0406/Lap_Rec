import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000'; // Flask server URL

export const recommendLaptop = (role, require_gpu) => {
    return axios.post(`${API_BASE_URL}/recommend`, { role, require_gpu });
};

export const onboardEmployee = (employee_id, name, role, require_gpu) => {
    return axios.post(`${API_BASE_URL}/onboard`, { employee_id, name, role, require_gpu });
};

export const offboardEmployee = (employee_id, laptop_name) => {
    return axios.post(`${API_BASE_URL}/offboard`, { employee_id, laptop_name });
};

export const reserveLaptop = (laptop_name, manager_name) => {
    return axios.post(`${API_BASE_URL}/reserve`, { laptop_name, manager_name });
};

export const checkReservation = (laptop_name) => {
    return axios.post(`${API_BASE_URL}/check`, { laptop_name });
};
