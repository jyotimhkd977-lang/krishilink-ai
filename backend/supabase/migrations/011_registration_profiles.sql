-- Additional fields required by farmer and buyer registration forms.

alter table public.farmer_profiles
    add column if not exists block_tehsil text,
    add column if not exists pincode text,
    add column if not exists farm_name text,
    add column if not exists farm_unit text check (farm_unit is null or farm_unit in ('acres', 'hectares')),
    add column if not exists primary_crops text[] not null default '{}',
    add column if not exists preferred_language text check (preferred_language is null or preferred_language in ('en', 'hi', 'or')),
    add column if not exists profile_photo_path text;

alter table public.buyer_profiles
    add column if not exists full_name text,
    add column if not exists phone text,
    add column if not exists district text,
    add column if not exists state text,
    add column if not exists pincode text;