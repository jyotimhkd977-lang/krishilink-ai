-- KrishiLink AI logistics, driver assignment, routes, and location tracking.

create table if not exists public.vehicles (
    id uuid primary key default gen_random_uuid(),
    driver_id uuid not null references public.users(id) on delete restrict,
    registration_number text not null unique,
    vehicle_type text not null,
    capacity numeric(14, 2) not null check (capacity > 0),
    is_available boolean not null default true,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.deliveries (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null unique references public.orders(id) on delete restrict,
    farmer_id uuid not null references public.users(id) on delete restrict,
    buyer_id uuid not null references public.users(id) on delete restrict,
    driver_id uuid references public.users(id) on delete restrict,
    vehicle_id uuid references public.vehicles(id) on delete restrict,
    pickup_address text not null,
    delivery_address text not null,
    scheduled_pickup_at timestamptz,
    estimated_arrival timestamptz,
    route jsonb not null default '[]'::jsonb,
    status text not null default 'unassigned' check (status in (
        'unassigned', 'assigned', 'pickup_scheduled', 'en_route',
        'picked_up', 'in_transit', 'delivered', 'cancelled'
    )),
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.vehicle_locations (
    id uuid primary key default gen_random_uuid(),
    vehicle_id uuid not null references public.vehicles(id) on delete cascade,
    delivery_id uuid not null references public.deliveries(id) on delete cascade,
    driver_id uuid not null references public.users(id) on delete restrict,
    latitude numeric(9, 6) not null check (latitude between -90 and 90),
    longitude numeric(9, 6) not null check (longitude between -180 and 180),
    speed_kph numeric(7, 2) check (speed_kph is null or speed_kph >= 0),
    heading numeric(6, 2) check (heading is null or heading between 0 and 360),
    recorded_at timestamptz not null default timezone('utc', now())
);

create index if not exists deliveries_farmer_idx on public.deliveries(farmer_id, created_at desc);
create index if not exists deliveries_buyer_idx on public.deliveries(buyer_id, created_at desc);
create index if not exists deliveries_driver_idx on public.deliveries(driver_id, status);
create index if not exists vehicle_locations_delivery_idx on public.vehicle_locations(delivery_id, recorded_at desc);

drop trigger if exists vehicles_set_updated_at on public.vehicles;
create trigger vehicles_set_updated_at before update on public.vehicles
for each row execute function public.set_updated_at();

drop trigger if exists deliveries_set_updated_at on public.deliveries;
create trigger deliveries_set_updated_at before update on public.deliveries
for each row execute function public.set_updated_at();

create or replace function public.record_vehicle_location(
    p_delivery_id uuid,
    p_vehicle_id uuid,
    p_driver_id uuid,
    p_latitude numeric,
    p_longitude numeric,
    p_speed_kph numeric default null,
    p_heading numeric default null
)
returns public.vehicle_locations
language plpgsql
security definer
set search_path = public
as $$
declare
    delivery_row public.deliveries%rowtype;
    location_row public.vehicle_locations%rowtype;
    last_recorded timestamptz;
begin
    select * into delivery_row from public.deliveries where id = p_delivery_id for update;
    if delivery_row.id is null or delivery_row.driver_id <> auth.uid() or delivery_row.vehicle_id <> p_vehicle_id then
        raise exception 'Driver is not assigned to this delivery';
    end if;
    select max(recorded_at) into last_recorded from public.vehicle_locations where delivery_id = p_delivery_id;
    if last_recorded is not null and last_recorded > timezone('utc', now()) - interval '10 seconds' then
        raise exception 'Location updates must be at least 10 seconds apart';
    end if;
    insert into public.vehicle_locations (delivery_id, vehicle_id, driver_id, latitude, longitude, speed_kph, heading)
    values (p_delivery_id, p_vehicle_id, p_driver_id, p_latitude, p_longitude, p_speed_kph, p_heading)
    returning * into location_row;
    return location_row;
end;
$$;

alter table public.vehicles enable row level security;
alter table public.deliveries enable row level security;
alter table public.vehicle_locations enable row level security;

create policy "Drivers and logistics view vehicles"
on public.vehicles for select
using (
    driver_id = auth.uid()
    or (auth.jwt() -> 'app_metadata' ->> 'role') in ('logistics', 'admin')
);

create policy "Logistics admins manage vehicles"
on public.vehicles for all
using ((auth.jwt() -> 'app_metadata' ->> 'role') in ('logistics', 'admin'))
with check ((auth.jwt() -> 'app_metadata' ->> 'role') in ('logistics', 'admin'));

create policy "Participants view deliveries"
on public.deliveries for select
using (
    farmer_id = auth.uid() or buyer_id = auth.uid() or driver_id = auth.uid()
    or (auth.jwt() -> 'app_metadata' ->> 'role') in ('logistics', 'admin')
);

create policy "Logistics assign deliveries"
on public.deliveries for insert
with check ((auth.jwt() -> 'app_metadata' ->> 'role') in ('logistics', 'admin'));

create policy "Logistics update deliveries"
on public.deliveries for update
using ((auth.jwt() -> 'app_metadata' ->> 'role') in ('logistics', 'admin'))
with check ((auth.jwt() -> 'app_metadata' ->> 'role') in ('logistics', 'admin'));

create policy "Assigned drivers update deliveries"
on public.deliveries for update
using (driver_id = auth.uid() and (auth.jwt() -> 'app_metadata' ->> 'role') = 'logistics')
with check (driver_id = auth.uid());

create policy "Participants view vehicle locations"
on public.vehicle_locations for select
using (exists (
    select 1 from public.deliveries delivery
    where delivery.id = delivery_id
    and (delivery.farmer_id = auth.uid() or delivery.buyer_id = auth.uid()
         or delivery.driver_id = auth.uid()
         or (auth.jwt() -> 'app_metadata' ->> 'role') in ('logistics', 'admin'))
));

create policy "Assigned drivers insert vehicle locations"
on public.vehicle_locations for insert
with check (driver_id = auth.uid());

alter table public.deliveries replica identity full;
alter table public.vehicle_locations replica identity full;

do $$
begin
    alter publication supabase_realtime add table public.deliveries;
exception when duplicate_object then null;
end $$;
do $$
begin
    alter publication supabase_realtime add table public.vehicle_locations;
exception when duplicate_object then null;
end $$;