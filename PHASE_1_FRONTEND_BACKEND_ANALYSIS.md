# KrishiLink AI Phase 1 Analysis

Review date: 2026-09-06
Scope: inventory and integration plan only. No frontend runtime behavior was changed in Phase 1.

## Executive Summary

The frontend is a single-page HTML application driven by vanilla JavaScript modules. It has one API client in `js/api.js`, but the main rendering path still reads `window.KrishiData` from `js/data.js`.

The backend is a versioned FastAPI service under `/api/v1` with Supabase Auth, JWT/RBAC, PostgREST services, SQL migrations `001` through `010`, RLS policies, Storage, and Realtime publication setup.

The main integration problem is not the UI structure. It is the data boundary: most UI modules render static objects, mutate local arrays, show alerts, or simulate authentication instead of calling the backend.

## Frontend Inventory

### Files

HTML:

- `index.html` is the only HTML page.
- It contains landing, farmer dashboard, buyer portal, farm, produce, price intelligence, buyer matches, marketplace, orders, logistics, quality, earnings, trust, profile, notifications, auth, sell, negotiation, settlement, and AI assistant views/modals.

CSS:

- `css/design-system.css`
- `css/components.css`
- `css/dashboard.css`
- `css/modals.css`
- `css/landing-auth.css`
- `css/responsive.css`

JavaScript:

- `js/data.js`: static application data source.
- `js/app.js`: dashboard renderer, navigation, alerts, static view actions.
- `js/auth.js`: fake OTP/demo auth plus partial email/password API integration.
- `js/api.js`: current health/auth API client; not yet a complete service layer.
- `js/sell-wizard.js`: local produce creation and simulated AI quality/price.
- `js/consumer.js`: local cart and simulated checkout.
- `js/negotiation.js`: local offer/order mutation and simulated negotiation.
- `js/logistics-map.js`: hardcoded SVG route, driver, and alert.
- `js/ai-assistant.js`: hardcoded agricultural responses and simulated voice fallback.
- `js/i18n.js`: language preference and translations.
- `js/audio.js`: UI sound effects.

Assets:

- `assets/images/` contains local presentation images currently used as static crop/avatar assets.

### Hardcoded data locations

`js/data.js` contains the primary demo store:

- farmer identity, location, farm size, trust score, KCC/bank/UPI display data
- weather and forecast
- market prices
- AI insight and recommendation values
- four produce listings
- four buyers and match scores
- two orders and status steps
- earnings, trends, and transactions
- five notifications

Additional hardcoded/demo data exists outside `data.js`:

- `js/auth.js`: Ramesh/Priya users, simulated OTP `4819`, demo login buttons, local session objects.
- `js/sell-wizard.js`: default tomato, quantity, location, quality score, price range, and local listing insertion.
- `js/negotiation.js`: default buyer/offer/AI price, random local order ID, local order insertion.
- `js/consumer.js`: pre-filled cart item, farmer/price/image defaults, local checkout.
- `js/logistics-map.js`: Farmer A/B, Khordha farm, ABC Foods, driver call text, animated fake truck.
- `js/ai-assistant.js`: hardcoded price, demand, buyer, earnings answers and random voice fallback prompt.
- `js/app.js`: hardcoded UI strings and alert-backed payout/dispute/AI-score actions.
- `index.html`: static cards for produce, buyers, marketplace demands, logistics, quality, and settlement.

### Storage and session usage

`localStorage` is currently used for:

- `krishilink_access_token` in `js/api.js`
- `krishilink_auth_user` in `js/auth.js`
- `krishilink_lang` in `js/i18n.js`

`sessionStorage` usage: none found.

Security note: the frontend token is currently persisted in `localStorage`. Phase 2 should document the tradeoff and centralize session handling. No service-role key may ever move to frontend code.

### Fake authentication

Current behavior:

- Farmer flow asks for a phone number but does not call an OTP backend.
- OTP is auto-filled with a hardcoded value and accepted locally.
- `submitOtp()` creates a local farmer or consumer object.
- Quick demo login buttons create local sessions.
- Email/password login and registration were partially added through `/auth/login` and `/auth/register`, but the same modal still exposes fake farmer OTP and demo paths.
- Buyer role is mapped to frontend role `consumer`, while backend role is `buyer`; this must be normalized in the service boundary.

Required backend alignment before implementation:

- Add a real Supabase phone OTP route/service or use the Supabase Auth client directly for `signInWithOtp` and OTP verification.
- Add farmer profile completion fields supported by the database: block/tehsil, pincode, farm name, units, crops, language, and profile photo need schema/API support before the form can persist them.
- Add buyer registration fields to backend schemas/profile tables.
- Return `profile_completed` from `/auth/me` or a profile endpoint.

### Alerts, fake success, and unsubmitted actions

`alert()` calls were found in:

- `js/app.js`: payout initiated, produce management, AI buyer detail, dispute.
- `js/auth.js`: invalid phone, simulated OTP, fake welcome.
- `js/consumer.js`: empty cart and fake order.
- `js/logistics-map.js`: fake driver call.
- `js/negotiation.js`: accept/counter validation and fake deal closure.
- `js/sell-wizard.js`: fake listing success.

`prompt()` / `confirm()`: no matches found.

Forms/actions not connected to backend:

- Sell wizard publish.
- Negotiation accept/counter.
- Consumer cart checkout.
- Payout withdrawal.
- Driver call/tracking.
- Quality/dispute controls.
- Settlement modal.
- AI assistant chat.
- Most dashboard renderers.
- Farm management controls.
- Marketplace filters and buyer demand actions.

## Current API Client Findings

`js/api.js` currently supports:

- health check
- register
- login
- current user
- logout
- forgot password
- bearer token attachment

It does not yet expose service methods for farms, listings, marketplace, demands, offers, negotiations, orders, logistics, quality, payments, trust, notifications, uploads, signed URLs, or Realtime subscriptions.

The current API error parser understands the existing backend error envelope and FastAPI `detail`, but the project-wide requested `{success, message, data}` envelope is not implemented consistently in the backend yet. Phase 2 should choose one contract and update both sides before broad service integration.

## Backend Endpoint and Table Map

| Current frontend area | Backend API target | Database/storage target | Phase 2 notes |
|---|---|---|---|
| Farmer phone auth | Missing real phone OTP endpoints; existing `/api/v1/auth/me` | Supabase Auth + `users` | Add OTP provider flow; never simulate OTP. |
| Buyer email auth | `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/me` | Supabase Auth + `users` + `buyer_profiles` | Expand buyer registration fields. |
| Farmer profile | `/api/v1/auth/profiles/me` | `users`, `farmer_profiles` | Add missing block, pincode, crops, language, photo fields. |
| Buyer profile | `/api/v1/auth/profiles/me` | `users`, `buyer_profiles` | Add phone, district, state, pincode, complete business fields. |
| Dashboard | No consolidated dashboard endpoint | orders, listings, payments, settlements, trust_scores, notifications | Add read aggregation endpoints or parallel service calls. |
| My Farm | `GET /api/v1/farms`; create exists; update/delete missing | `farms` | Add `PUT` and `DELETE` endpoints plus coordinates/crops. |
| My Produce | `GET/POST/PUT/DELETE /api/v1/listings*` | `produce_listings`, `produce_images` | Replace static cards; add upload/signed URL service. |
| AI quality | No `/ai/quality-check` endpoint | quality inspection tables are order-based | Add image quality endpoint and response contract. |
| AI price | Existing `/api/v1/ai/price` | `price_predictions` | Adapt frontend payload to current fields; requested `/price-predict` is not current path. |
| AI demand | Existing `/api/v1/ai/demand` | `demand_forecasts` | Connect buyer/farmer views to real input data. |
| Marketplace | Existing `/api/v1/marketplace/listings` | `produce_listings`, profiles, images | Add sort and buyer-facing public/auth behavior as required. |
| Buyer demands | Existing `/api/v1/demands` | `buyer_demands` | Current schema lacks delivery date and verified buyer filtering. |
| Offers | Existing `POST/GET /api/v1/offers`, `PATCH /offers/{id}` | `offers` | Add explicit accept/reject/counter endpoint aliases or update frontend to current contract. |
| Negotiation | Existing negotiation/message routes | `negotiations`, `negotiation_messages` | Add Supabase Realtime client subscription. |
| Orders | Existing `/api/v1/orders*` | `orders`, `order_items`, `order_status_history` | Create only from accepted offer; map backend statuses to UI timeline. |
| Logistics | Existing `/api/v1/deliveries*`, `/vehicles` | `deliveries`, `vehicles`, `vehicle_locations` | Replace fake SVG route; subscribe to Realtime locations/status. |
| Payments | Existing `/api/v1/payments*`, `/settlements` | `payments`, `settlements`, `audit_logs` | Frontend sends only order ID/idempotency key; never calculates money. |
| Reviews/trust | Existing `/api/v1/reviews`, `/trust-scores*` | `reviews`, `trust_scores` | Connect completed-order review form and score cards. |
| Notifications | Existing `/api/v1/notifications*` | `notifications`, `notification_preferences` | Add notification center, unread count, mark-read, preferences, Realtime. |
| Storage | Existing upload/signed URL routes | Supabase Storage + image/evidence tables | Keep buckets private; use short-lived signed URLs. |

## Important Backend Contract Gaps Found

These are not frontend rewrites; they are API prerequisites for the requested real flows:

1. Farmer phone OTP is not implemented; current frontend OTP is simulated.
2. Farmer and buyer registration schemas do not contain all requested final fields.
3. `/auth/me` does not return `profile_completed`.
4. Dashboard aggregation endpoints do not exist.
5. Farm update/delete endpoints do not exist.
6. AI quality-check endpoint does not exist.
7. Buyer demand lacks delivery date in the current schema.
8. Current offer decision is a generic PATCH rather than the requested accept/reject/counter routes.
9. Frontend requested `/payments/my`, `/settlements/my`, and `/trust-score/me`; current backend uses `/payments`, `/settlements`, and `/trust-scores/me`.
10. Backend responses are not consistently wrapped in the requested `{success, message, data}` envelope.
11. Supabase Realtime client subscription helpers are not present in the frontend.
12. Weather data provider/endpoint is not present; weather must remain an explicit unavailable state until added.

## Proposed Integration Plan

### Phase 1 — Completed in this document

- Inventory frontend files and hardcoded data.
- Inventory local/session storage and fake auth.
- Inventory alerts and unsubmitted actions.
- Map frontend components to API endpoints and tables.
- Identify backend contract gaps and security blockers.

### Phase 2 — Central API and UI state layer

- Create one API configuration and service modules.
- Add one API error handler, loading/empty/error states, retry helpers, and toast system.
- Add safe DOM rendering helpers; avoid interpolating untrusted API data into `innerHTML`.
- Preserve the existing HTML/CSS/navigation.

### Phase 3 — Real authentication and profile completion

- Implement Supabase phone OTP for farmers.
- Keep email/password for buyers.
- Remove demo login and simulated OTP.
- Restore/validate JWT sessions through `/auth/me`.
- Add farmer/buyer registration forms and backend schema support.
- Enforce role routing and profile completion.

### Phase 4 — Farmer data surfaces

- Connect profile, farms, listings, image uploads, signed URLs, quality, price, dashboard, and trust score.
- Replace static `KrishiData` reads with API calls and real empty/loading/error states.

### Phase 5 — Buyer marketplace

- Connect listing search/filter/sort, demands, offers, negotiation, buyer dashboard, and Realtime messages.

### Phase 6 — Orders through settlement

- Connect order creation/status timeline, logistics/vehicle Realtime, payment simulation, settlement, and earnings.

### Phase 7 — Notifications, reviews, and final audit

- Connect Realtime notification center and preferences.
- Connect completed-order reviews and trust refresh.
- Remove all remaining alerts/demo paths.
- Run end-to-end auth, ownership, invalid transition, upload, payment idempotency, and Realtime tests.

## Phase 1 Decision / Wait Point

Phase 1 analysis is complete. No runtime frontend behavior was changed. The next implementation step should be Phase 2 only after resolving the environment-secret issue and confirming the backend contract decisions above.
