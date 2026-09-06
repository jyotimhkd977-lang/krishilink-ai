/* ==========================================================================
   KrishiLink AI — Main Application Controller & View Router
   ========================================================================== */

class KrishiApp {
  constructor() {
    this.currentView = 'dashboard';
  }

  init() {
    console.log("Initializing KrishiLink AI Farmer Platform...");
    
    // Initialize components
    if (window.KrishiSellWizard) window.KrishiSellWizard.init();
    if (window.KrishiAiAssistant) window.KrishiAiAssistant.init();
    if (window.KrishiLogistics) window.KrishiLogistics.init();
    if (window.KrishiConsumer) window.KrishiConsumer.init();
    if (window.KrishiAuth) window.KrishiAuth.init();

    this.bindNavigation();
    this.bindLanguageSwitcher();
    this.bindActionModals();
    this.renderAllViews();
    this.connectBackend();

    // Set saved or default language
    const savedLang = localStorage.getItem('krishilink_lang') || 'en';
    window.KrishiI18n.setLanguage(savedLang);

    // Listen for language changes to re-render dynamic cards
    window.addEventListener('languageChanged', () => {
      this.renderAllViews();
    });
  }

  async connectBackend() {
    if (!window.KrishiApi) return;

    try {
      const health = await window.KrishiApi.checkHealth();
      console.info(`KrishiLink AI backend connected (${health.service})`);
    } catch (error) {
      console.warn('KrishiLink AI backend is unavailable; using local demo data.', error);
    }
  }

  bindNavigation() {
    // Desktop Nav Links
    document.querySelectorAll('.nav-link[data-view]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const view = link.dataset.view;
        this.switchView(view);
      });
    });

    // Mobile Bottom Nav
    document.querySelectorAll('.mob-nav-item[data-view]').forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const view = item.dataset.view;
        this.switchView(view);
      });
    });

    // Top avatar / Profile link
    const avatar = document.getElementById('topbar-avatar-btn');
    if (avatar) {
      avatar.addEventListener('click', () => this.switchView('profile'));
    }

    const trustBadge = document.getElementById('topbar-trust-badge');
    if (trustBadge) {
      trustBadge.addEventListener('click', () => this.switchView('trust-score'));
    }

    // Quick action clicks
    document.querySelectorAll('[data-action-target]').forEach(card => {
      card.addEventListener('click', (e) => {
        const target = card.dataset.actionTarget;
        if (target === 'sell-modal') {
          window.KrishiSellWizard.openWizard();
        } else if (target === 'ai-modal') {
          window.KrishiAiAssistant.open();
        } else {
          this.switchView(target);
        }
      });
    });
  }

  bindLanguageSwitcher() {
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const lang = btn.dataset.lang;
        window.KrishiAudio.playClick();
        window.KrishiI18n.setLanguage(lang);
      });
    });
  }

  switchView(viewId) {
    window.KrishiAudio.playClick();
    this.currentView = viewId;

    // Update active state on nav links
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.toggle('active', link.dataset.view === viewId);
    });

    document.querySelectorAll('.mob-nav-item').forEach(item => {
      item.classList.toggle('active', item.dataset.view === viewId);
    });

    // Hide all views and show selected
    document.querySelectorAll('.view-section').forEach(sec => {
      sec.classList.remove('active');
    });

    const targetSection = document.getElementById(`view-${viewId}`);
    if (targetSection) {
      targetSection.classList.add('active');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Special view triggers
    if (viewId === 'logistics' && window.KrishiLogistics) {
      window.KrishiLogistics.renderMap();
    }
  }

  bindActionModals() {
    // Produce Add Buttons
    document.querySelectorAll('.btn-add-produce-modal').forEach(btn => {
      btn.addEventListener('click', () => window.KrishiSellWizard.openWizard());
    });

    // Modal dismiss buttons
    document.querySelectorAll('.btn-close-modal').forEach(btn => {
      btn.addEventListener('click', () => {
        const modal = btn.closest('.modal-overlay');
        if (modal) modal.classList.remove('active');
        window.KrishiAudio.playClick();
      });
    });

    // Backdrop click dismiss
    document.querySelectorAll('.modal-overlay').forEach(modal => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          modal.classList.remove('active');
          window.KrishiAudio.playClick();
        }
      });
    });

    // Settlement Statement Modal Trigger
    const btnSettlement = document.getElementById('btn-open-settlement');
    if (btnSettlement) {
      btnSettlement.addEventListener('click', () => {
        const modal = document.getElementById('settlement-modal');
        if (modal) modal.classList.add('active');
        window.KrishiAudio.playClick();
      });
    }

    // Withdraw Payout Button
    const btnWithdraw = document.getElementById('btn-withdraw-action');
    if (btnWithdraw) {
      btnWithdraw.addEventListener('click', () => {
        window.KrishiAudio.playSuccess();
        alert("🎉 Payout Initiated!\n₹47,850 successfully transferred via IMPS/DBT to:\nState Bank of India (Jatani Branch) •••• 4819\nRef: DBT-KL-2026-904128");
      });
    }

    // Notification dropdown/modal trigger
    const notifBtn = document.getElementById('topbar-notif-btn');
    if (notifBtn) {
      notifBtn.addEventListener('click', () => this.switchView('notifications'));
    }
  }

  renderAllViews() {
    this.renderMarketTickers();
    this.renderProduceCards();
    this.renderBuyerMatches();
    this.renderOrders();
    this.renderNotifications();
  }

  renderMarketTickers() {
    const container = document.getElementById('market-tickers-grid');
    if (!container) return;

    const data = window.KrishiData.marketPrices;
    container.innerHTML = data.map(crop => {
      const name = window.KrishiI18n.currentLang === 'hi' ? crop.hindi : (window.KrishiI18n.currentLang === 'or' ? crop.odia : crop.name);
      return `
        <div class="ticker-item" onclick="window.KrishiApp.switchView('price-intel')">
          <div class="ticker-crop-info">
            <img src="${crop.img}" alt="${name}" class="crop-mini-thumb"/>
            <div>
              <div class="ticker-crop-name">${name}</div>
              <div class="ticker-apmc">${crop.apmc}</div>
            </div>
          </div>
          <div class="ticker-price-row">
            <div class="ticker-price">₹${crop.price.toFixed(2)}<span style="font-size:0.8rem; font-weight:600; color:var(--text-muted)">/${crop.unit}</span></div>
            <div class="ticker-trend ${crop.isUp ? 'trend-up' : 'trend-down'}">
              ${crop.isUp ? '↑' : '↓'} ${Math.abs(crop.change)}%
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  renderProduceCards() {
    const grid = document.getElementById('my-produce-grid');
    if (!grid) return;

    const list = window.KrishiData.myProduce;
    grid.innerHTML = list.map(item => `
      <div class="produce-card">
        <div class="produce-card-img-wrap">
          <img src="${item.img}" alt="${item.name}" class="produce-card-img"/>
          <span class="produce-card-grade-badge">
            <span style="color:#16A34A">★</span> ${item.qualityGrade}
          </span>
          <span class="produce-card-status-badge">
            ● ${window.KrishiI18n.t('status_active')}
          </span>
        </div>
        <div class="produce-card-body">
          <div class="produce-title-row">
            <h4 class="produce-crop-name">${item.name}</h4>
            <span class="produce-qty-tag">${item.availableKg.toLocaleString()} KG</span>
          </div>
          <div class="produce-stats-row">
            <div class="produce-stat-col">
              <span>Quality Score</span>
              <span>${item.aiQualityScore}/100</span>
            </div>
            <div class="produce-stat-col">
              <span>AI Valuation</span>
              <span style="color:var(--green-700)">₹${item.aiPriceMin}–₹${item.aiPriceMax}</span>
            </div>
            <div class="produce-stat-col">
              <span>Demand</span>
              <span style="color:#B45309">🔥 High</span>
            </div>
          </div>
          <div class="produce-card-actions">
            <button class="btn btn-primary btn-sm" style="flex:1" onclick="window.KrishiNegotiation.openNegotiation('ABC Foods India Ltd.', 30.00)">
              Find Buyers
            </button>
            <button class="btn btn-secondary btn-sm" onclick="KrishiApp.manageProduce('${item.id}')">
              Manage
            </button>
          </div>
        </div>
      </div>
    `).join('');
  }

  renderBuyerMatches() {
    const grid = document.getElementById('buyer-matches-grid');
    if (!grid) return;

    const buyers = window.KrishiData.buyers;
    grid.innerHTML = buyers.map(b => `
      <div class="buyer-card">
        <div class="buyer-card-header">
          <div class="buyer-name-group">
            <h4>${b.name}</h4>
            <span class="buyer-dist">📍 ${b.location} (${b.distanceKm} km)</span>
          </div>
          <span class="ai-match-pill">
            ★ ${b.aiMatchScore}% Match
          </span>
        </div>
        <div class="buyer-offer-highlight">
          <div>
            <div style="font-size:0.8rem; color:var(--text-muted); font-weight:600">Buyer Offer</div>
            <div class="buyer-offer-price">₹${b.offerPrice.toFixed(2)}<span style="font-size:0.85rem; color:var(--text-muted)">/kg</span></div>
          </div>
          <div style="text-align:right">
            <div style="font-size:0.8rem; color:var(--text-muted); font-weight:600">Required Quantity</div>
            <div style="font-size:1.15rem; font-weight:800; color:var(--green-900)">${b.requiredKg} kg</div>
          </div>
        </div>
        <div class="buyer-tags-row">
          ${b.badges.map(badge => `<span class="tag-verified">✓ ${badge}</span>`).join('')}
        </div>
        <div style="display:flex; gap:10px; margin-top:auto">
          <button class="btn btn-accent btn-sm" style="flex:1" onclick="window.KrishiNegotiation.openNegotiation('${b.name}', ${b.offerPrice})">
            ${window.KrishiI18n.t('btn_view_offer')}
          </button>
          <button class="btn btn-secondary btn-sm" onclick="KrishiApp.showBuyerAiDetails('${b.id}')">
            AI Score Breakdown
          </button>
        </div>
      </div>
    `).join('');
  }

  renderOrders() {
    const list = document.getElementById('orders-list-container');
    if (!list) return;

    const orders = window.KrishiData.orders;
    list.innerHTML = orders.map(ord => `
      <div class="card" style="margin-bottom: 20px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px; flex-wrap:wrap; gap:12px;">
          <div>
            <span class="pill pill-gold" style="margin-bottom:6px">ORDER #${ord.id}</span>
            <h3 style="font-size:1.25rem; font-weight:800; color:var(--green-900)">${ord.crop} (${ord.quantityKg} kg)</h3>
            <p style="font-size:0.88rem; color:var(--text-muted)">Buyer: <strong>${ord.buyer}</strong> • Rate: ₹${ord.unitPrice}/kg</p>
          </div>
          <div style="text-align:right">
            <div style="font-size:0.8rem; color:var(--text-muted)">Total Value</div>
            <div style="font-size:1.4rem; font-weight:800; color:var(--green-900)">₹${ord.totalAmount.toLocaleString('en-IN')}</div>
          </div>
        </div>

        <!-- 6-Stage Visual Stepper -->
        <div style="display:flex; justify-content:space-between; margin:24px 0 16px 0; position:relative;">
          <div style="position:absolute; top:14px; left:20px; right:20px; height:3px; background:#E5DFD3; z-index:1;"></div>
          ${[
            { num: 1, label: "Order Confirmed", icon: "✓" },
            { num: 2, label: "Pickup Scheduled", icon: "📅" },
            { num: 3, label: "Produce Collected", icon: "📦" },
            { num: 4, label: "In Transit", icon: "🚚" },
            { num: 5, label: "Delivered", icon: "🏬" },
            { num: 6, label: "Payment Released", icon: "₹" }
          ].map(st => {
            const isDone = st.num < ord.statusStep;
            const isCurrent = st.num === ord.statusStep;
            const bg = isCurrent ? 'var(--green-800)' : (isDone ? 'var(--green-500)' : '#FFFFFF');
            const color = (isCurrent || isDone) ? '#FFFFFF' : 'var(--text-muted)';
            const border = (isCurrent || isDone) ? 'none' : '2px solid #D1C7B7';
            return `
              <div style="position:relative; z-index:2; display:flex; flex-direction:column; align-items:center; gap:6px;">
                <div style="width:30px; height:30px; border-radius:50%; background:${bg}; color:${color}; border:${border}; display:flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:bold;">
                  ${st.icon}
                </div>
                <span style="font-size:0.68rem; font-weight:700; color:${isCurrent ? 'var(--green-900)' : 'var(--text-muted)'}; text-align:center; max-width:65px;">
                  ${st.label}
                </span>
              </div>
            `;
          }).join('')}
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:16px; pt:12px; border-top:1px solid var(--border-soft); flex-wrap:wrap; gap:10px;">
          <div style="display:flex; align-items:center; gap:8px; font-size:0.88rem; color:var(--text-secondary)">
            <span>🚚 ${ord.vehicleNo}</span> •
            <span>Driver: ${ord.driverName}</span> •
            <span>ETA: <strong>${ord.pickupETA}</strong></span>
          </div>
          <div style="display:flex; gap:10px">
            <button class="btn btn-primary btn-sm" onclick="KrishiApp.switchView('logistics')">
              ${window.KrishiI18n.t('btn_track_order')}
            </button>
            <button class="btn btn-secondary btn-sm" onclick="KrishiApp.switchView('quality-protection')">
              Quality Inspection
            </button>
          </div>
        </div>
      </div>
    `).join('');
  }

  renderNotifications() {
    const list = document.getElementById('notif-list-container');
    if (!list) return;

    const notifs = window.KrishiData.notifications;
    list.innerHTML = notifs.map(n => `
      <div style="background:#FFFFFF; border:1px solid var(--border-soft); border-radius:var(--radius-md); padding:16px; display:flex; align-items:center; gap:16px; margin-bottom:12px; box-shadow:var(--shadow-sm);">
        <div style="width:44px; height:44px; border-radius:var(--radius-pill); background:var(--bg-card-alt); display:flex; align-items:center; justify-content:center; font-size:1.4rem; flex-shrink:0;">
          ${n.icon}
        </div>
        <div style="flex:1">
          <div style="display:flex; justify-content:space-between; margin-bottom:2px">
            <span style="font-size:0.75rem; font-weight:800; color:var(--green-800); text-transform:uppercase">${n.category}</span>
            <span style="font-size:0.75rem; color:var(--text-muted)">${n.time}</span>
          </div>
          <h5 style="font-size:0.95rem; font-weight:700; color:var(--green-900)">${n.title}</h5>
          <p style="font-size:0.85rem; color:var(--text-secondary)">${n.desc}</p>
        </div>
      </div>
    `).join('');
  }

  // Static Helpers
  static showCropPriceIntel(cropId) {
    window.KrishiApp.switchView('price-intel');
  }

  static manageProduce(cropId) {
    window.KrishiAudio.playClick();
    alert("⚙ Produce Management:\nYou can pause this listing, adjust minimum lot sizes, or issue bulk batch labels.");
  }

  static showBuyerAiDetails(buyerId) {
    window.KrishiAudio.playClick();
    alert("🤖 AI Buyer Scoring Breakdown:\n• Price Match: 96%\n• Payment History: 98% (Zero default, <24h release)\n• Route Efficiency: 92% (On direct pickup corridor)\n• Buyer Trust Rating: 4.9/5 stars");
  }

  static toggleDisputeState(isProblem) {
    window.KrishiAudio.playClick();
    const statusBox = document.getElementById('quality-status-banner');
    if (statusBox) {
      if (isProblem) {
        statusBox.style.background = '#FEE2E2';
        statusBox.style.borderColor = '#EF4444';
        statusBox.innerHTML = `
          <div style="display:flex; align-items:center; gap:12px; color:#991B1B;">
            <span style="font-size:1.8rem">🔴</span>
            <div>
              <h4 style="font-weight:800; font-size:1.1rem">QUALITY ISSUE REPORTED BY BUYER</h4>
              <p style="font-size:0.88rem">Buyer flagged 8% moisture variation. KrishiLink AI escrow is holding funds pending arbitration.</p>
            </div>
          </div>
          <button class="btn btn-danger btn-sm" onclick="alert('Dispute raised! KrishiLink Agri-Officer assigned for video re-inspection within 2 hours.')">Raise Dispute</button>
        `;
      } else {
        statusBox.style.background = '#E8F7EE';
        statusBox.style.borderColor = '#22C55E';
        statusBox.innerHTML = `
          <div style="display:flex; align-items:center; gap:12px; color:#14532D;">
            <span style="font-size:1.8rem">🟢</span>
            <div>
              <h4 style="font-weight:800; font-size:1.1rem">QUALITY ACCEPTED & VERIFIED</h4>
              <p style="font-size:0.88rem">Grade A quality confirmed by Collection Hub sensor. Payment released into your settlement account.</p>
            </div>
          </div>
          <button class="btn btn-primary btn-sm" onclick="window.KrishiApp.switchView('earnings')">View Earnings</button>
        `;
      }
    }
  }
}

window.KrishiApp = new KrishiApp();
document.addEventListener('DOMContentLoaded', () => {
  window.KrishiApp.init();
});
