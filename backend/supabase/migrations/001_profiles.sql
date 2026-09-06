-- KrishiLink AI application profiles and Row Level Security.
-- Apply this migration in the Supabase SQL editor or through Supabase CLI.

create table if not exists public.users (
    id uuid primary key references auth.users(id) on delete cascade,
    email text not null,
    role text not null default 'farmer'
        check (role in ('farmer', 'buyer', 'fpo', 'logistics', 'admin')),
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.farmer_profiles (
    user_id uuid primary key references public.users(id) on delete cascade,
    full_name text,
    phone text,
    village text,
    district text,
    state text,
    farm_size numeric(12, 2) check (farm_size is null or farm_size >= 0),
    trust_score numeric(5, 2) not null default 0 check (trust_score between 0 and 100),
    verified boolean not null default false,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.buyer_profiles (
    user_id uuid primary key references public.users(id) on delete cascade,
    business_name text,
    buyer_type text,
    location text,
    trust_score numeric(5, 2) not null default 0 check (trust_score between 0 and 100),
    verified boolean not null default false,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
begin
    new.updated_at = timezone('utc', now());
    return new;
end;
$$;

drop trigger if exists users_set_updated_at on public.users;
create trigger users_set_updated_at
before update on public.users
for each row execute function public.set_updated_at();

drop trigger if exists farmer_profiles_set_updated_at on public.farmer_profiles;
create trigger farmer_profiles_set_updated_at
before update on public.farmer_profiles
for each row execute function public.set_updated_at();

drop trigger if exists buyer_profiles_set_updated_at on public.buyer_profiles;
create trigger buyer_profiles_set_updated_at
before update on public.buyer_profiles
for each row execute function public.set_updated_at();

create or replace function public.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    requested_role text := coalesce(new.raw_user_meta_data ->> 'role', 'farmer');
    profile_data jsonb := coalesce(new.raw_user_meta_data -> 'profile', '{}'::jsonb);
begin
    if requested_role not in ('farmer', 'buyer', 'fpo', 'logistics', 'admin') then
        requested_role := 'farmer';
    end if;

    insert into public.users (id, email, role)
    values (new.id, new.email, requested_role)
    on conflict (id) do update set email = excluded.email;

    if requested_role = 'farmer' then
        insert into public.farmer_profiles (
            user_id, full_name, phone, village, district, state, farm_size
        )
        values (
            new.id,
            profile_data ->> 'full_name',
            profile_data ->> 'phone',
            profile_data ->> 'village',
            profile_data ->> 'district',
            profile_data ->> 'state',
            case when profile_data ->> 'farm_size' is null then null else (profile_data ->> 'farm_size')::numeric end
        )
        on conflict (user_id) do nothing;
    elsif requested_role = 'buyer' then
        insert into public.buyer_profiles (user_id, business_name, buyer_type, location)
        values (
            new.id,
            profile_data ->> 'business_name',
            profile_data ->> 'buyer_type',
            profile_data ->> 'location'
        )
        on conflict (user_id) do nothing;
    end if;

    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_auth_user();

alter table public.users enable row level security;
alter table public.farmer_profiles enable row level security;
alter table public.buyer_profiles enable row level security;

create policy "Users can view their own application user"
on public.users for select
using (id = auth.uid() or (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

create policy "Farmers can view their own profile"
on public.farmer_profiles for select
using (user_id = auth.uid() or (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

create policy "Farmers can update their own profile"
on public.farmer_profiles for update
using (
    user_id = auth.uid()
    and (auth.jwt() -> 'app_metadata' ->> 'role') = 'farmer'
)
with check (
    user_id = auth.uid()
    and (auth.jwt() -> 'app_metadata' ->> 'role') = 'farmer'
);

create policy "Buyers can view their own profile"
on public.buyer_profiles for select
using (user_id = auth.uid() or (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

create policy "Buyers can update their own profile"
on public.buyer_profiles for update
using (
    user_id = auth.uid()
    and (auth.jwt() -> 'app_metadata' ->> 'role') = 'buyer'
)
with check (
    user_id = auth.uid()
    and (auth.jwt() -> 'app_metadata' ->> 'role') = 'buyer'
);