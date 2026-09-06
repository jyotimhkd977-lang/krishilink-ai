/* ========================================================================== 
   KrishiLink AI - Backend API Client (Full SQLite & Services Integration)
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

    if (this.accessToken) {
      headers.Authorization = `Bearer ${this.accessToken}`;
    }
    if (options.body && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    try {
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
          // Keep default message
        }
        throw new Error(message);
      }

      this.isAvailable = true;
      return response.json();
    } catch (err) {
      // If network fails
      if (err.message && (err.message.includes('Failed to fetch') || err.message.includes('NetworkError'))) {
        this.isAvailable = false;
      }
      throw err;
    }
  }

  setSession(authResponse) {
    this.accessToken = authResponse.access_token;
    if (this.accessToken) {
      localStorage.setItem('krishilink_access_token', this.accessToken);
    }
    if (authResponse.user) {
      localStorage.setItem('krishilink_auth_user', JSON.stringify(authResponse.user));
    }
    return authResponse;
  }

  clearSession() {
    this.accessToken = null;
    localStorage.removeItem('krishilink_access_token');
    localStorage.removeItem('krishilink_auth_user');
  }

  // --- Health ---
  async checkHealth() {
    const health = await this.request('/health');
    this.isAvailable = health.status === 'ok';
    return health;
  }

  // --- Authentication & SMTP OTP ---
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
    return this.setSession(response);
  }

  async sendEmailOtp(email, role = 'farmer') {
    return this.request('/auth/email/send-otp', {
      method: 'POST',
      body: JSON.stringify({ email, role })
    });
  }

  async verifyEmailOtp(email, token, role = 'farmer') {
    const response = await this.request('/auth/email/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ email, token, role })
    });
    return this.setSession(response);
  }

  async sendPhoneOtp(phone) {
    return this.request('/auth/phone/send-otp', {
      method: 'POST',
      body: JSON.stringify({ phone })
    });
  }

  async verifyPhoneOtp(phone, token) {
    const response = await this.request('/auth/phone/verify-otp', {
      method: 'POST',
      body: JSON.stringify({ phone, token })
    });
    return this.setSession(response);
  }

  async currentUser() {
    return this.request('/auth/me');
  }

  async getMyProfile() {
    return this.request('/auth/profiles/me');
  }

  async updateMyProfile(profile) {
    return this.request('/auth/profiles/me', {
      method: 'PATCH',
      body: JSON.stringify(profile)
    });
  }

  async logout() {
    try {
      if (this.accessToken) {
        await this.request('/auth/logout', { method: 'POST' });
      }
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

  // --- Produce & Farm Listings ---
  async getProduceListings() {
    return this.request('/produce/listings');
  }

  async createProduceListing(payload) {
    return this.request('/produce/listings', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async getFarms() {
    return this.request('/produce/farms');
  }

  async createFarm(payload) {
    return this.request('/produce/farms', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  // --- Marketplace & Buyer Demands ---
  async getDemands() {
    return this.request('/marketplace/demands');
  }

  async createDemand(payload) {
    return this.request('/marketplace/demands', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async getOffers() {
    return this.request('/marketplace/offers');
  }

  async createOffer(payload) {
    return this.request('/marketplace/offers', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async decideOffer(offerId, status) {
    return this.request(`/marketplace/offers/${offerId}/decision`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    });
  }

  // --- Orders ---
  async getOrders() {
    return this.request('/orders');
  }

  async getOrder(orderId) {
    return this.request(`/orders/${orderId}`);
  }

  async createOrderFromOffer(offerId) {
    return this.request(`/orders/from-offer/${offerId}`, {
      method: 'POST'
    });
  }

  async updateOrderStatus(orderId, status, note = null) {
    return this.request(`/orders/${orderId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, note })
    });
  }

  // --- Logistics & Deliveries ---
  async getDeliveries() {
    return this.request('/deliveries');
  }

  async getDelivery(deliveryId) {
    return this.request(`/deliveries/${deliveryId}`);
  }

  // --- Quality & Disputes ---
  async getInspection(orderId) {
    return this.request(`/quality/orders/${orderId}/inspection`);
  }

  async getDisputes() {
    return this.request('/quality/disputes');
  }

  async createDispute(orderId, reason) {
    return this.request(`/quality/orders/${orderId}/disputes`, {
      method: 'POST',
      body: JSON.stringify({ reason })
    });
  }

  // --- Settlements & Payments ---
  async getSettlements() {
    return this.request('/payments/settlements');
  }

  async getPayments() {
    return this.request('/payments');
  }

  // --- Notifications ---
  async getNotifications() {
    return this.request('/notifications');
  }

  async markNotificationRead(notificationId) {
    return this.request(`/notifications/${notificationId}/read`, {
      method: 'PATCH'
    });
  }

  // --- AI Decision Support & Chat ---
  async chatAi(message, lang = 'en', crop = 'Tomato') {
    return this.request('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ message, lang, crop })
    });
  }

  async predictPrice(payload) {
    return this.request('/ai/price', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }

  async matchBuyers(listingId) {
    return this.request(`/ai/matching/${listingId}`, {
      method: 'POST'
    });
  }
}

window.KrishiApi = new KrishiApiClient();