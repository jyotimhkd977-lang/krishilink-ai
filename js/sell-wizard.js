/* ==========================================================================
   KrishiLink AI — 5-Step Produce Selling Wizard
   Interactive Multi-Step Farmer Flow with AI Quality Scanner
   ========================================================================== */

class SellWizard {
  constructor() {
    this.currentStep = 1;
    this.selectedCrop = { id: 'tomato', name: 'Tomato', emoji: '🍅', img: 'assets/images/tomato.jpg' };
    this.quantityKg = 500;
    this.harvestDate = new Date().toISOString().split('T')[0];
    this.location = "Khordha Farm Field, Odisha";
    this.aiQuality = {
      score: 92,
      grade: 'A',
      freshness: 95,
      uniformity: 89,
      damage: 4
    };
    this.aiPricing = {
      marketPrice: 29.00,
      recommendedMin: 31.00,
      recommendedMax: 33.00,
      demand: 'High (89%)',
      buyerInterest: 'High (4 Bids Ready)'
    };
  }

  init() {
    this.bindEvents();
  }

  openWizard() {
    this.currentStep = 1;
    this.renderStep();
    const modal = document.getElementById('sell-produce-modal');
    if (modal) modal.classList.add('active');
    window.KrishiAudio.playClick();
  }

  closeWizard() {
    const modal = document.getElementById('sell-produce-modal');
    if (modal) modal.classList.remove('active');
    window.KrishiAudio.playClick();
  }

  bindEvents() {
    // Crop selection pills
    document.addEventListener('click', (e) => {
      const cropCard = e.target.closest('.crop-pick-card');
      if (cropCard) {
        document.querySelectorAll('.crop-pick-card').forEach(c => c.classList.remove('selected'));
        cropCard.classList.add('selected');
        this.selectedCrop = {
          id: cropCard.dataset.crop,
          name: cropCard.dataset.name,
          emoji: cropCard.dataset.emoji,
          img: cropCard.dataset.img
        };
        window.KrishiAudio.playClick();
      }
    });

    // Step navigation buttons
    const btnNext = document.getElementById('wizard-btn-next');
    const btnBack = document.getElementById('wizard-btn-back');

    if (btnNext) {
      btnNext.addEventListener('click', () => this.nextStep());
    }
    if (btnBack) {
      btnBack.addEventListener('click', () => this.prevStep());
    }
  }

  nextStep() {
    if (this.currentStep === 2) {
      const qtyInput = document.getElementById('wizard-qty-input');
      if (qtyInput) {
        this.quantityKg = parseFloat(qtyInput.value) || 500;
      }
    }

    if (this.currentStep < 5) {
      this.currentStep++;
      this.renderStep();
      window.KrishiAudio.playClick();

      // Trigger AI scan animation if step 3
      if (this.currentStep === 3) {
        this.simulateAiScan();
      }
    } else {
      // Step 5 Submit: Publish produce
      this.publishProduce();
    }
  }

  prevStep() {
    if (this.currentStep > 1) {
      this.currentStep--;
      this.renderStep();
      window.KrishiAudio.playClick();
    }
  }

  simulateAiScan() {
    const scanStatus = document.getElementById('ai-scan-status-text');
    window.KrishiAudio.playScan();
    if (scanStatus) {
      scanStatus.textContent = "AI Vision Scanner analyzing surface texture, brix & color...";
      setTimeout(() => {
        scanStatus.textContent = "✓ AI Analysis Complete: Grade A Certified";
        window.KrishiAudio.playSuccess();
      }, 1600);
    }
  }

  publishProduce() {
    // Create new produce item
    const newCrop = {
      id: `prod-${Date.now()}`,
      name: `${this.selectedCrop.name} (Fresh Harvest)`,
      cropKey: this.selectedCrop.id,
      availableKg: this.quantityKg,
      harvestDate: this.harvestDate,
      qualityGrade: `Grade ${this.aiQuality.grade}`,
      aiQualityScore: this.aiQuality.score,
      freshnessScore: this.aiQuality.freshness,
      uniformityScore: this.aiQuality.uniformity,
      damagePercent: this.aiQuality.damage,
      aiPriceMin: this.aiPricing.recommendedMin,
      aiPriceMax: this.aiPricing.recommendedMax,
      status: "Active",
      img: this.selectedCrop.img || "assets/images/tomato.jpg",
      buyerInterest: "Instant AI Match Active",
      tags: ["AI Quality Certified", "Direct Farm Listing"]
    };

    window.KrishiData.myProduce.unshift(newCrop);
    window.KrishiAudio.playSuccess();

    // Show celebration alert
    alert(`🎉 Congratulations Ramesh! Your ${this.quantityKg} kg ${this.selectedCrop.name} is now LIVE on KrishiLink Marketplace at AI Recommended ₹${this.aiPricing.recommendedMin}–₹${this.aiPricing.recommendedMax}/kg!`);

    this.closeWizard();

    // Refresh UI
    if (window.KrishiApp) {
      window.KrishiApp.renderProduceCards();
      window.KrishiApp.switchView('my-produce');
    }
  }

  renderStep() {
    // Update step indicator
    for (let i = 1; i <= 5; i++) {
      const node = document.getElementById(`step-node-${i}`);
      if (node) {
        node.classList.remove('active', 'done');
        if (i === this.currentStep) node.classList.add('active');
        else if (i < this.currentStep) node.classList.add('done');
      }
    }

    // Toggle step panes
    for (let i = 1; i <= 5; i++) {
      const pane = document.getElementById(`wizard-step-${i}`);
      if (pane) {
        pane.style.display = (i === this.currentStep) ? 'block' : 'none';
      }
    }

    const btnBack = document.getElementById('wizard-btn-back');
    const btnNext = document.getElementById('wizard-btn-next');

    if (btnBack) {
      btnBack.style.visibility = (this.currentStep === 1) ? 'hidden' : 'visible';
    }

    if (btnNext) {
      if (this.currentStep === 5) {
        btnNext.textContent = "✓ LIST MY PRODUCE";
        btnNext.className = "btn btn-accent btn-lg";
      } else {
        btnNext.textContent = "Next Step →";
        btnNext.className = "btn btn-primary";
      }
    }

    // Update Step 5 summary details if on step 5
    if (this.currentStep === 5) {
      const sumCrop = document.getElementById('sum-crop-name');
      const sumQty = document.getElementById('sum-qty');
      const sumQuality = document.getElementById('sum-quality');
      const sumPrice = document.getElementById('sum-price');

      if (sumCrop) sumCrop.textContent = `${this.selectedCrop.emoji} ${this.selectedCrop.name}`;
      if (sumQty) sumQty.textContent = `${this.quantityKg} KG`;
      if (sumQuality) sumQuality.textContent = `Grade ${this.aiQuality.grade} (${this.aiQuality.score}/100 Quality Score)`;
      if (sumPrice) sumPrice.textContent = `₹${this.aiPricing.recommendedMin} – ₹${this.aiPricing.recommendedMax} / kg`;
    }
  }
}

window.KrishiSellWizard = new SellWizard();
