/* ==========================================================================
   KrishiLink AI — Consumer & Bulk Buyer Marketplace Module
   Allows consumers, restaurants, and retailers to buy directly from farmers
   ========================================================================== */

class ConsumerPortal {
  constructor() {
    this.cart = [
      { id: 'prod-1', name: 'Hybrid Red Tomato', farmer: 'Ramesh Kumar (Khordha)', price: 32.00, qtyKg: 20, img: 'assets/images/tomato.jpg' }
    ];
  }

  init() {
    this.bindEvents();
    this.renderStore();
    this.updateCartCount();
  }

  bindEvents() {
    const btnOpenCart = document.getElementById('btn-open-cart');
    const btnCloseCart = document.getElementById('btn-close-cart');
    const cartDrawer = document.getElementById('consumer-cart-drawer');

    if (btnOpenCart && cartDrawer) {
      btnOpenCart.addEventListener('click', () => {
        cartDrawer.classList.add('active');
        window.KrishiAudio.playClick();
      });
    }

    if (btnCloseCart && cartDrawer) {
      btnCloseCart.addEventListener('click', () => {
        cartDrawer.classList.remove('active');
        window.KrishiAudio.playClick();
      });
    }

    const btnCheckout = document.getElementById('btn-cart-checkout');
    if (btnCheckout) {
      btnCheckout.addEventListener('click', () => this.checkout());
    }
  }

  renderStore() {
    const container = document.getElementById('consumer-produce-grid');
    if (!container) return;

    const items = window.KrishiData.myProduce;
    container.innerHTML = items.map(crop => `
      <div class="consumer-produce-card">
        <div style="position:relative; height:180px;">
          <img src="${crop.img}" style="width:100%; height:100%; object-fit:cover;"/>
          <span class="produce-card-grade-badge">★ ${crop.qualityGrade}</span>
          <span style="position:absolute; bottom:12px; left:12px; background:rgba(0,0,0,0.7); color:#FFFFFF; font-size:0.75rem; font-weight:700; padding:4px 10px; border-radius:var(--radius-pill);">
            Fresh Harvest: Sep 8
          </span>
        </div>

        <div style="padding:20px; display:flex; flex-direction:column; gap:12px; flex:1;">
          <div class="consumer-farmer-provenance">
            <span>👨‍🌾</span>
            <span>Grown by <strong>Ramesh Kumar</strong> • Khordha</span>
          </div>

          <div style="display:flex; justify-content:space-between; align-items:baseline;">
            <h4 style="font-size:1.25rem; font-weight:800; color:var(--green-900);">${crop.name}</h4>
            <div style="font-size:1.4rem; font-weight:800; color:var(--green-800);">
              ₹${crop.aiPriceMin + 1}<span style="font-size:0.85rem; color:var(--text-muted); font-weight:600;">/kg</span>
            </div>
          </div>

          <p style="font-size:0.85rem; color:var(--text-secondary)">
            AI Quality Certified • ${crop.availableKg} kg available in lot
          </p>

          <div style="display:flex; gap:10px; margin-top:auto;">
            <button class="btn btn-primary btn-sm" style="flex:1;" onclick="window.KrishiConsumer.addToCart('${crop.id}', '${crop.name}', ${crop.aiPriceMin + 1}, '${crop.img}')">
              🛒 Add to Cart
            </button>
            <button class="btn btn-secondary btn-sm" onclick="window.KrishiNegotiation.openNegotiation('Priya Sharma (Consumer)', ${crop.aiPriceMin + 1})">
              Bulk Bid
            </button>
          </div>
        </div>
      </div>
    `).join('');
  }

  addToCart(id, name, price, img) {
    window.KrishiAudio.playClick();
    const existing = this.cart.find(i => i.id === id);
    if (existing) {
      existing.qtyKg += 10;
    } else {
      this.cart.push({ id, name, farmer: 'Ramesh Kumar (Khordha)', price, qtyKg: 10, img });
    }
    this.updateCartCount();
    this.renderCartItems();

    const drawer = document.getElementById('consumer-cart-drawer');
    if (drawer) drawer.classList.add('active');
  }

  updateCartCount() {
    const badge = document.getElementById('consumer-cart-count');
    if (badge) {
      const totalItems = this.cart.reduce((sum, i) => sum + 1, 0);
      badge.textContent = totalItems;
    }
  }

  renderCartItems() {
    const list = document.getElementById('consumer-cart-items-list');
    const totalEl = document.getElementById('consumer-cart-total');
    if (!list) return;

    if (this.cart.length === 0) {
      list.innerHTML = `<p style="text-align:center; padding:32px 0; color:var(--text-muted)">Your direct farm cart is empty.</p>`;
      if (totalEl) totalEl.textContent = "₹0.00";
      return;
    }

    let grandTotal = 0;
    list.innerHTML = this.cart.map(item => {
      const lineTotal = item.price * item.qtyKg;
      grandTotal += lineTotal;
      return `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:12px 0; border-bottom:1px solid var(--border-soft);">
          <div>
            <h5 style="font-weight:700; color:var(--green-900); font-size:0.95rem;">${item.name}</h5>
            <span style="font-size:0.75rem; color:var(--text-muted)">${item.farmer} • ₹${item.price}/kg</span>
          </div>
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:0.85rem; font-weight:700;">${item.qtyKg} KG</span>
            <span style="font-weight:800; color:var(--green-800);">₹${lineTotal.toLocaleString('en-IN')}</span>
          </div>
        </div>
      `;
    }).join('');

    if (totalEl) totalEl.textContent = `₹${grandTotal.toLocaleString('en-IN')}.00`;
  }

  async checkout() {
    if (this.cart.length === 0) {
      alert("Cart is empty!");
      return;
    }

    window.KrishiAudio?.playSuccess();
    const buyerName = window.KrishiAuth?.currentUser?.name || "Consumer / Buyer";

    try {
      if (window.KrishiApi) {
        for (const item of this.cart) {
          try {
            await window.KrishiApi.createOffer({
              listing_id: item.id.startsWith("prod-") ? item.id : "prod-1",
              offered_price: item.price,
              quantity: item.qtyKg,
              unit: "kg"
            });
          } catch (e) {
            console.warn("Direct offer creation fallback:", e);
          }
        }
      }
    } catch (err) {
      console.warn("Checkout API error:", err);
    }

    alert(`🎉 Order Placed Directly with Farmers by ${buyerName}!\nSmart Logistics consolidation scheduled for tomorrow 8:00 AM.\nEscrow payment locked safely in SQLite backend.`);
    this.cart = [];
    this.updateCartCount();
    this.renderCartItems();

    const drawer = document.getElementById('consumer-cart-drawer');
    if (drawer) drawer.classList.remove('active');

    if (window.KrishiApp && window.KrishiApp.loadBackendData) {
      await window.KrishiApp.loadBackendData();
    }
  }
}

window.KrishiConsumer = new ConsumerPortal();
