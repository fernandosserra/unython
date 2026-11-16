import axios from 'axios';

export const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('unython_auth_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('unython_auth_token');
      localStorage.removeItem('unython_user_data');
      if (window.location.pathname !== '/login') {
        window.dispatchEvent(new Event('unython_auth_expired'));
      }
    }
    return Promise.reject(error);
  }
);
