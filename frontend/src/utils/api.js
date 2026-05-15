/**
 * Fetch-based API client for HMS. Uses Vite proxy in dev: /api -> backend.
 */

function getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    const token = localStorage.getItem('token');
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
  }
  
  async function handleResponse(res) {
    if (res.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') window.location.href = '/login';
      const err = new Error('Unauthorized');
      err.response = { status: 401, data: { message: 'Unauthorized' } };
      throw err;
    }
    const text = await res.text();
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (error) {
        console.error('Error parsing JSON:', error);
        console.error('Raw response text:', text);
      }
    }
    if (!res.ok) {
      const err = new Error(data?.message || res.statusText || 'Request failed');
      err.response = { status: res.status, data: data || {} };
      throw err;
    }
    return { data };
  }
  
  const api = {
    async get(url) {
      console.log(url);
      const res = await fetch(url, { method: 'GET', headers: getHeaders() });
      return handleResponse(res);
    },
    async post(url, data) {
      const res = await fetch(url, {
        method: 'POST',
        headers: getHeaders(),
        body: data ? JSON.stringify(data) : undefined,
      });
      return handleResponse(res);
    },
    async put(url, data) {
      const res = await fetch(url, {
        method: 'PUT',
        headers: getHeaders(),
        body: data ? JSON.stringify(data) : undefined,
      });
      return handleResponse(res);
    },
    async patch(url, data) {
      const res = await fetch(url, {
        method: 'PATCH',
        headers: getHeaders(),
        body: data ? JSON.stringify(data) : undefined,
      });
      return handleResponse(res);
    },
    async delete(url) {
      const res = await fetch(url, { method: 'DELETE', headers: getHeaders() });
      return handleResponse(res);
    },
  };
  
  export default api;
  