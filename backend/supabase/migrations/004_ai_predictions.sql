-- KrishiLink AI prediction storage and buyer matching inputs.

alter table public.buyer_profiles
    add column if not exists payment_reliability numeric(5, 2) not null default 0
        check (payment_reliability between 0 and 100),
    add column if not exists pickup_available boolean not null default false;

create table if not exists public.price_predictions (
    id uuid primary key default gen_random_uuid(),
    requester_id uuid not null references public.users(id) on delete cascade,
    crop text not null,
    location text not null,
    input_data jsonb not null,
    predicted_price numeric(12, 2) not null check (predicted_price >= 0),
    price_range jsonb not null,
    recommendation text not null,
    confidence_score numeric(5, 2) not null check (confidence_score between 0 and 100),
    model_version text not null default 'prototype-v1',
    created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.demand_forecasts (
    id uuid primary key default gen_random_uuid(),
    requester_id uuid not null references public.users(id) on delete cascade,
    crop text not null,
    location text not null,
    input_data jsonb not null,
    predicted_demand numeric(14, 2) not null check (predicted_demand >= 0),
    demand_level text not null check (demand_level in ('low', 'medium', 'high')),
    confidence numeric(5, 2) not null check (confidence between 0 and 100),
    model_version text not null default 'prototype-v1',
    created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.buyer_matches (
    id uuid primary key default gen_random_uuid(),
    listing_id uuid not null references public.produce_listings(id) on delete cascade,
    farmer_id uuid not null references public.users(id) on delete cascade,
    buyer_id uuid not null references public.users(id) on delete cascade,
    match_score numeric(5, 2) not null check (match_score between 0 and 100),
    explanation text not null,
    model_version text not null default 'prototype-v1',
    created_at timestamptz not null default timezone('utc', now()),
    unique (listing_id, buyer_id)
);

create index if not exists price_predictions_requester_idx on public.price_predictions(requester_id, created_at desc);
create index if not exists demand_forecasts_requester_idx on public.demand_forecasts(requester_id, created_at desc);
create index if not exists buyer_matches_listing_idx on public.buyer_matches(listing_id, match_score desc);

alter table public.price_predictions enable row level security;
alter table public.demand_forecasts enable row level security;
alter table public.buyer_matches enable row level security;

create policy "Users manage their own price predictions"
on public.price_predictions for all
using (requester_id = auth.uid()) with check (requester_id = auth.uid());

create policy "Users manage their own demand forecasts"
on public.demand_forecasts for all
using (requester_id = auth.uid()) with check (requester_id = auth.uid());

create policy "Farmers view matches for own listings"
on public.buyer_matches for select
using (farmer_id = auth.uid());

create policy "Admins view all buyer matches"
on public.buyer_matches for select
using ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

create policy "Backend can write buyer matches"
on public.buyer_matches for insert
with check (farmer_id = auth.uid() or (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');