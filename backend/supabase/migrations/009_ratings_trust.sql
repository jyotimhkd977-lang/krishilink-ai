-- KrishiLink AI reviews and derived trust scores.

create table if not exists public.reviews (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null references public.orders(id) on delete restrict,
    reviewer_id uuid not null references public.users(id) on delete restrict,
    reviewee_id uuid not null references public.users(id) on delete restrict,
    rating numeric(2, 1) not null check (rating between 1 and 5),
    quality_rating numeric(2, 1) check (quality_rating is null or quality_rating between 1 and 5),
    delivery_rating numeric(2, 1) check (delivery_rating is null or delivery_rating between 1 and 5),
    comment text check (comment is null or char_length(comment) <= 2000),
    created_at timestamptz not null default timezone('utc', now()),
    unique (order_id, reviewer_id)
);

create table if not exists public.trust_scores (
    user_id uuid primary key references public.users(id) on delete cascade,
    score numeric(5, 2) not null default 0 check (score between 0 and 100),
    successful_orders integer not null default 0 check (successful_orders >= 0),
    quality_score numeric(5, 2) not null default 0 check (quality_score between 0 and 100),
    delivery_reliability numeric(5, 2) not null default 0 check (delivery_reliability between 0 and 100),
    payment_reliability numeric(5, 2) not null default 0 check (payment_reliability between 0 and 100),
    ratings numeric(5, 2) not null default 0 check (ratings between 0 and 100),
    dispute_history numeric(5, 2) not null default 100 check (dispute_history between 0 and 100),
    badges text[] not null default '{}',
    calculated_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists reviews_reviewee_idx on public.reviews(reviewee_id, created_at desc);
create index if not exists reviews_order_idx on public.reviews(order_id);

alter table public.reviews enable row level security;
alter table public.trust_scores enable row level security;

create policy "Authenticated users view reviews"
on public.reviews for select to authenticated using (true);

create policy "Review participants view own review"
on public.reviews for select
using (reviewer_id = auth.uid() or reviewee_id = auth.uid());

create policy "Users view trust scores"
on public.trust_scores for select to authenticated using (true);

create or replace function public.refresh_trust_score(p_user_id uuid)
returns public.trust_scores
language plpgsql
security definer
set search_path = public
as $$
declare
    completed_count integer;
    total_count integer;
    quality numeric := 0;
    delivery numeric := 0;
    payment numeric := 0;
    rating_value numeric := 0;
    disputes integer;
    dispute_value numeric;
    calculated_score numeric;
    role_value text;
    badge_values text[] := '{}';
    result public.trust_scores%rowtype;
begin
    select role into role_value from public.users where id = p_user_id;
    select count(*)::integer into completed_count from public.orders
    where (buyer_id = p_user_id or farmer_id = p_user_id) and status = 'completed';
    select count(*)::integer into total_count from public.orders
    where buyer_id = p_user_id or farmer_id = p_user_id;
    select coalesce(avg(ai_quality_score), 0) into quality from public.quality_inspections inspection
    join public.orders order_row on order_row.id = inspection.order_id
    where order_row.farmer_id = p_user_id and ai_quality_score is not null;
    delivery := case when total_count = 0 then 0 else (completed_count::numeric / total_count) * 100 end;
    select coalesce(avg(rating), 0) * 20 into rating_value from public.reviews where reviewee_id = p_user_id;
    select count(*)::integer into disputes from public.disputes
    where (buyer_id = p_user_id or farmer_id = p_user_id) and status <> 'RESOLVED';
    dispute_value := greatest(0, 100 - (disputes * 15));
    select coalesce(payment_reliability, 0) into payment from public.buyer_profiles where user_id = p_user_id;
    if payment = 0 and role_value = 'farmer' then payment := 100; end if;

    calculated_score := round(
        least(100, (least(completed_count, 20)::numeric / 20) * 20 + quality * 0.20
        + delivery * 0.20 + payment * 0.15 + rating_value * 0.15 + dispute_value * 0.10), 2
    );
    if role_value = 'farmer' and exists (select 1 from public.farmer_profiles where user_id = p_user_id and verified) then
        badge_values := array_append(badge_values, 'Verified Farmer');
    end if;
    if role_value = 'farmer' and calculated_score >= 80 then badge_values := array_append(badge_values, 'Trusted Seller'); end if;
    if role_value = 'farmer' and quality >= 90 then badge_values := array_append(badge_values, 'Quality Champion'); end if;
    if role_value = 'buyer' and calculated_score >= 80 then badge_values := array_append(badge_values, 'Reliable Buyer'); end if;

    insert into public.trust_scores (user_id, score, successful_orders, quality_score, delivery_reliability, payment_reliability, ratings, dispute_history, badges)
    values (p_user_id, calculated_score, completed_count, quality, delivery, payment, rating_value, dispute_value, badge_values)
    on conflict (user_id) do update set
        score = excluded.score, successful_orders = excluded.successful_orders, quality_score = excluded.quality_score,
        delivery_reliability = excluded.delivery_reliability, payment_reliability = excluded.payment_reliability,
        ratings = excluded.ratings, dispute_history = excluded.dispute_history, badges = excluded.badges,
        calculated_at = timezone('utc', now()), updated_at = timezone('utc', now())
    returning * into result;
    return result;
end;
$$;

create or replace function public.create_review(
    p_order_id uuid,
    p_reviewee_id uuid,
    p_rating numeric,
    p_quality_rating numeric default null,
    p_delivery_rating numeric default null,
    p_comment text default null
)
returns public.reviews
language plpgsql
security definer
set search_path = public
as $$
declare
    order_row public.orders%rowtype;
    new_review public.reviews%rowtype;
begin
    select * into order_row from public.orders where id = p_order_id;
    if order_row.id is null or order_row.status <> 'completed'
        or auth.uid() not in (order_row.buyer_id, order_row.farmer_id)
        or p_reviewee_id not in (order_row.buyer_id, order_row.farmer_id)
        or p_reviewee_id = auth.uid() then
        raise exception 'Review is not allowed for this order';
    end if;
    insert into public.reviews (order_id, reviewer_id, reviewee_id, rating, quality_rating, delivery_rating, comment)
    values (p_order_id, auth.uid(), p_reviewee_id, p_rating, p_quality_rating, p_delivery_rating, p_comment)
    returning * into new_review;
    perform public.refresh_trust_score(p_reviewee_id);
    insert into public.audit_logs (actor_id, entity_type, entity_id, action)
    values (auth.uid(), 'review', new_review.id, 'REVIEW_CREATED');
    return new_review;
exception when unique_violation then
    raise exception 'A review already exists for this order';
end;
$$;

create or replace function public.get_trust_score(p_user_id uuid)
returns public.trust_scores
language plpgsql
security definer
set search_path = public
as $$
declare
    result public.trust_scores%rowtype;
begin
    if auth.uid() <> p_user_id and (auth.jwt() -> 'app_metadata' ->> 'role') <> 'admin' then
        raise exception 'Trust score access denied';
    end if;
    result := public.refresh_trust_score(p_user_id);
    return result;
end;
$$;

alter table public.trust_scores replica identity full;
do $$
begin
    alter publication supabase_realtime add table public.trust_scores;
exception when duplicate_object then null;
end $$;