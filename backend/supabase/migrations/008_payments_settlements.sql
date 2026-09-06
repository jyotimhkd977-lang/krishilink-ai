-- KrishiLink AI prototype payments, escrow, and farmer settlements.
-- No card, UPI, bank, or wallet credentials are stored here.

create table if not exists public.payments (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null unique references public.orders(id) on delete restrict,
    buyer_id uuid not null references public.users(id) on delete restrict,
    farmer_id uuid not null references public.users(id) on delete restrict,
    idempotency_key text not null unique,
    gross_amount numeric(14, 2) not null check (gross_amount >= 0),
    logistics_fee numeric(14, 2) not null check (logistics_fee >= 0),
    platform_fee numeric(14, 2) not null check (platform_fee >= 0),
    net_settlement numeric(14, 2) not null check (net_settlement >= 0),
    status text not null default 'PAYMENT_PENDING' check (status in (
        'PAYMENT_PENDING', 'PAYMENT_AUTHORIZED', 'ESCROW',
        'DELIVERY_CONFIRMED', 'SETTLEMENT', 'FARMER_PAID', 'FAILED'
    )),
    transaction_reference text unique,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.settlements (
    id uuid primary key default gen_random_uuid(),
    payment_id uuid not null unique references public.payments(id) on delete restrict,
    order_id uuid not null unique references public.orders(id) on delete restrict,
    farmer_id uuid not null references public.users(id) on delete restrict,
    amount numeric(14, 2) not null check (amount >= 0),
    status text not null default 'SETTLEMENT' check (status in ('SETTLEMENT', 'FARMER_PAID', 'FAILED')),
    transaction_reference text not null unique,
    paid_at timestamptz,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists payments_buyer_idx on public.payments(buyer_id, created_at desc);
create index if not exists payments_farmer_idx on public.payments(farmer_id, created_at desc);
create index if not exists settlements_farmer_idx on public.settlements(farmer_id, created_at desc);

drop trigger if exists payments_set_updated_at on public.payments;
create trigger payments_set_updated_at before update on public.payments
for each row execute function public.set_updated_at();

drop trigger if exists settlements_set_updated_at on public.settlements;
create trigger settlements_set_updated_at before update on public.settlements
for each row execute function public.set_updated_at();

alter table public.payments enable row level security;
alter table public.settlements enable row level security;

create policy "Payment participants view payments"
on public.payments for select
using (
    buyer_id = auth.uid() or farmer_id = auth.uid()
    or (auth.jwt() -> 'app_metadata' ->> 'role') in ('admin', 'logistics')
);

create policy "Settlement farmers view own settlements"
on public.settlements for select
using (
    farmer_id = auth.uid()
    or (auth.jwt() -> 'app_metadata' ->> 'role') in ('admin', 'logistics')
);

create or replace function public.create_payment_for_order(p_order_id uuid, p_idempotency_key text)
returns public.payments
language plpgsql
security definer
set search_path = public
as $$
declare
    order_row public.orders%rowtype;
    payment_row public.payments%rowtype;
    logistics numeric(14, 2);
    platform numeric(14, 2);
begin
    if p_idempotency_key is null or char_length(trim(p_idempotency_key)) < 8 then
        raise exception 'A valid idempotency key is required';
    end if;

    select * into payment_row from public.payments where idempotency_key = p_idempotency_key;
    if payment_row.id is not null then
        if payment_row.buyer_id <> auth.uid() then raise exception 'Idempotency key is not available'; end if;
        return payment_row;
    end if;

    select * into order_row from public.orders where id = p_order_id for update;
    if order_row.id is null or order_row.status <> 'confirmed' or auth.uid() <> order_row.buyer_id then
        raise exception 'Payment is not available for this order';
    end if;

    logistics := round(order_row.total_amount * 0.05, 2);
    platform := round(order_row.total_amount * 0.02, 2);
    insert into public.payments (
        order_id, buyer_id, farmer_id, idempotency_key,
        gross_amount, logistics_fee, platform_fee, net_settlement
    ) values (
        order_row.id, order_row.buyer_id, order_row.farmer_id, p_idempotency_key,
        order_row.total_amount, logistics, platform,
        greatest(0, order_row.total_amount - logistics - platform)
    ) returning * into payment_row;

    insert into public.audit_logs (actor_id, entity_type, entity_id, action, metadata)
    values (auth.uid(), 'payment', payment_row.id, 'PAYMENT_CREATED', jsonb_build_object('order_id', order_row.id));
    return payment_row;
exception when unique_violation then
    select * into payment_row from public.payments where order_id = p_order_id or idempotency_key = p_idempotency_key limit 1;
    if payment_row.id is not null and payment_row.buyer_id = auth.uid() then return payment_row; end if;
    raise;
end;
$$;

create or replace function public.simulate_payment(p_payment_id uuid)
returns public.payments
language plpgsql
security definer
set search_path = public
as $$
declare
    payment_row public.payments%rowtype;
begin
    select * into payment_row from public.payments where id = p_payment_id for update;
    if payment_row.id is null or auth.uid() <> payment_row.buyer_id or payment_row.status <> 'PAYMENT_PENDING' then
        raise exception 'Payment cannot be simulated';
    end if;
    update public.payments set status = 'PAYMENT_AUTHORIZED', transaction_reference = 'PAY-' || upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 20)) where id = p_payment_id returning * into payment_row;
    insert into public.audit_logs (actor_id, entity_type, entity_id, action) values (auth.uid(), 'payment', p_payment_id, 'PAYMENT_AUTHORIZED');
    update public.payments set status = 'ESCROW' where id = p_payment_id returning * into payment_row;
    insert into public.audit_logs (actor_id, entity_type, entity_id, action) values (auth.uid(), 'payment', p_payment_id, 'PAYMENT_ESCROWED');
    return payment_row;
end;
$$;

create or replace function public.confirm_payment_delivery(p_payment_id uuid)
returns public.payments
language plpgsql
security definer
set search_path = public
as $$
declare
    payment_row public.payments%rowtype;
    order_status text;
begin
    select * into payment_row from public.payments where id = p_payment_id for update;
    select status into order_status from public.orders where id = payment_row.order_id;
    if payment_row.id is null or order_status not in ('delivered', 'completed')
        or (auth.uid() <> payment_row.buyer_id and (auth.jwt() -> 'app_metadata' ->> 'role') not in ('admin', 'logistics'))
        or payment_row.status <> 'ESCROW' then
        raise exception 'Delivery is not confirmed for this payment';
    end if;
    update public.payments set status = 'DELIVERY_CONFIRMED' where id = p_payment_id returning * into payment_row;
    insert into public.audit_logs (actor_id, entity_type, entity_id, action) values (auth.uid(), 'payment', p_payment_id, 'DELIVERY_CONFIRMED');
    return payment_row;
end;
$$;

create or replace function public.release_payment_settlement(p_payment_id uuid)
returns public.settlements
language plpgsql
security definer
set search_path = public
as $$
declare
    payment_row public.payments%rowtype;
    settlement_row public.settlements%rowtype;
    reference text;
begin
    select * into payment_row from public.payments where id = p_payment_id for update;
    if payment_row.id is null or payment_row.status <> 'DELIVERY_CONFIRMED'
        or (auth.jwt() -> 'app_metadata' ->> 'role') not in ('admin', 'logistics') then
        raise exception 'Settlement cannot be released';
    end if;
    select * into settlement_row from public.settlements where payment_id = p_payment_id for update;
    if settlement_row.id is not null then return settlement_row; end if;

    reference := 'SET-' || upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 20));
    update public.payments set status = 'SETTLEMENT' where id = p_payment_id returning * into payment_row;
    insert into public.settlements (payment_id, order_id, farmer_id, amount, transaction_reference)
    values (payment_row.id, payment_row.order_id, payment_row.farmer_id, payment_row.net_settlement, reference)
    returning * into settlement_row;
    update public.settlements set status = 'FARMER_PAID', paid_at = timezone('utc', now()) where id = settlement_row.id returning * into settlement_row;
    update public.payments set status = 'FARMER_PAID' where id = p_payment_id;
    insert into public.audit_logs (actor_id, entity_type, entity_id, action, metadata)
    values (auth.uid(), 'settlement', settlement_row.id, 'FARMER_PAID', jsonb_build_object('payment_id', p_payment_id));
    return settlement_row;
exception when unique_violation then
    select * into settlement_row from public.settlements where payment_id = p_payment_id;
    if settlement_row.id is not null then return settlement_row; end if;
    raise;
end;
$$;

alter table public.payments replica identity full;
alter table public.settlements replica identity full;

do $$
begin
    alter publication supabase_realtime add table public.payments;
exception when duplicate_object then null;
end $$;
do $$
begin
    alter publication supabase_realtime add table public.settlements;
exception when duplicate_object then null;
end $$;