/* ==========================================================================
   KrishiLink AI — Realistic Indian Agricultural Data Store
   Location: Khordha, Bhubaneswar, Odisha
   ========================================================================== */

const KrishiData = {
  farmer: {
    name: "Ramesh Kumar",
    avatar: "assets/images/ramesh.jpg",
    village: "Jatani Block",
    district: "Khordha",
    state: "Odisha",
    locationString: "Khordha, Odisha",
    landSize: "3.5 Acres",
    soilType: "Alluvial Red Loam",
    irrigation: "Canal + Drip Irrigation",
    activeCropsCount: 4,
    totalSoldKg: 12500,
    totalLifetimeSales: 480000,
    trustScore: 94,
    successfulOrders: 38,
    onTimePickupRate: 96,
    qualityPassRate: 98.5,
    kccNumber: "KCC-OD-KHR-882194",
    bankAccount: "State Bank of India (Jatani Branch) •••• 4819",
    upiId: "ramesh.farmer@sbi"
  },

  weather: {
    temp: 31,
    condition: "Sunny / Partial Clouds",
    humidity: 72,
    rainProb: 20,
    wind: "8 km/h ENE",
    uvIndex: "Moderate (5)",
    forecast: [
      { day: "Today", temp: "31°C", icon: "☀️", rain: "20%" },
      { day: "Tomorrow", temp: "29°C", icon: "🌧️", rain: "82%" },
      { day: "Day after", temp: "28°C", icon: "⛈️", rain: "65%" }
    ]
  },

  marketPrices: [
    { id: "tomato", name: "Tomato", hindi: "टमाटर", odia: "ଟମାଟୋ", price: 30.50, unit: "kg", change: 8.2, isUp: true, apmc: "Khordha Mandi", img: "assets/images/tomato.jpg" },
    { id: "potato", name: "Potato", hindi: "आलू", odia: "ଆଳୁ", price: 24.00, unit: "kg", change: 4.1, isUp: true, apmc: "Bhubaneswar Ainthapali", img: "assets/images/potato.jpg" },
    { id: "onion", name: "Onion", hindi: "प्याज", odia: "ପିଆଜ", price: 27.00, unit: "kg", change: -2.3, isUp: false, apmc: "Cuttack Malgodown", img: "assets/images/onion.jpg" },
    { id: "brinjal", name: "Brinjal", hindi: "बैंगन", odia: "ବାଇଗଣ", price: 19.50, unit: "kg", change: 5.0, isUp: true, apmc: "Jatani Rural Haat", img: "assets/images/brinjal.jpg" }
  ],

  aiInsight: {
    crop: "Tomato",
    region: "Khordha & Bhubaneswar Hub",
    demandIncrease: 18,
    timeframe: "next 7 days",
    demandScore: 82,
    priceTrendScore: 74,
    buyerUrgencyScore: 89,
    localSupplyScore: 48,
    currentMarket: 29.00,
    potentialMin: 31.00,
    potentialMax: 34.00,
    recommendedSellKg: "300–500 kg",
    recommendedWindow: "3–5 days",
    summary: "Tomato demand is expected to increase by 18% in your region over the next 7 days due to festive procurement. Local supply is decreasing. AI recommends selling 300–500 kg within the next 3–5 days to maximize revenue."
  },

  myProduce: [
    {
      id: "prod-1",
      name: "Hybrid Red Tomato",
      cropKey: "tomato",
      availableKg: 500,
      harvestDate: "2026-09-08",
      qualityGrade: "Grade A",
      aiQualityScore: 92,
      freshnessScore: 95,
      uniformityScore: 89,
      damagePercent: 4,
      aiPriceMin: 31,
      aiPriceMax: 33,
      status: "Active",
      img: "assets/images/tomato.jpg",
      buyerInterest: "High (4 Bids)",
      tags: ["Organic Traceable", "High Brix", "Pre-Cooled"]
    },
    {
      id: "prod-2",
      name: "Kufri Jyoti Potato",
      cropKey: "potato",
      availableKg: 300,
      harvestDate: "2026-09-12",
      qualityGrade: "Grade A",
      aiQualityScore: 90,
      freshnessScore: 92,
      uniformityScore: 88,
      damagePercent: 3,
      aiPriceMin: 25,
      aiPriceMax: 27,
      status: "Active",
      img: "assets/images/potato.jpg",
      buyerInterest: "Moderate (2 Bids)",
      tags: ["Sorted & Graded", "Low Moisture"]
    },
    {
      id: "prod-3",
      name: "Nasik Red Onion",
      cropKey: "onion",
      availableKg: 450,
      harvestDate: "2026-09-15",
      qualityGrade: "Grade A",
      aiQualityScore: 94,
      freshnessScore: 96,
      uniformityScore: 91,
      damagePercent: 2,
      aiPriceMin: 28,
      aiPriceMax: 31,
      status: "Active",
      img: "assets/images/onion.jpg",
      buyerInterest: "Very High (6 Bids)",
      tags: ["Cured Skin", "Export Quality"]
    },
    {
      id: "prod-4",
      name: "Green Long Brinjal",
      cropKey: "brinjal",
      availableKg: 200,
      harvestDate: "2026-09-07",
      qualityGrade: "Grade A",
      aiQualityScore: 89,
      freshnessScore: 94,
      uniformityScore: 86,
      damagePercent: 5,
      aiPriceMin: 18,
      aiPriceMax: 21,
      status: "Active",
      img: "assets/images/brinjal.jpg",
      buyerInterest: "Moderate (3 Bids)",
      tags: ["Pesticide-Free", "Fresh Farm Pluck"]
    }
  ],

  buyers: [
    {
      id: "buyer-abc",
      name: "ABC Foods India Ltd.",
      type: "Food Processor & Exporter",
      aiMatchScore: 94,
      crop: "Tomato",
      offerPrice: 32.00,
      requiredKg: 500,
      distanceKm: 18,
      location: "Khordha Industrial Estate",
      badges: ["Verified Buyer", "Reliable Payment", "Regular Buyer"],
      paymentTerm: "Instant UPI on Delivery",
      pickupAvailable: true,
      breakdown: {
        priceMatch: 96,
        distanceConvenience: 92,
        paymentSpeed: 98,
        buyerReliability: 95
      }
    },
    {
      id: "buyer-freshmart",
      name: "FreshMart Supermarkets",
      type: "Modern Retail Chain (7 Stores)",
      aiMatchScore: 88,
      crop: "Tomato",
      offerPrice: 31.00,
      requiredKg: 300,
      distanceKm: 12,
      location: "Bhubaneswar Patia",
      badges: ["Verified Buyer", "Fast Payment"],
      paymentTerm: "Same-Day Bank Settlement",
      pickupAvailable: true,
      breakdown: {
        priceMatch: 88,
        distanceConvenience: 95,
        paymentSpeed: 90,
        buyerReliability: 91
      }
    },
    {
      id: "buyer-mayfair",
      name: "Mayfair Hotels & Resorts",
      type: "Hospitality & Dining",
      aiMatchScore: 91,
      crop: "Tomato",
      offerPrice: 33.00,
      requiredKg: 250,
      distanceKm: 22,
      location: "Jaydev Vihar, Bhubaneswar",
      badges: ["Premium Quality Buyer", "Weekly Scheduled"],
      paymentTerm: "Next-Day Direct NEFT",
      pickupAvailable: true,
      breakdown: {
        priceMatch: 98,
        distanceConvenience: 85,
        paymentSpeed: 94,
        buyerReliability: 96
      }
    },
    {
      id: "buyer-fpo",
      name: "Odisha Krushak Producer Co.",
      type: "State Level FPO Federation",
      aiMatchScore: 92,
      crop: "Potato & Onion",
      offerPrice: 28.50,
      requiredKg: 1500,
      distanceKm: 15,
      location: "Baramunda Logistics Hub",
      badges: ["FPO Partner", "Guaranteed Off-take"],
      paymentTerm: "Direct DBT Settlement",
      pickupAvailable: true,
      breakdown: {
        priceMatch: 90,
        distanceConvenience: 94,
        paymentSpeed: 96,
        buyerReliability: 97
      }
    }
  ],

  orders: [
    {
      id: "KL10294",
      crop: "Tomato",
      cropImg: "assets/images/tomato.jpg",
      quantityKg: 500,
      buyer: "ABC Foods India Ltd.",
      unitPrice: 32.00,
      totalAmount: 16000,
      statusStep: 3, // 1: Confirmed, 2: Scheduled, 3: Collected, 4: Transit, 5: Delivered, 6: Settled
      statusText: "Produce Collected & In Transit",
      vehicleNo: "OD-02-AB-1234",
      driverName: "Raju Mohanty",
      driverPhone: "+91 94370 12894",
      pickupETA: "8:22 AM",
      pickupDate: "Today, Sep 6",
      routeSavings: {
        distanceSavedKm: 18,
        fuelSavingsInr: 420,
        co2SavedKg: 14
      }
    },
    {
      id: "KL10288",
      crop: "Potato",
      cropImg: "assets/images/potato.jpg",
      quantityKg: 300,
      buyer: "FreshMart Supermarkets",
      unitPrice: 31.00,
      totalAmount: 9300,
      statusStep: 6,
      statusText: "Payment Released & Transferred",
      vehicleNo: "OD-02-CD-5678",
      driverName: "Bikash Jena",
      driverPhone: "+91 98610 55421",
      pickupETA: "Delivered Yesterday",
      pickupDate: "Sep 5, 2026",
      settlement: {
        gross: 9300,
        logistics: 350,
        platformFee: 140,
        net: 8810
      }
    }
  ],

  earnings: {
    netEarnings: 47850,
    grossSales: 51200,
    logisticsDeduction: 2100,
    platformFee: 1250,
    growthRate: "↑ 26.8%",
    monthlyTrend: [
      { month: "May", amount: 28400 },
      { month: "Jun", amount: 34200 },
      { month: "Jul", amount: 39800 },
      { month: "Aug", amount: 44100 },
      { month: "Sep (MTD)", amount: 47850 }
    ],
    recentTransactions: [
      { id: "TXN-9021", buyer: "ABC Foods", crop: "Tomato (500 kg)", gross: 16000, net: 15180, date: "Today", status: "In Transit Escrow" },
      { id: "TXN-8942", buyer: "FreshMart", crop: "Potato (300 kg)", gross: 9300, net: 8810, date: "Yesterday", status: "Transferred to Bank" },
      { id: "TXN-8815", buyer: "Odisha Retail Hub", crop: "Onion (250 kg)", gross: 7500, net: 7120, date: "Sep 02, 2026", status: "Transferred to Bank" },
      { id: "TXN-8690", buyer: "Mayfair Hotels", crop: "Tomato & Herbs", gross: 15000, net: 14250, date: "Aug 28, 2026", status: "Transferred to Bank" }
    ]
  },

  notifications: [
    { id: "notif-1", category: "AI Alerts", title: "Tomato Demand Surge", desc: "Regional demand jumped 18% in Khordha.", time: "10m ago", icon: "🤖" },
    { id: "notif-2", category: "Logistics", title: "Pickup Vehicle Approaching", desc: "Driver Raju (OD-02-AB-1234) is 12 mins away.", time: "25m ago", icon: "🚚" },
    { id: "notif-3", category: "Buyers", title: "New Offer from ABC Foods", desc: "ABC Foods offered ₹32/kg for 500 kg Tomato.", time: "1h ago", icon: "💰" },
    { id: "notif-4", category: "Weather", title: "Heavy Rain Forecast", desc: "82% chance of rain tomorrow. Finish harvesting.", time: "3h ago", icon: "🌧️" },
    { id: "notif-5", category: "Payments", title: "Payment Released ₹8,810", desc: "Order #KL10288 successfully transferred to SBI A/C 4819.", time: "Yesterday", icon: "🎉" }
  ]
};

window.KrishiData = KrishiData;
