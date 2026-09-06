# KrishiLink AI Backend

Secure FastAPI foundation for the KrishiLink AI agricultural marketplace.
Marketplace, authentication, database, realtime, and AI domain features will be added in later slices.

See [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) for the security review, executable verification results, and production deployment requirements.

## Setup

1. Create a virtual environment and activate it:

   ```bash
   python -m venv .venv
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and replace the placeholder Supabase values. Never commit `.env`.

4. Start the development server from this directory:

   ```bash
   uvicorn app.main:app --reload
   ```

The API is available at `http://localhost:8000`. Check `http://localhost:8000/api/v1/health` and open the development docs at `http://localhost:8000/docs`.

## Authentication

Supabase Auth owns passwords, email verification, sessions, and reset emails. The API validates Supabase JWTs before serving protected routes. Apply `supabase/migrations/001_profiles.sql` before using profile endpoints.

| Method | Endpoint | Auth |
| --- | --- | --- |
| `POST` | `/api/v1/auth/register` | Public |
| `POST` | `/api/v1/auth/login` | Public |
| `GET` | `/api/v1/auth/me` | Bearer JWT |
| `POST` | `/api/v1/auth/logout` | Bearer JWT |
| `POST` | `/api/v1/auth/forgot-password` | Public |
| `POST` | `/api/v1/auth/reset-password` | Bearer JWT |
| `GET` | `/api/v1/auth/profiles/me` | Bearer JWT |
| `PATCH` | `/api/v1/auth/profiles/me` | Bearer JWT |
| `GET` | `/api/v1/auth/profiles` | Admin Bearer JWT |

Send tokens as `Authorization: Bearer <access-token>`. Role checks use server-managed Supabase `app_metadata.role`; user-editable metadata is never used for authorization. Configure either `SUPABASE_JWT_SECRET` or `SUPABASE_JWKS_URL` for JWT verification.

The profile migration enables RLS on `users`, `farmer_profiles`, and `buyer_profiles`. Farmers and buyers can update only their own role-specific row. Admins can read all profiles, while cross-role profile access and edits are denied by both the API and database policies.

## Farms and Produce

Apply `supabase/migrations/002_farms_produce.sql` after the profile migration. It creates farms, crop categories, produce listings, produce images, the private `produce-images` Storage bucket, and RLS policies.

All endpoints below are under `/api/v1`:

| Method | Endpoint | Auth |
| --- | --- | --- |
| `POST` | `/farms` | Farmer JWT |
| `GET` | `/farms` | Farmer JWT |
| `POST` | `/listings` | Farmer JWT |
| `GET` | `/listings` | Public active listings; farmer JWT sees own listings |
| `GET` | `/listings/{id}` | Public active listing; farmer JWT sees own listing |
| `PUT` | `/listings/{id}` | Owner farmer JWT |
| `DELETE` | `/listings/{id}` | Owner farmer JWT |
| `POST` | `/listings/{id}/images` | Owner farmer JWT, JPEG/PNG/WebP, max 5 MB |

Listing images are stored under `{farmer_id}/{listing_id}/{uuid}.ext`. The API validates content type and size, while Supabase Storage policies enforce that the first path segment matches the authenticated farmer.

## Marketplace

Apply `supabase/migrations/003_marketplace.sql` after the farm/produce migration. It creates `buyer_demands`, `offers`, `negotiations`, and `negotiation_messages`, enables RLS, prevents duplicate pending/accepted offers for the same buyer and listing, and adds the three collaboration tables to `supabase_realtime`.

All marketplace endpoints require an authenticated JWT:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/marketplace/listings` | Search active produce with crop, location, price, quantity, quality, and verified-farmer filters |
| `POST` | `/demands` | Buyer creates a demand request |
| `GET` | `/demands` | Authenticated users browse demand requests |
| `POST` | `/offers` | Buyer makes a validated offer on an active listing |
| `GET` | `/offers` | Buyer sees own offers; farmer sees offers on own listings |
| `PATCH` | `/offers/{id}` | Farmer accepts or rejects a pending offer |
| `POST` | `/negotiations` | Offer participants open a negotiation |
| `POST` | `/negotiations/{id}/messages` | Participant sends a message |
| `GET` | `/negotiations/{id}/messages` | Participant reads messages |

Subscribe from a Supabase client to `postgres_changes` on `offers`, `negotiations`, and `negotiation_messages`, filtered by the relevant listing, buyer, farmer, or negotiation ID. RLS controls which realtime rows each authenticated user can receive.

## AI Services

Apply `supabase/migrations/004_ai_predictions.sql` after the marketplace migration. It creates `price_predictions`, `demand_forecasts`, and `buyer_matches` and adds buyer scoring inputs for payment reliability and pickup availability.

AI endpoints require authentication and store each result without exposing model internals:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/ai/price` | Predict price, range, recommendation, and confidence |
| `POST` | `/ai/demand` | Forecast demand level and confidence |
| `POST` | `/ai/matching/{listing_id}` | Rank buyers for a farmer-owned listing |

The prototype implementations live in `app/services/price_ai.py`, `demand_ai.py`, and `matching_ai.py`. They conform to the contracts in `app/ai/interfaces.py`, so trained models can replace the implementations without changing routes or persistence. Matching responses expose only sanitized buyer identifiers, business names, scores, and explanations; private buyer scoring inputs remain server-side.

## Orders

Apply `supabase/migrations/005_orders.sql` after the marketplace migration. Orders are created only through `POST /orders/from-offer/{offer_id}` after the referenced offer is accepted. The database function locks the offer and listing, validates available quantity, prevents duplicate orders through the unique offer constraint, creates the order item and initial history row, and decrements the listing in one transaction.

Order endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/orders/from-offer/{offer_id}` | Create an order from an accepted offer |
| `GET` | `/orders` | List orders visible to the authenticated farmer or buyer |
| `GET` | `/orders/{id}` | View one authorized order with items and status history |
| `PATCH` | `/orders/{id}/status` | Advance one valid lifecycle state |

The only valid progression is `pending -> confirmed -> pickup_scheduled -> collected -> quality_check -> in_transit -> delivered -> completed`. Every transition is recorded in `order_status_history`. `orders` and `order_status_history` are enabled for Supabase Realtime; subscribe to `postgres_changes` filtered by order ID for live status updates.

## Logistics

Apply `supabase/migrations/006_logistics.sql` after the orders migration. It creates `deliveries`, `vehicles`, and `vehicle_locations`, enables RLS, and adds deliveries and locations to Supabase Realtime.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/deliveries` | Logistics/admin creates a delivery for an order |
| `GET` | `/deliveries` | Farmer, buyer, or assigned driver views authorized deliveries |
| `GET` | `/deliveries/{id}` | View one authorized delivery and ETA |
| `PATCH` | `/deliveries/{id}/assignment` | Logistics/admin assigns driver, vehicle, and pickup time |
| `PATCH` | `/deliveries/{id}/status` | Update pickup/delivery status |
| `GET` | `/deliveries/{id}/locations` | Read the location history |
| `POST` | `/deliveries/{id}/location` | Assigned driver sends a location update |
| `POST` | `/deliveries/{id}/route` | Logistics/admin stores an optimized route |
| `POST` | `/vehicles` | Logistics/admin registers a vehicle |
| `GET` | `/vehicles` | Logistics/admin lists vehicles |

Location coordinates are validated, throttled to one update per 10 seconds per driver, and checked again by the `record_vehicle_location` database function. Subscribe to `postgres_changes` on `deliveries` and `vehicle_locations` for pickup status, delivery status, and live vehicle updates.

## Quality and Disputes

Apply `supabase/migrations/007_quality_disputes.sql` after logistics. It creates `quality_inspections`, `disputes`, `dispute_evidence`, and `audit_logs`, plus a private `dispute-evidence` Storage bucket.

Quality inspection statuses are `APPROVED`, `REJECTED`, and `ISSUE_FOUND`. Disputes progress only as `OPEN -> UNDER_REVIEW -> REFUND` or `REPLACEMENT` -> `RESOLVED`.

| Method | Endpoint | Access |
| --- | --- | --- |
| `POST` | `/orders/{id}/quality-inspections` | Logistics/admin inspector |
| `PATCH` | `/quality-inspections/{id}/confirm` | Buyer on the order |
| `POST` | `/disputes` | Buyer or farmer participant |
| `GET` | `/disputes` | Order participants/admin through RLS |
| `POST` | `/disputes/{id}/evidence` | Buyer or farmer participant |
| `PATCH` | `/disputes/{id}/review` | Admin |
| `PATCH` | `/disputes/{id}/decision` | Admin, `REFUND` or `REPLACEMENT` |
| `PATCH` | `/disputes/{id}/resolve` | Admin |

Evidence is restricted to JPEG, PNG, WebP, and PDF files up to 10 MB. Audit rows are written for inspection, confirmation, dispute, evidence, decision, and resolution actions.

## Ratings and Trust

Apply `supabase/migrations/009_ratings_trust.sql` after payments. Reviews can only be created through a completed order, by one of that order's participants, for the other participant. The unique `(order_id, reviewer_id)` constraint and the database function prevent duplicate and self-reviews.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/reviews` | Create one completed-order review |
| `GET` | `/users/{id}/reviews` | View a user's reviews |
| `GET` | `/trust-scores/me` | Get the authenticated user's score and badges |
| `GET` | `/trust-scores/{id}` | View an authorized user's score and badges |

Trust scores are stored from `0` to `100` and combine successful orders, quality score, delivery reliability, payment reliability, ratings, and unresolved dispute history. Badges are derived server-side: `Verified Farmer`, `Trusted Seller`, `Quality Champion`, and `Reliable Buyer`. Scores refresh when reviews are created and when they are read, without allowing clients to edit score components.

## Notifications

Apply `supabase/migrations/010_notifications.sql` after the ratings migration. It creates the user-owned `notifications` stream and `notification_preferences`, enables RLS, and publishes notifications through Supabase Realtime.

Notification types are `ORDER`, `PAYMENT`, `BUYER`, `AI_ALERT`, `LOGISTICS`, `WEATHER`, `QUALITY`, and `DISPUTE`. Existing offer, order, delivery, payment, AI prediction, quality, and dispute events create notifications through database triggers, honoring each user's preferences.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/notifications` | List notifications, optionally with `unread_only=true` |
| `GET` | `/notifications/unread-count` | Return unread count |
| `PATCH` | `/notifications/{id}/read` | Mark one notification as read |
| `POST` | `/notifications/read-all` | Mark all own notifications as read |
| `GET` | `/notification-preferences` | Read own notification preferences |
| `PUT` | `/notification-preferences` | Update own type preferences |

Subscribe to `postgres_changes` on `notifications` with a filter for `user_id=eq.<current-user-id>`. RLS prevents cross-user reads, updates, and Realtime delivery.

## Payments and Settlements

Apply `supabase/migrations/008_payments_settlements.sql` after the quality/dispute migration. It creates `payments` and `settlements` without storing card details, UPI credentials, bank credentials, or payment-provider secrets.

Payment flow:

```text
ORDER CONFIRMED -> PAYMENT_PENDING -> PAYMENT_AUTHORIZED -> ESCROW
-> DELIVERY_CONFIRMED -> SETTLEMENT -> FARMER_PAID
```

| Method | Endpoint | Access |
| --- | --- | --- |
| `POST` | `/payments` | Buyer; accepts only order ID and idempotency key |
| `POST` | `/payments/{id}/simulate` | Buyer; prototype authorization and escrow |
| `POST` | `/payments/{id}/delivery-confirmed` | Buyer, logistics, or admin after delivery |
| `POST` | `/payments/{id}/release` | Logistics/admin after delivery confirmation |
| `GET` | `/payments` | Authorized payment participants through RLS |
| `GET` | `/settlements` | Farmer/admin/logistics through RLS |

Gross amount is read from the confirmed order inside the database transaction. The prototype calculates a 5% logistics fee, 2% platform fee, and the remaining net farmer settlement. Idempotency keys and unique order/payment constraints prevent duplicate payments and settlements. Payment and settlement tables are enabled for Supabase Realtime, and all payment changes write audit records.

## Structure

```text
app/
  ai/             AI integrations
  api/v1/         Versioned HTTP routes
  core/           Settings and logging
  middleware/     Centralized exception handling
  models/         SQLAlchemy models
  schemas/        Pydantic schemas
  services/       Application services
supabase/
   migrations/     Supabase schema and Row Level Security policies
```