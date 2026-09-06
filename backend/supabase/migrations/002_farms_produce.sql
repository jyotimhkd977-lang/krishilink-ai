-- KrishiLink AI farms, produce listings, images, and storage policies.

create table if not exists public.farms (
    id uuid primary key default gen_random_uuid(),
    farmer_id uuid not null references public.users(id) on delete cascade,
    name text not null,
    location text not null,
    village text,
    district text,
    state text,
    size numeric(12, 2) not null check (size >= 0),
    unique (id, farmer_id),
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.crop_categories (
    id uuid primary key default gen_random_uuid(),
    name text not null unique,
    description text,
    created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.produce_listings (
    id uuid primary key default gen_random_uuid(),
    farmer_id uuid not null references public.users(id) on delete cascade,
    farm_id uuid not null references public.farms(id) on delete cascade,
    crop_category_id uuid references public.crop_categories(id) on delete set null,
    crop text not null,
    quantity numeric(14, 2) not null check (quantity > 0),
    unit text not null check (unit in ('kg', 'quintal', 'ton', 'piece', 'crate')),
    quality_grade text,
    quality_score numeric(5, 2) check (quality_score is null or quality_score between 0 and 100),
    asking_price numeric(12, 2) not null check (asking_price >= 0),
    ai_price numeric(12, 2) check (ai_price is null or ai_price >= 0),
    location text not null,
    harvest_date date,
    status text not null default 'draft' check (status in ('draft', 'active', 'sold', 'expired', 'archived')),
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now()),
    constraint produce_listing_farm_owner foreign key (farm_id, farmer_id)
        references public.farms(id, farmer_id)
);

create table if not exists public.produce_images (
    id uuid primary key default gen_random_uuid(),
    listing_id uuid not null references public.produce_listings(id) on delete cascade,
    farmer_id uuid not null references public.users(id) on delete cascade,
    storage_path text not null unique,
    content_type text not null check (content_type in ('image/jpeg', 'image/png', 'image/webp')),
    file_size integer not null check (file_size > 0 and file_size <= 5242880),
    created_at timestamptz not null default timezone('utc', now())
);

create index if not exists produce_listings_active_idx on public.produce_listings(status, created_at desc);
create index if not exists produce_listings_farmer_idx on public.produce_listings(farmer_id);
create index if not exists produce_images_listing_idx on public.produce_images(listing_id);

insert into public.crop_categories (name, description) values
    ('vegetables', 'Fresh vegetables and leafy greens'),
    ('fruits', 'Fresh fruits'),
    ('grains', 'Cereals, grains, and millets'),
    ('pulses', 'Pulses and legumes'),
    ('spices', 'Spices and herbs')
on conflict (name) do nothing;

drop trigger if exists farms_set_updated_at on public.farms;
create trigger farms_set_updated_at before update on public.farms
for each row execute function public.set_updated_at();

drop trigger if exists produce_listings_set_updated_at on public.produce_listings;
create trigger produce_listings_set_updated_at before update on public.produce_listings
for each row execute function public.set_updated_at();

alter table public.farms enable row level security;
alter table public.crop_categories enable row level security;
alter table public.produce_listings enable row level security;
alter table public.produce_images enable row level security;

create policy "Farmers manage their own farms"
on public.farms for all
using (farmer_id = auth.uid() and (auth.jwt() -> 'app_metadata' ->> 'role') = 'farmer')
with check (farmer_id = auth.uid() and (auth.jwt() -> 'app_metadata' ->> 'role') = 'farmer');

create policy "Admins view all farms"
on public.farms for select
using ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

create policy "Anyone can view crop categories"
on public.crop_categories for select using (true);

create policy "Farmers manage their own listings"
on public.produce_listings for all
using (farmer_id = auth.uid() and (auth.jwt() -> 'app_metadata' ->> 'role') = 'farmer')
with check (
    farmer_id = auth.uid()
    and (auth.jwt() -> 'app_metadata' ->> 'role') = 'farmer'
    and exists (select 1 from public.farms f where f.id = farm_id and f.farmer_id = auth.uid())
);

create policy "Public can view active listings"
on public.produce_listings for select using (status = 'active');

create policy "Admins view all listings"
on public.produce_listings for select
using ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

create policy "Farmers manage their own images"
on public.produce_images for all
using (farmer_id = auth.uid() and (auth.jwt() -> 'app_metadata' ->> 'role') = 'farmer')
with check (
    farmer_id = auth.uid()
    and (auth.jwt() -> 'app_metadata' ->> 'role') = 'farmer'
    and exists (
        select 1 from public.produce_listings listing
        where listing.id = listing_id and listing.farmer_id = auth.uid()
    )
);

create policy "Public can view images for active listings"
on public.produce_images for select
using (exists (
    select 1 from public.produce_listings listing
    where listing.id = listing_id and listing.status = 'active'
));

insert into storage.buckets (id, name, public)
values ('produce-images', 'produce-images', false)
on conflict (id) do nothing;

create policy "Farmers upload images to their own folder"
on storage.objects for insert to authenticated
with check (
    bucket_id = 'produce-images'
    and (storage.foldername(name))[1] = auth.uid()::text
    and (auth.jwt() -> 'app_metadata' ->> 'role') = 'farmer'
    and lower(coalesce(metadata ->> 'mimetype', '')) in ('image/jpeg', 'image/png', 'image/webp')
);

create policy "Farmers manage images in their own folder"
on storage.objects for delete to authenticated
using (
    bucket_id = 'produce-images'
    and (storage.foldername(name))[1] = auth.uid()::text
    and (auth.jwt() -> 'app_metadata' ->> 'role') = 'farmer'
);

create policy "Public can read active listing images"
on storage.objects for select to anon, authenticated
using (
    bucket_id = 'produce-images'
    and exists (
        select 1
        from public.produce_images image
        join public.produce_listings listing on listing.id = image.listing_id
        where image.storage_path = name and listing.status = 'active'
    )
);