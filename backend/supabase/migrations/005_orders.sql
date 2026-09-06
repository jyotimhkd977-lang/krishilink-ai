-- KrishiLink AI order lifecycle, transactional creation, and status history.

create table if not exists public.orders (
    id uuid primary key default gen_random_uuid(),
    offer_id uuid not null unique references public.offers(id) on delete restrict,
    listing_id uuid not null references public.produce_listings(id) on delete restrict,
    buyer_id uuid not null references public.users(id) on delete restrict,
    farmer_id uuid not null references public.users(id) on delete restrict,
    total_amount numeric(14, 2) not null check (total_amount >= 0),
    status text not null default 'pending' check (status in (
        'pending', 'confirmed', 'pickup_scheduled', 'collected',
        'quality_check', 'in_transit', 'delivered', 'completed'
    )),
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.order_items (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null references public.orders(id) on delete cascade,
    listing_id uuid not null references public.produce_listings(id) on delete restrict,
    crop text not null,
    quantity numeric(14, 2) not null check (quantity > 0),
    unit text not null check (unit in ('kg', 'quintal', 'ton', 'piece', 'crate')),
    unit_price numeric(12, 2) not null check (unit_price >= 0),
    created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.order_status_history (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null references public.orders(id) on delete cascade,
    from_status text,
    to_status text not null,
    changed_by uuid not null references public.users(id) on delete restrict,
    changed_at timestamptz not null default timezone('utc', now()),
    note text
);

create index if not exists orders_buyer_idx on public.orders(buyer_id, created_at desc);
create index if not exists orders_farmer_idx on public.orders(farmer_id, created_at desc);
create index if not exists order_status_history_order_idx on public.order_status_history(order_id, changed_at);

drop trigger if exists orders_set_updated_at on public.orders;
create trigger orders_set_updated_at before update on public.orders
for each row execute function public.set_updated_at();

create or replace function public.record_order_status_change()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    if old.status is distinct from new.status then
        insert into public.order_status_history (order_id, from_status, to_status, changed_by)
        values (new.id, old.status, new.status, auth.uid());
    end if;
    return new;
end;
$$;

drop trigger if exists orders_status_history_trigger on public.orders;
create trigger orders_status_history_trigger
after update of status on public.orders
for each row execute function public.record_order_status_change();

create or replace function public.create_order_from_offer(p_offer_id uuid)
returns public.orders
language plpgsql
security definer
set search_path = public
as $$
declare
    selected_offer public.offers%rowtype;
    selected_listing public.produce_listings%rowtype;
    new_order public.orders%rowtype;
begin
    select * into selected_offer
    from public.offers
    where id = p_offer_id
    for update;

    if selected_offer.id is null or selected_offer.status <> 'accepted' then
        raise exception 'Offer must be accepted before creating an order';
    end if;
    if auth.uid() <> selected_offer.buyer_id and auth.uid() <> (
        select farmer_id from public.produce_listings where id = selected_offer.listing_id
    ) then
        raise exception 'Order participant is not authorized';
    end if;

    select * into selected_listing from public.produce_listings
    where id = selected_offer.listing_id for update;
    if selected_listing.status <> 'active' or selected_offer.quantity > selected_listing.quantity then
        raise exception 'Listing quantity is no longer available';
    end if;

    insert into public.orders (offer_id, listing_id, buyer_id, farmer_id, total_amount)
    values (
        selected_offer.id,
        selected_offer.listing_id,
        selected_offer.buyer_id,
        selected_listing.farmer_id,
        selected_offer.quantity * selected_offer.offered_price
    )
    returning * into new_order;

    insert into public.order_items (order_id, listing_id, crop, quantity, unit, unit_price)
    values (new_order.id, selected_listing.id, selected_listing.crop, selected_offer.quantity, selected_offer.unit, selected_offer.offered_price);

    insert into public.order_status_history (order_id, from_status, to_status, changed_by)
    values (new_order.id, null, 'pending', auth.uid());

    update public.produce_listings
    set quantity = quantity - selected_offer.quantity,
        status = case when quantity - selected_offer.quantity = 0 then 'sold' else status end
    where id = selected_listing.id;

    return new_order;
exception
    when unique_violation then
        raise exception 'An order already exists for this offer';
end;
$$;

create or replace function public.advance_order_status(p_order_id uuid, p_next_status text)
returns public.orders
language plpgsql
security definer
set search_path = public
as $$
declare
    current_order public.orders%rowtype;
    allowed boolean := false;
    changed_order public.orders%rowtype;
begin
    select * into current_order from public.orders where id = p_order_id for update;
    if current_order.id is null then raise exception 'Order not found'; end if;
    if auth.uid() <> current_order.buyer_id and auth.uid() <> current_order.farmer_id
        and (auth.jwt() -> 'app_metadata' ->> 'role') not in ('logistics', 'admin') then
        raise exception 'Order participant is not authorized';
    end if;

    allowed := (current_order.status, p_next_status) in (
        ('pending', 'confirmed'),
        ('confirmed', 'pickup_scheduled'),
        ('pickup_scheduled', 'collected'),
        ('collected', 'quality_check'),
        ('quality_check', 'in_transit'),
        ('in_transit', 'delivered'),
        ('delivered', 'completed')
    );
    if not allowed then raise exception 'Invalid order status transition'; end if;

    update public.orders set status = p_next_status where id = p_order_id returning * into changed_order;
    return changed_order;
end;
$$;

alter table public.orders enable row level security;
alter table public.order_items enable row level security;
alter table public.order_status_history enable row level security;
alter table public.orders replica identity full;
alter table public.order_status_history replica identity full;

create policy "Participants view their orders"
on public.orders for select
using (
    buyer_id = auth.uid() or farmer_id = auth.uid()
    or (auth.jwt() -> 'app_metadata' ->> 'role') in ('logistics', 'admin')
);

create policy "Participants view order items"
on public.order_items for select
using (exists (
    select 1 from public.orders order_row
    where order_row.id = order_id
    and (order_row.buyer_id = auth.uid() or order_row.farmer_id = auth.uid()
         or (auth.jwt() -> 'app_metadata' ->> 'role') in ('logistics', 'admin'))
));

create policy "Participants view status history"
on public.order_status_history for select
using (exists (
    select 1 from public.orders order_row
    where order_row.id = order_id
    and (order_row.buyer_id = auth.uid() or order_row.farmer_id = auth.uid()
         or (auth.jwt() -> 'app_metadata' ->> 'role') in ('logistics', 'admin'))
));

do $$
begin
    alter publication supabase_realtime add table public.orders;
exception when duplicate_object then null;
end $$;
do $$
begin
    alter publication supabase_realtime add table public.order_status_history;
exception when duplicate_object then null;
end $$;