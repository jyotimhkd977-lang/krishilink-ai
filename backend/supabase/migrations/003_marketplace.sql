-- KrishiLink AI marketplace demands, offers, and realtime negotiations.

create table if not exists public.buyer_demands (
    id uuid primary key default gen_random_uuid(),
    buyer_id uuid not null references public.users(id) on delete cascade,
    crop text not null,
    quantity numeric(14, 2) not null check (quantity > 0),
    unit text not null check (unit in ('kg', 'quintal', 'ton', 'piece', 'crate')),
    target_price numeric(12, 2) not null check (target_price >= 0),
    location text not null,
    minimum_quality_score numeric(5, 2) check (minimum_quality_score is null or minimum_quality_score between 0 and 100),
    status text not null default 'open' check (status in ('open', 'fulfilled', 'closed')),
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.offers (
    id uuid primary key default gen_random_uuid(),
    listing_id uuid not null references public.produce_listings(id) on delete cascade,
    buyer_id uuid not null references public.users(id) on delete cascade,
    quantity numeric(14, 2) not null check (quantity > 0),
    unit text not null check (unit in ('kg', 'quintal', 'ton', 'piece', 'crate')),
    offered_price numeric(12, 2) not null check (offered_price >= 0),
    message text,
    status text not null default 'pending' check (status in ('pending', 'accepted', 'rejected', 'withdrawn')),
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create unique index if not exists one_active_offer_per_buyer_listing
on public.offers (listing_id, buyer_id)
where status in ('pending', 'accepted');

create table if not exists public.negotiations (
    id uuid primary key default gen_random_uuid(),
    listing_id uuid not null references public.produce_listings(id) on delete cascade,
    offer_id uuid unique references public.offers(id) on delete set null,
    buyer_id uuid not null references public.users(id) on delete cascade,
    farmer_id uuid not null references public.users(id) on delete cascade,
    status text not null default 'open' check (status in ('open', 'accepted', 'rejected', 'closed')),
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.negotiation_messages (
    id uuid primary key default gen_random_uuid(),
    negotiation_id uuid not null references public.negotiations(id) on delete cascade,
    sender_id uuid not null references public.users(id) on delete cascade,
    message text not null check (char_length(trim(message)) between 1 and 2000),
    created_at timestamptz not null default timezone('utc', now())
);

create index if not exists buyer_demands_open_idx on public.buyer_demands(status, created_at desc);
create index if not exists offers_listing_idx on public.offers(listing_id, status);
create index if not exists negotiations_participants_idx on public.negotiations(buyer_id, farmer_id);
create index if not exists negotiation_messages_idx on public.negotiation_messages(negotiation_id, created_at);

drop trigger if exists buyer_demands_set_updated_at on public.buyer_demands;
create trigger buyer_demands_set_updated_at before update on public.buyer_demands
for each row execute function public.set_updated_at();

drop trigger if exists offers_set_updated_at on public.offers;
create trigger offers_set_updated_at before update on public.offers
for each row execute function public.set_updated_at();

drop trigger if exists negotiations_set_updated_at on public.negotiations;
create trigger negotiations_set_updated_at before update on public.negotiations
for each row execute function public.set_updated_at();

alter table public.buyer_demands enable row level security;
alter table public.offers enable row level security;
alter table public.negotiations enable row level security;
alter table public.negotiation_messages enable row level security;

create policy "Buyers manage their own demands"
on public.buyer_demands for all
using (buyer_id = auth.uid() and (auth.jwt() -> 'app_metadata' ->> 'role') = 'buyer')
with check (buyer_id = auth.uid() and (auth.jwt() -> 'app_metadata' ->> 'role') = 'buyer');

create policy "Authenticated users view open demands"
on public.buyer_demands for select to authenticated
using (status = 'open' or buyer_id = auth.uid());

create policy "Buyers create and manage their own offers"
on public.offers for all
using (buyer_id = auth.uid() and (auth.jwt() -> 'app_metadata' ->> 'role') = 'buyer')
with check (
    buyer_id = auth.uid()
    and (auth.jwt() -> 'app_metadata' ->> 'role') = 'buyer'
    and exists (
        select 1 from public.produce_listings listing
        where listing.id = listing_id and listing.status = 'active'
    )
);

create policy "Farmers view offers for own listings"
on public.offers for select
using (exists (
    select 1 from public.produce_listings listing
    where listing.id = listing_id and listing.farmer_id = auth.uid()
));

create policy "Farmers update offers for own listings"
on public.offers for update
using (exists (
    select 1 from public.produce_listings listing
    where listing.id = listing_id and listing.farmer_id = auth.uid()
))
with check (exists (
    select 1 from public.produce_listings listing
    where listing.id = listing_id and listing.farmer_id = auth.uid()
));

create policy "Negotiation participants can view"
on public.negotiations for select
using (buyer_id = auth.uid() or farmer_id = auth.uid());

create policy "Negotiation participants can create"
on public.negotiations for insert
with check (
    (buyer_id = auth.uid() or farmer_id = auth.uid())
    and exists (
        select 1
        from public.offers offer
        join public.produce_listings listing on listing.id = offer.listing_id
        where offer.id = offer_id
        and offer.buyer_id = buyer_id
        and listing.farmer_id = farmer_id
    )
);

create policy "Negotiation participants can update"
on public.negotiations for update
using (buyer_id = auth.uid() or farmer_id = auth.uid())
with check (buyer_id = auth.uid() or farmer_id = auth.uid());

create policy "Negotiation participants can view messages"
on public.negotiation_messages for select
using (exists (
    select 1 from public.negotiations negotiation
    where negotiation.id = negotiation_id
    and (negotiation.buyer_id = auth.uid() or negotiation.farmer_id = auth.uid())
));

create policy "Negotiation participants can send messages"
on public.negotiation_messages for insert
with check (
    sender_id = auth.uid()
    and exists (
        select 1 from public.negotiations negotiation
        where negotiation.id = negotiation_id
        and (negotiation.buyer_id = auth.uid() or negotiation.farmer_id = auth.uid())
    )
);

-- Supabase Realtime broadcasts row changes for these three collaboration streams.
do $$
begin
    alter publication supabase_realtime add table public.offers;
exception when duplicate_object then null;
end $$;
do $$
begin
    alter publication supabase_realtime add table public.negotiation_messages;
exception when duplicate_object then null;
end $$;
do $$
begin
    alter publication supabase_realtime add table public.negotiations;
exception when duplicate_object then null;
end $$;