-- KrishiLink AI quality protection, disputes, evidence, and audit logs.

create table if not exists public.quality_inspections (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null unique references public.orders(id) on delete restrict,
    inspector_id uuid not null references public.users(id) on delete restrict,
    status text not null check (status in ('APPROVED', 'REJECTED', 'ISSUE_FOUND')),
    ai_quality_score numeric(5, 2) check (ai_quality_score is null or ai_quality_score between 0 and 100),
    ai_quality_label text,
    notes text,
    buyer_confirmed boolean not null default false,
    buyer_confirmed_by uuid references public.users(id) on delete restrict,
    buyer_confirmed_at timestamptz,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.disputes (
    id uuid primary key default gen_random_uuid(),
    order_id uuid not null references public.orders(id) on delete restrict,
    raised_by uuid not null references public.users(id) on delete restrict,
    buyer_id uuid not null references public.users(id) on delete restrict,
    farmer_id uuid not null references public.users(id) on delete restrict,
    reason text not null check (char_length(trim(reason)) between 1 and 2000),
    status text not null default 'OPEN' check (status in ('OPEN', 'UNDER_REVIEW', 'REFUND', 'REPLACEMENT', 'RESOLVED')),
    resolution_note text,
    resolved_by uuid references public.users(id) on delete restrict,
    created_at timestamptz not null default timezone('utc', now()),
    updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.dispute_evidence (
    id uuid primary key default gen_random_uuid(),
    dispute_id uuid not null references public.disputes(id) on delete cascade,
    uploaded_by uuid not null references public.users(id) on delete restrict,
    storage_path text not null unique,
    content_type text not null check (content_type in ('image/jpeg', 'image/png', 'image/webp', 'application/pdf')),
    file_size integer not null check (file_size > 0 and file_size <= 10485760),
    created_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.audit_logs (
    id uuid primary key default gen_random_uuid(),
    actor_id uuid references public.users(id) on delete set null,
    entity_type text not null,
    entity_id uuid not null,
    action text not null,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default timezone('utc', now())
);

create index if not exists disputes_order_idx on public.disputes(order_id, created_at desc);
create index if not exists disputes_status_idx on public.disputes(status, created_at desc);
create index if not exists dispute_evidence_dispute_idx on public.dispute_evidence(dispute_id, created_at);
create index if not exists audit_logs_entity_idx on public.audit_logs(entity_type, entity_id, created_at desc);

drop trigger if exists quality_inspections_set_updated_at on public.quality_inspections;
create trigger quality_inspections_set_updated_at before update on public.quality_inspections
for each row execute function public.set_updated_at();

drop trigger if exists disputes_set_updated_at on public.disputes;
create trigger disputes_set_updated_at before update on public.disputes
for each row execute function public.set_updated_at();

alter table public.quality_inspections enable row level security;
alter table public.disputes enable row level security;
alter table public.dispute_evidence enable row level security;
alter table public.audit_logs enable row level security;

create policy "Order participants view quality inspections"
on public.quality_inspections for select
using (exists (
    select 1 from public.orders order_row
    where order_row.id = order_id
    and (order_row.buyer_id = auth.uid() or order_row.farmer_id = auth.uid()
         or (auth.jwt() -> 'app_metadata' ->> 'role') in ('admin', 'logistics'))
));

create policy "Inspectors create quality inspections"
on public.quality_inspections for insert
with check ((auth.jwt() -> 'app_metadata' ->> 'role') in ('admin', 'logistics') and inspector_id = auth.uid());

create policy "Buyers confirm their quality inspection"
on public.quality_inspections for update
using (exists (
    select 1 from public.orders order_row
    where order_row.id = order_id and order_row.buyer_id = auth.uid()
))
with check (buyer_confirmed_by = auth.uid() and buyer_confirmed = true);

create policy "Participants view disputes"
on public.disputes for select
using (buyer_id = auth.uid() or farmer_id = auth.uid() or (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

create policy "Participants create disputes"
on public.disputes for insert
with check (
    raised_by = auth.uid()
    and (raised_by = buyer_id or raised_by = farmer_id)
    and exists (select 1 from public.orders order_row where order_row.id = order_id and order_row.buyer_id = buyer_id and order_row.farmer_id = farmer_id)
);

create policy "Admins resolve disputes"
on public.disputes for update
using ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin')
with check ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

create policy "Participants view dispute evidence"
on public.dispute_evidence for select
using (exists (
    select 1 from public.disputes dispute
    where dispute.id = dispute_id and (dispute.buyer_id = auth.uid() or dispute.farmer_id = auth.uid() or (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin')
));

create policy "Participants add dispute evidence"
on public.dispute_evidence for insert
with check (
    uploaded_by = auth.uid()
    and exists (select 1 from public.disputes dispute where dispute.id = dispute_id and (dispute.buyer_id = auth.uid() or dispute.farmer_id = auth.uid()))
);

create policy "Participants view audit logs"
on public.audit_logs for select
using (actor_id = auth.uid() or (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

create policy "Authenticated users append audit logs"
on public.audit_logs for insert to authenticated
with check (actor_id = auth.uid());

insert into storage.buckets (id, name, public)
values ('dispute-evidence', 'dispute-evidence', false)
on conflict (id) do nothing;

create policy "Participants upload dispute evidence"
on storage.objects for insert to authenticated
with check (
    bucket_id = 'dispute-evidence'
    and (storage.foldername(name))[1] = auth.uid()::text
    and lower(coalesce(metadata ->> 'mimetype', '')) in ('image/jpeg', 'image/png', 'image/webp', 'application/pdf')
    and exists (
        select 1 from public.disputes dispute
        where dispute.id = nullif((storage.foldername(name))[2], '')::uuid
        and (dispute.buyer_id = auth.uid() or dispute.farmer_id = auth.uid())
    )
);

create policy "Participants read dispute evidence"
on storage.objects for select to authenticated
using (
    bucket_id = 'dispute-evidence'
    and exists (
        select 1 from public.dispute_evidence evidence
        join public.disputes dispute on dispute.id = evidence.dispute_id
        where evidence.storage_path = name
        and (dispute.buyer_id = auth.uid() or dispute.farmer_id = auth.uid() or (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin')
    )
);

alter table public.quality_inspections replica identity full;
alter table public.disputes replica identity full;

do $$
begin
    alter publication supabase_realtime add table public.quality_inspections;
exception when duplicate_object then null;
end $$;
do $$
begin
    alter publication supabase_realtime add table public.disputes;
exception when duplicate_object then null;
end $$;