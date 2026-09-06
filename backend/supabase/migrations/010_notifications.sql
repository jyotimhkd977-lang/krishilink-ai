-- KrishiLink AI realtime notifications and per-user preferences.

create table if not exists public.notifications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    type text not null check (type in ('ORDER', 'PAYMENT', 'BUYER', 'AI_ALERT', 'LOGISTICS', 'WEATHER', 'QUALITY', 'DISPUTE')),
    title text not null,
    body text not null,
    data jsonb not null default '{}'::jsonb,
    read_at timestamptz,
    created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.notification_preferences (
    user_id uuid primary key references public.users(id) on delete cascade,
    preferences jsonb not null default '{"ORDER":true,"PAYMENT":true,"BUYER":true,"AI_ALERT":true,"LOGISTICS":true,"WEATHER":true,"QUALITY":true,"DISPUTE":true}'::jsonb,
    updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists notifications_user_unread_idx on public.notifications(user_id, read_at, created_at desc);

alter table public.notifications enable row level security;
alter table public.notification_preferences enable row level security;

create policy "Users access their own notifications"
on public.notifications for all
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy "Users manage their notification preferences"
on public.notification_preferences for all
using (user_id = auth.uid())
with check (user_id = auth.uid());

create or replace function public.notification_enabled(p_user_id uuid, p_type text)
returns boolean
language sql
security definer
set search_path = public
as $$
    select coalesce((select (preferences ->> p_type)::boolean from public.notification_preferences where user_id = p_user_id), true);
$$;

create or replace function public.create_notification(
    p_user_id uuid,
    p_type text,
    p_title text,
    p_body text,
    p_data jsonb default '{}'::jsonb
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
    if public.notification_enabled(p_user_id, p_type) then
        insert into public.notifications (user_id, type, title, body, data)
        values (p_user_id, p_type, p_title, p_body, coalesce(p_data, '{}'::jsonb));
    end if;
end;
$$;

create or replace function public.notify_offer_event()
returns trigger language plpgsql security definer set search_path = public as $$
declare farmer uuid;
begin
    select farmer_id into farmer from public.produce_listings where id = new.listing_id;
    if tg_op = 'INSERT' then
        perform public.create_notification(farmer, 'BUYER', 'New buyer offer', 'A buyer has made an offer on your produce.', jsonb_build_object('offer_id', new.id, 'listing_id', new.listing_id));
    elsif old.status is distinct from new.status and new.status = 'accepted' then
        perform public.create_notification(new.buyer_id, 'BUYER', 'Offer accepted', 'Your offer has been accepted by the farmer.', jsonb_build_object('offer_id', new.id, 'listing_id', new.listing_id));
    end if;
    return new;
end; $$;

drop trigger if exists offers_notification_trigger on public.offers;
create trigger offers_notification_trigger after insert or update of status on public.offers
for each row execute function public.notify_offer_event();

create or replace function public.notify_order_event()
returns trigger language plpgsql security definer set search_path = public as $$
begin
    if old.status is distinct from new.status and new.status = 'confirmed' then
        perform public.create_notification(new.buyer_id, 'ORDER', 'Order confirmed', 'Your order has been confirmed.', jsonb_build_object('order_id', new.id));
        perform public.create_notification(new.farmer_id, 'ORDER', 'Order confirmed', 'An order for your produce has been confirmed.', jsonb_build_object('order_id', new.id));
    end if;
    return new;
end; $$;

drop trigger if exists orders_notification_trigger on public.orders;
create trigger orders_notification_trigger after update of status on public.orders
for each row execute function public.notify_order_event();

create or replace function public.notify_delivery_event()
returns trigger language plpgsql security definer set search_path = public as $$
begin
    if old.status is distinct from new.status then
        if new.status = 'pickup_scheduled' then
            perform public.create_notification(new.farmer_id, 'LOGISTICS', 'Pickup scheduled', 'A pickup has been scheduled for your order.', jsonb_build_object('delivery_id', new.id, 'order_id', new.order_id));
            perform public.create_notification(new.buyer_id, 'LOGISTICS', 'Pickup scheduled', 'Pickup has been scheduled for your order.', jsonb_build_object('delivery_id', new.id, 'order_id', new.order_id));
        elsif new.status = 'en_route' then
            perform public.create_notification(new.farmer_id, 'LOGISTICS', 'Vehicle arriving', 'Your assigned vehicle is on the way.', jsonb_build_object('delivery_id', new.id));
            perform public.create_notification(new.buyer_id, 'LOGISTICS', 'Vehicle arriving', 'The delivery vehicle is on the way.', jsonb_build_object('delivery_id', new.id));
        elsif new.status in ('delivered') then
            perform public.create_notification(new.farmer_id, 'LOGISTICS', 'Delivery completed', 'The order delivery has been completed.', jsonb_build_object('delivery_id', new.id, 'order_id', new.order_id));
            perform public.create_notification(new.buyer_id, 'LOGISTICS', 'Delivery completed', 'Your order has been delivered.', jsonb_build_object('delivery_id', new.id, 'order_id', new.order_id));
        end if;
    end if;
    return new;
end; $$;

drop trigger if exists deliveries_notification_trigger on public.deliveries;
create trigger deliveries_notification_trigger after update of status on public.deliveries
for each row execute function public.notify_delivery_event();

create or replace function public.notify_payment_event()
returns trigger language plpgsql security definer set search_path = public as $$
begin
    if old.status is distinct from new.status and new.status = 'FARMER_PAID' then
        perform public.create_notification(new.farmer_id, 'PAYMENT', 'Payment released', 'Your farmer settlement has been released.', jsonb_build_object('payment_id', new.id, 'order_id', new.order_id));
    end if;
    return new;
end; $$;

drop trigger if exists payments_notification_trigger on public.payments;
create trigger payments_notification_trigger after update of status on public.payments
for each row execute function public.notify_payment_event();

create or replace function public.notify_ai_event()
returns trigger language plpgsql security definer set search_path = public as $$
begin
    perform public.create_notification(new.requester_id, 'AI_ALERT', 'New AI recommendation', 'A new AI recommendation is available.', jsonb_build_object('entity_id', new.id, 'entity_type', tg_table_name));
    return new;
end; $$;

drop trigger if exists price_predictions_notification_trigger on public.price_predictions;
create trigger price_predictions_notification_trigger after insert on public.price_predictions
for each row execute function public.notify_ai_event();
drop trigger if exists demand_forecasts_notification_trigger on public.demand_forecasts;
create trigger demand_forecasts_notification_trigger after insert on public.demand_forecasts
for each row execute function public.notify_ai_event();

create or replace function public.notify_quality_event()
returns trigger language plpgsql security definer set search_path = public as $$
declare buyer uuid; farmer uuid;
begin
    select order_row.buyer_id, order_row.farmer_id into buyer, farmer from public.orders order_row where order_row.id = new.order_id;
    perform public.create_notification(buyer, 'QUALITY', 'Quality inspection updated', 'A quality inspection is available for your order.', jsonb_build_object('inspection_id', new.id, 'order_id', new.order_id));
    perform public.create_notification(farmer, 'QUALITY', 'Quality inspection updated', 'A quality inspection is available for your order.', jsonb_build_object('inspection_id', new.id, 'order_id', new.order_id));
    return new;
end; $$;

drop trigger if exists quality_inspections_notification_trigger on public.quality_inspections;
create trigger quality_inspections_notification_trigger after insert or update on public.quality_inspections
for each row execute function public.notify_quality_event();

create or replace function public.notify_dispute_event()
returns trigger language plpgsql security definer set search_path = public as $$
begin
    perform public.create_notification(new.buyer_id, 'DISPUTE', 'New dispute', 'A dispute has been opened for an order.', jsonb_build_object('dispute_id', new.id, 'order_id', new.order_id));
    perform public.create_notification(new.farmer_id, 'DISPUTE', 'New dispute', 'A dispute has been opened for an order.', jsonb_build_object('dispute_id', new.id, 'order_id', new.order_id));
    return new;
end; $$;

drop trigger if exists disputes_notification_trigger on public.disputes;
create trigger disputes_notification_trigger after insert on public.disputes
for each row execute function public.notify_dispute_event();

alter table public.notifications replica identity full;
do $$
begin
    alter publication supabase_realtime add table public.notifications;
exception when duplicate_object then null;
end $$;