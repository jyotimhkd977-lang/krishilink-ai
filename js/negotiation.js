/* ==========================================================================
   KrishiLink AI — Negotiation Engine
   Farmer-Buyer Negotiation Screen with AI Fair Price Guardrail
   ========================================================================== */

class NegotiationEngine {
  constructor() {
    this.currentDeal = {
      product: "Tomato",
      quantity: 500,
      buyer: "ABC Foods India Ltd.",
      buyerOffer: 30.00,
      aiFairPrice: 32.00,
      buyerLocation: "Khordha Industrial Estate"
    };
  }

  openNegotiation(buyerName = "ABC Foods India Ltd.", offer = 30.00) {
    this.currentDeal.buyer = buyerName;
    this.currentDeal.buyerOffer = offer;

    const modal = document.getElementById('negotiation-modal');
    if (modal) {
      document.getElementById('neg-buyer-name').textContent = this.currentDeal.buyer;
      document.getElementById('neg-buyer-offer').textContent = `₹${this.currentDeal.buyerOffer.toFixed(2)}`;
      document.getElementById('neg-ai-price').textContent = `₹${this.currentDeal.aiFairPrice.toFixed(2)}`;
      document.getElementById('neg-counter-input').value = this.currentDeal.aiFairPrice;
      modal.classList.add('active');
    }
    window.KrishiAudio.playClick();
  }

  closeNegotiation() {
    const modal = document.getElementById('negotiation-modal');
    if (modal) modal.classList.remove('active');
    window.KrishiAudio.playClick();
  }

  async acceptOffer(price, source = 'buyer') {
    window.KrishiAudio?.playSuccess();
    const total = price * this.currentDeal.quantity;
    const orderId = `KL${Math.floor(10000 + Math.random() * 90000)}`;
    
    // Attempt backend persistence
    try {
      if (window.KrishiApi) {
        await window.KrishiApi.createOffer({
          listing_id: "prod-1",
          offered_price: price,
          quantity: this.currentDeal.quantity,
          unit: "kg"
        });
      }
    } catch (e) {
      console.warn("Backend offer/order sync fallback:", e);
    }

    // Add confirmed order to local state for immediate feedback
    const newOrder = {
      id: orderId,
      crop: this.currentDeal.product,
      cropImg: "assets/images/tomato.jpg",
      quantityKg: this.currentDeal.quantity,
      buyer: this.currentDeal.buyer,
      unitPrice: price,
      totalAmount: total,
      statusStep: 1, // Order Confirmed
      statusText: "Order Confirmed & Awaiting Pickup",
      vehicleNo: "OD-02-KL-9081",
      driverName: "Santosh Das",
      driverPhone: "+91 94371 90234",
      pickupETA: "Today 11:30 AM",
      pickupDate: "Today",
      routeSavings: {
        distanceSavedKm: 14,
        fuelSavingsInr: 350,
        co2SavedKg: 10
      }
    };

    window.KrishiData.orders.unshift(newOrder);

    alert(`🎉 Deal Closed! You accepted ₹${price}/kg with ${this.currentDeal.buyer}.\nTotal Order Value: ₹${total.toLocaleString('en-IN')}.\nSmart Pickup has been scheduled.`);

    this.closeNegotiation();

    if (window.KrishiApp) {
      if (window.KrishiApp.loadBackendData) await window.KrishiApp.loadBackendData();
      window.KrishiApp.renderOrders();
      window.KrishiApp.switchView('orders');
    }
  }

  sendCounter() {
    const inputVal = parseFloat(document.getElementById('neg-counter-input').value);
    if (!inputVal || inputVal <= 0) {
      alert("Please enter a valid price per kg.");
      return;
    }

    const btn = document.getElementById('btn-submit-counter');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Negotiating with Buyer AI...";
    window.KrishiAudio.playClick();

    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = originalText;

      if (inputVal <= 32.50) {
        // Buyer accepts
        window.KrishiAudio.playSuccess();
        alert(`🤝 Success! ${this.currentDeal.buyer} accepted your counter-offer of ₹${inputVal}/kg!\nContract generated automatically.`);
        this.acceptOffer(inputVal, 'counter');
      } else {
        // Buyer countered with fair middle ground
        const compromisePrice = 32.00;
        alert(`💬 ${this.currentDeal.buyer} reviewed your price of ₹${inputVal}/kg and agreed to meet at AI Recommended ₹${compromisePrice}/kg.\nClick "Accept AI Recommendation" to close deal.`);
        document.getElementById('neg-counter-input').value = compromisePrice;
      }
    }, 1200);
  }
}

window.KrishiNegotiation = new NegotiationEngine();
