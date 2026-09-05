/* ==========================================================================
   KrishiLink AI — Smart Logistics & Route Optimization Map
   Section 14: Dynamic SVG Route Animation & Fuel Savings Indicator
   ========================================================================== */

class LogisticsMap {
  constructor() {
    this.truckPos = 45; // percentage along the route
    this.interval = null;
  }

  init() {
    this.renderMap();
  }

  renderMap() {
    const container = document.getElementById('logistics-svg-map-wrap');
    if (!container) return;

    container.innerHTML = `
      <div style="position: relative; width: 100%; height: 260px; background: linear-gradient(180deg, #EDF7F0 0%, #E2EFE7 100%); border-radius: var(--radius-lg); overflow: hidden; border: 1.5px solid var(--border-soft);">
        <svg viewBox="0 0 700 240" style="width: 100%; height: 100%;">
          <!-- Background Grid / Fields -->
          <pattern id="farmGrid" width="30" height="30" patternUnits="userSpaceOnUse">
            <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(45, 106, 79, 0.08)" stroke-width="1"/>
          </pattern>
          <rect width="100%" height="100%" fill="url(#farmGrid)" />

          <!-- Optimized Curving Path -->
          <path id="routePath" d="M 50,180 C 140,80 220,190 320,120 C 420,50 520,180 640,90" fill="none" stroke="#52B788" stroke-width="6" stroke-linecap="round" stroke-dasharray="8 6"/>

          <!-- Farmer A Stop -->
          <g transform="translate(50, 180)">
            <circle r="14" fill="#FFFFFF" stroke="#2D6A4F" stroke-width="3"/>
            <text y="5" text-anchor="middle" font-size="12" font-weight="bold" fill="#1B4332">A</text>
            <text y="30" text-anchor="middle" font-size="10" font-weight="bold" fill="#3D5A4C">Farmer A (Pipili)</text>
          </g>

          <!-- Farmer B Stop -->
          <g transform="translate(190, 140)">
            <circle r="14" fill="#FFFFFF" stroke="#2D6A4F" stroke-width="3"/>
            <text y="5" text-anchor="middle" font-size="12" font-weight="bold" fill="#1B4332">B</text>
            <text y="30" text-anchor="middle" font-size="10" font-weight="bold" fill="#3D5A4C">Farmer B</text>
          </g>

          <!-- YOUR FARM STOP (Pulsing Spotlight) -->
          <g transform="translate(320, 120)">
            <circle r="26" fill="none" stroke="#E9B949" stroke-width="3" opacity="0.6">
              <animate attributeName="r" values="18;32;18" dur="2s" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="0.8;0;0.8" dur="2s" repeatCount="indefinite"/>
            </circle>
            <circle r="18" fill="#E9B949" stroke="#FFFFFF" stroke-width="3"/>
            <text y="6" text-anchor="middle" font-size="14" font-weight="bold" fill="#0B2319">📍</text>
            <rect x="-65" y="24" width="130" height="24" rx="12" fill="#1B4332"/>
            <text y="40" text-anchor="middle" font-size="10" font-weight="bold" fill="#FFFFFF">YOUR FARM (Khordha)</text>
          </g>

          <!-- Collection Center -->
          <g transform="translate(480, 125)">
            <circle r="16" fill="#FFFFFF" stroke="#0284C7" stroke-width="3"/>
            <text y="5" text-anchor="middle" font-size="14">🏬</text>
            <text y="32" text-anchor="middle" font-size="10" font-weight="bold" fill="#0369A1">AgriHub Center</text>
          </g>

          <!-- Buyer Facility -->
          <g transform="translate(640, 90)">
            <circle r="16" fill="#2D6A4F" stroke="#FFFFFF" stroke-width="3"/>
            <text y="5" text-anchor="middle" font-size="14">🏭</text>
            <text y="32" text-anchor="middle" font-size="10" font-weight="bold" fill="#1B4332">ABC Foods Hub</text>
          </g>

          <!-- Animated Moving Truck Icon -->
          <g id="animated-truck-marker" transform="translate(290, 128)">
            <rect x="-18" y="-12" width="36" height="24" rx="6" fill="#1B4332" stroke="#FFFFFF" stroke-width="2"/>
            <text x="0" y="4" text-anchor="middle" font-size="12">🚚</text>
          </g>
        </svg>

        <!-- Floating Live Tag -->
        <div style="position: absolute; top: 12px; left: 16px; background: rgba(255,255,255,0.95); backdrop-filter: blur(8px); padding: 4px 12px; border-radius: var(--radius-pill); font-size: 0.75rem; font-weight: 800; color: var(--green-800); display: flex; align-items: center; gap: 6px; box-shadow: var(--shadow-sm);">
          <span style="width: 8px; height: 8px; border-radius: 50%; background: #22C55E; display: inline-block;"></span>
          LIVE MULTI-FARM CONSOLIDATED ROUTE
        </div>
      </div>
    `;
  }

  callDriver() {
    window.KrishiAudio.playClick();
    alert("📞 Calling Driver Raju Mohanty (+91 94370 12894)...\nDriver notes: 'Approaching Khordha Jatani gate in 12 mins. Please keep 500 kg crates near farm gate.'");
  }
}

window.KrishiLogistics = new LogisticsMap();
