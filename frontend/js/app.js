const API_BASE_URL = '/api';

const getToken = () => localStorage.getItem('access_token');
const getRefreshToken = () => localStorage.getItem('refresh_token');
const setTokens = (access, refresh) => {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
};
const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};
const isAuthenticated = () => !!getToken();

htmx.config.selfRequestsOnly = false;

document.body.addEventListener('htmx:configRequest', (evt) => {
  const token = getToken();
  if (token) {
    evt.detail.headers['Authorization'] = `Bearer ${token}`;
  }
});

document.body.addEventListener('htmx:responseError', (evt) => {
  if (evt.detail.xhr.status === 401) {
    clearTokens();
    window.location.href = 'index.html';
  }
});

document.addEventListener('DOMContentLoaded', () => {
  if (window.location.pathname.includes('dashboard.html') && !isAuthenticated()) {
    window.location.href = 'index.html';
  }

  if (window.location.pathname.includes('index.html') && isAuthenticated()) {
    window.location.href = 'dashboard.html';
  }
});
