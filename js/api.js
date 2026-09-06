/* ========================================================================== 
   KrishiLink AI - Backend API Client
   ========================================================================== */

class KrishiApiClient {
  constructor() {
    this.baseUrl = (window.KRISHILINK_API_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');
    this.isAvailable = false;
    this.accessToken = localStorage.getItem('krishilink_access_token');
  }

  async request(path, options = {}) {
    const headers = {
      Accept: 'application/json',
      ...(options.headers || {})
    };

    if (this.accessToken) headers.Authorization = `Bearer ${this.accessToken}`;
    if (options.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json';

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers
    });

    if (!response.ok) {
      let message = `API request failed with status ${response.status}`;
      try {
        const error = await response.json();
        message = error.error?.message || error.detail || message;
      } catch (parseError) {
        // Keep the status-based error when the response is not JSON.
      }
      throw new Error(message);
    }

    return response.json();
  }

  setSession(authResponse) {
    this.accessToken = authResponse.access_token;
    if (this.accessToken) localStorage.setItem('krishilink_access_token', this.accessToken);
    return authResponse;
  }

  clearSession() {
    this.accessToken = null;
    localStorage.removeItem('krishilink_access_token');
  }

  async checkHealth() {
    const health = await this.request('/health');
    this.isAvailable = health.status === 'ok';
    return health;
  }

  async register(payload) {
    const response = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    return this.setSession(response);
  }

  async login(email, password, role) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    response.user = response.user || { role };
    return this.setSession(response);
  }

  async currentUser() {
    return this.request('/auth/me');
  }

  async logout() {
    try {
      if (this.accessToken) await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.clearSession();
    }
  }

  async forgotPassword(email) {
    return this.request('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email })
    });
  }

  async getMyProfile() {
    return this.request('/auth/profiles/me');
  }
}

window.KrishiApi = new KrishiApiClient();