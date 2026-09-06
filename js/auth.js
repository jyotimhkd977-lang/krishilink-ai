/* ==========================================================================
   KrishiLink AI — Authentication & Role Session Manager
   Supports: Farmer / FPO and Consumer / Bulk Buyer Login & Switching
   ========================================================================== */

class AuthManager {
  constructor() {
    this.currentUser = null;
    this.currentRoleTab = 'farmer'; // 'farmer' or 'consumer'
    this.simulatedOtp = '4819';
    this.phoneEntered = '';
  }

  init() {
    // Restore session if exists
    const saved = localStorage.getItem('krishilink_auth_user');
    if (saved) {
      try {
        this.currentUser = JSON.parse(saved);
      } catch (e) {
        this.currentUser = null;
      }
    }

    this.bindEvents();
    this.updateAuthStateUI();
    this.restoreBackendSession();
  }

  bindEvents() {
    // Role switch tabs inside modal
    document.querySelectorAll('.auth-role-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const role = tab.dataset.role;
        this.switchRoleTab(role);
      });
    });

    // Quick demo login buttons
    const btnDemoFarmer = document.getElementById('btn-demo-login-farmer');
    if (btnDemoFarmer) {
      btnDemoFarmer.addEventListener('click', () => {
        this.quickLogin('farmer');
      });
    }

    const btnDemoConsumer = document.getElementById('btn-demo-login-consumer');
    if (btnDemoConsumer) {
      btnDemoConsumer.addEventListener('click', () => {
        this.quickLogin('consumer');
      });
    }

    // OTP submit button
    const btnVerifyOtp = document.getElementById('btn-verify-otp');
    if (btnVerifyOtp) {
      btnVerifyOtp.addEventListener('click', () => {
        this.submitOtp();
      });
    }

    // Send OTP button
    const btnSendOtp = document.getElementById('btn-send-otp');
    if (btnSendOtp) {
      btnSendOtp.addEventListener('click', () => {
        this.sendOtp();
      });
    }

    // Landing portal buttons
    const btnPortalFarmer = document.getElementById('btn-portal-farmer');
    if (btnPortalFarmer) {
      btnPortalFarmer.addEventListener('click', () => {
        this.openAuthModal('farmer');
      });
    }

    const btnPortalConsumer = document.getElementById('btn-portal-consumer');
    if (btnPortalConsumer) {
      btnPortalConsumer.addEventListener('click', () => {
        this.openAuthModal('consumer');
      });
    }

    // Global Logout & Switch Portal Buttons
    document.querySelectorAll('.btn-auth-logout').forEach(btn => {
      btn.addEventListener('click', () => this.logout());
    });

    document.querySelectorAll('.btn-switch-portal').forEach(btn => {
      btn.addEventListener('click', () => this.switchPortal());
    });

    const btnBackendLogin = document.getElementById('btn-backend-login');
    if (btnBackendLogin) btnBackendLogin.addEventListener('click', () => this.loginWithBackend());

    const btnBackendRegister = document.getElementById('btn-backend-register');
    if (btnBackendRegister) btnBackendRegister.addEventListener('click', () => this.registerWithBackend());

    const btnForgotPassword = document.getElementById('btn-forgot-password');
    if (btnForgotPassword) btnForgotPassword.addEventListener('click', () => this.requestPasswordReset());
  }

  openAuthModal(defaultRole = 'farmer') {
    this.switchRoleTab(defaultRole);
    const modal = document.getElementById('auth-modal');
    if (modal) modal.classList.add('active');
    window.KrishiAudio.playClick();
  }

  closeAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) modal.classList.remove('active');
    window.KrishiAudio.playClick();
  }

  getBackendCredentials() {
    return {
      email: document.getElementById('auth-email-input')?.value.trim() || '',
      password: document.getElementById('auth-password-input')?.value || ''
    };
  }

  setBackendStatus(message, isError = false) {
    const status = document.getElementById('auth-api-status');
    if (status) {
      status.textContent = message;
      status.style.color = isError ? 'var(--status-danger)' : 'var(--green-700)';
    }
  }

  async loginWithBackend() {
    const { email, password } = this.getBackendCredentials();
    if (!email || !password) {
      this.setBackendStatus('Enter your email and password.', true);
      return;
    }

    try {
      this.setBackendStatus('Signing in...');
      const response = await window.KrishiApi.login(email, password, this.currentRoleTab);
      this.currentUser = this.mapBackendUser(response.user, email);
      this.saveSession();
      this.closeAuthModal();
      this.updateAuthStateUI();
      this.setBackendStatus('');
    } catch (error) {
      this.setBackendStatus(error.message, true);
    }
  }

  async registerWithBackend() {
    const { email, password } = this.getBackendCredentials();
    if (!email || password.length < 8) {
      this.setBackendStatus('Use an email and a password with at least 8 characters.', true);
      return;
    }

    const role = this.currentRoleTab === 'consumer' ? 'buyer' : 'farmer';
    try {
      this.setBackendStatus('Creating your account...');
      const response = await window.KrishiApi.register({ email, password, role });
      if (!response.access_token) {
        this.setBackendStatus('Account created. Check your email to verify it, then sign in.');
        return;
      }
      this.currentUser = this.mapBackendUser(response.user, email);
      this.saveSession();
      this.closeAuthModal();
      this.updateAuthStateUI();
    } catch (error) {
      this.setBackendStatus(error.message, true);
    }
  }

  async requestPasswordReset() {
    const { email } = this.getBackendCredentials();
    if (!email) {
      this.setBackendStatus('Enter your email first.', true);
      return;
    }
    try {
      const response = await window.KrishiApi.forgotPassword(email);
      this.setBackendStatus(response.message);
    } catch (error) {
      this.setBackendStatus(error.message, true);
    }
  }

  async restoreBackendSession() {
    if (!window.KrishiApi.accessToken) return;
    try {
      const user = await window.KrishiApi.currentUser();
      this.currentUser = this.mapBackendUser(user, user.email);
      this.saveSession();
      this.updateAuthStateUI();
    } catch (error) {
      window.KrishiApi.clearSession();
      localStorage.removeItem('krishilink_auth_user');
    }
  }

  mapBackendUser(user, fallbackEmail) {
    const role = user?.role || 'farmer';
    return {
      id: user?.id,
      email: user?.email || fallbackEmail,
      role: role === 'buyer' ? 'consumer' : role,
      name: user?.email || fallbackEmail,
      location: 'India',
      avatar: 'assets/images/ramesh.jpg'
    };
  }

  switchRoleTab(role) {
    this.currentRoleTab = role;
    document.querySelectorAll('.auth-role-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.role === role);
    });

    // Toggle description & demo buttons
    const farmerDemo = document.getElementById('demo-farmer-wrap');
    const consumerDemo = document.getElementById('demo-consumer-wrap');
    const roleHint = document.getElementById('auth-role-hint');

    if (farmerDemo) farmerDemo.style.display = (role === 'farmer') ? 'block' : 'none';
    if (consumerDemo) consumerDemo.style.display = (role === 'consumer') ? 'block' : 'none';
    if (roleHint) {
      roleHint.textContent = (role === 'farmer')
        ? "Farmer & FPO Login: Access AI crop pricing, orders & instant payments"
        : "Consumer & Buyer Login: Procure fresh harvest directly from certified farmers";
    }
  }

  sendOtp() {
    const phoneInput = document.getElementById('auth-phone-input');
    const phone = phoneInput ? phoneInput.value.trim() : '';

    if (!phone || phone.length < 10) {
      alert("Please enter a valid 10-digit Indian mobile number.");
      return;
    }

    this.phoneEntered = phone;
    window.KrishiAudio.playClick();

    // Show OTP input pane
    const phonePane = document.getElementById('auth-phone-pane');
    const otpPane = document.getElementById('auth-otp-pane');
    if (phonePane) phonePane.style.display = 'none';
    if (otpPane) otpPane.style.display = 'block';

    // Auto pre-fill demo OTP
    const otp1 = document.getElementById('otp-1');
    const otp2 = document.getElementById('otp-2');
    const otp3 = document.getElementById('otp-3');
    const otp4 = document.getElementById('otp-4');
    if (otp1 && otp2 && otp3 && otp4) {
      otp1.value = '4';
      otp2.value = '8';
      otp3.value = '1';
      otp4.value = '9';
    }

    alert(`📩 SMS Sent to +91 ${phone}!\nYour simulated KrishiLink verification OTP is: ${this.simulatedOtp}`);
  }

  submitOtp() {
    window.KrishiAudio.playSuccess();
    const role = this.currentRoleTab;

    if (role === 'farmer') {
      this.currentUser = {
        role: 'farmer',
        name: 'Ramesh Kumar',
        phone: this.phoneEntered || '94370 12894',
        location: 'Khordha, Odisha',
        avatar: 'assets/images/ramesh.jpg',
        trustScore: 94
      };
    } else {
      this.currentUser = {
        role: 'consumer',
        name: 'Priya Sharma',
        phone: this.phoneEntered || '98610 88210',
        location: 'Patia, Bhubaneswar',
        avatar: 'assets/images/ramesh.jpg',
        company: 'ABC Foods & Retail'
      };
    }

    this.saveSession();
    this.closeAuthModal();
    this.updateAuthStateUI();

    alert(`🎉 Welcome to KrishiLink AI, ${this.currentUser.name}!\nLogged in successfully as ${role === 'farmer' ? 'Farmer' : 'Consumer / Buyer'}.`);
  }

  quickLogin(role) {
    window.KrishiAudio.playSuccess();
    if (role === 'farmer') {
      this.currentUser = {
        role: 'farmer',
        name: 'Ramesh Kumar',
        phone: '94370 12894',
        location: 'Khordha, Odisha',
        avatar: 'assets/images/ramesh.jpg',
        trustScore: 94
      };
    } else {
      this.currentUser = {
        role: 'consumer',
        name: 'Priya Sharma (ABC Foods)',
        phone: '98610 88210',
        location: 'Patia, Bhubaneswar',
        avatar: 'assets/images/ramesh.jpg',
        company: 'ABC Foods India Ltd.'
      };
    }

    this.saveSession();
    this.closeAuthModal();
    this.updateAuthStateUI();
  }

  async logout() {
    window.KrishiAudio.playClick();
    try {
      await window.KrishiApi.logout();
    } catch (error) {
      console.warn('Backend logout failed; clearing local session.', error);
    }
    this.currentUser = null;
    localStorage.removeItem('krishilink_auth_user');
    this.updateAuthStateUI();
  }

  switchPortal() {
    if (!this.currentUser) {
      this.openAuthModal();
      return;
    }

    const newRole = (this.currentUser.role === 'farmer') ? 'consumer' : 'farmer';
    this.quickLogin(newRole);
  }

  saveSession() {
    localStorage.setItem('krishilink_auth_user', JSON.stringify(this.currentUser));
  }

  updateAuthStateUI() {
    const landingView = document.getElementById('view-landing');
    const farmerApp = document.querySelector('.app-layout');
    const consumerView = document.getElementById('view-consumer-portal');

    if (!this.currentUser) {
      // Show Landing Page for unauthenticated guests
      if (landingView) landingView.classList.add('active');
      if (farmerApp) farmerApp.style.display = 'none';
      if (consumerView) consumerView.style.display = 'none';
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    // Authenticated
    if (landingView) landingView.classList.remove('active');

    if (this.currentUser.role === 'farmer') {
      if (farmerApp) farmerApp.style.display = 'flex';
      if (consumerView) consumerView.style.display = 'none';
      if (window.KrishiApp) window.KrishiApp.switchView('dashboard');
    } else {
      // Consumer Mode
      if (farmerApp) farmerApp.style.display = 'none';
      if (consumerView) consumerView.style.display = 'block';
      if (window.KrishiConsumer) window.KrishiConsumer.renderStore();
    }
  }
}

window.KrishiAuth = new AuthManager();
