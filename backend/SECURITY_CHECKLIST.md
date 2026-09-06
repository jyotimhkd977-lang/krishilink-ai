# KrishiLink AI Backend Security Checklist

Review date: 2026-09-06

## Authentication

- [x] Supabase Auth owns registration, passwords, sessions, reset emails, and email verification.
  Evidence: `app/services/auth.py`, `/api/v1/auth/*` routes.
- [x] JWT signature, issuer, audience, subject, and expiration are validated.
  Evidence: `app/core/security.py`; expired-token test passed.
- [x] Password reset uses the authenticated Supabase token and generic responses.
  Evidence: `app/api/v1/routes/auth.py`.
- [x] Email verification is required at login when `REQUIRE_EMAIL_VERIFICATION=true`.
  Evidence: `app/services/auth.py`, `.env.example`.
- [x] Passwords, access tokens, and provider credentials are never stored by the application.

## Authorization

- [x] Role-based dependencies cover farmer, buyer, fpo, logistics, and admin roles.
  Evidence: `app/core/security.py` and route dependencies.
- [x] Public registration cannot provision `admin` or `logistics`; those roles require administrator provisioning.
- [x] Resource ownership is checked in service code and database policies.
- [x] Supabase RLS is enabled across profiles, farms, listings, marketplace, orders, logistics, quality, payments, trust, and notifications.
  Evidence: migrations `001_profiles.sql` through `010_notifications.sql`.
- [x] Notification reads and writes are scoped to `auth.uid()`.

## API Security

- [x] HTTPS redirect and HSTS are available with `FORCE_HTTPS=true`.
- [x] Trusted hosts are enforced through `TrustedHostMiddleware`.
- [x] CORS uses an explicit allowlist; wildcard origins are rejected.
- [x] Rate limiting exists for all `/api` requests, login attempts by IP/email, and driver location updates.
- [x] Request content length is limited by `MAX_REQUEST_BYTES`.
- [x] Pydantic validates request types, ranges, lengths, enums, and identifiers at the API boundary.
- [x] Validation errors return generic messages without echoing invalid inputs.
- [x] Unhandled errors return generic responses; internal details are logged server-side.
- [x] Security headers include `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy`.

## Database

- [x] Foreign keys and check constraints protect ownership, quantities, amounts, statuses, and score ranges.
- [x] Critical order, payment, settlement, location, review, and trust operations use database functions/transactions.
- [x] Order and dispute state transitions reject invalid skips.
- [x] Duplicate orders, payments, settlements, offers, and reviews are blocked by unique constraints/indexes.
- [x] Status histories and audit records are written for critical changes.
- [x] Realtime tables use replica identity where update payloads require it.

## File Security

- [x] Produce and dispute uploads allow only approved MIME types.
- [x] File signatures are checked against declared MIME types.
- [x] Produce images are limited to 5 MB; dispute evidence is limited to 10 MB.
- [x] Storage buckets are private.
- [x] Storage RLS checks uploader ownership and dispute/listing ownership.
- [x] Signed URLs expire after 300 seconds and are issued only after ownership/visibility checks.

## Payment Security

- [x] Client requests contain only order ID and idempotency key; amount is read from the confirmed order in SQL.
- [x] Logistics fee, platform fee, and farmer net settlement are calculated server-side.
- [x] Idempotency keys are unique and scoped to the original buyer.
- [x] One payment per order and one settlement per payment are enforced.
- [x] Payment and settlement transitions are audited.
- [x] No card, UPI, bank, wallet, or payment-provider credentials are stored.

## Logging and Audit

- [x] JSON structured logs are enabled.
- [x] Failed login and rate-limit security events are logged without passwords or tokens.
- [x] A log filter redacts bearer tokens, passwords, API keys, secrets, and credentials.
- [x] `audit_logs` records payment, settlement, review, quality, dispute, and evidence actions.
- [x] Audit data is protected by RLS.

## Verification performed

The following executable checks passed during this review:

- Backend compilation and diagnostics.
- OpenAPI route registration across all modules.
- Expired JWT rejection and generic 401 response.
- Missing-token rejection.
- Buyer-to-farmer RBAC denial for farmer-only routes.
- Security headers on `/api/v1/health`.
- Request-size rejection at 413.
- Disallowed CORS origin rejection.
- Privileged-role registration rejection.
- JPEG/PDF magic-byte validation and invalid-signature rejection.
- Log redaction for bearer tokens, passwords, and API keys.

## Production deployment requirements

- Set `ENVIRONMENT=production` and `FORCE_HTTPS=true` behind a correctly configured TLS proxy.
- Set explicit production `CORS_ORIGINS` and `TRUSTED_HOSTS`; never use wildcard CORS.
- Keep `.env` outside source control and provide `SUPABASE_SERVICE_ROLE_KEY` only to the backend runtime.
- Apply migrations `001_profiles.sql` through `010_notifications.sql` in order.
- Enable Supabase email confirmation and configure reset/verification redirect URLs.
- The in-memory API/login/location limiters are safe for a single process only. Use Redis or an API gateway limiter before horizontal scaling.
- Review Supabase Storage and Realtime policies after applying migrations in the target project.
