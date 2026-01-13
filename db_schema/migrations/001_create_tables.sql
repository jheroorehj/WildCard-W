create table if not exists analysis_requests (
  id uuid primary key,
  created_at timestamptz default now(),
  layer1_stock text not null,
  layer2_buy_date date,
  layer2_sell_date date,
  layer3_decision_basis text,
  user_message text,
  raw_input jsonb
);

create table if not exists analysis_results (
  id uuid primary key default gen_random_uuid(),
  request_id uuid references analysis_requests(id) on delete cascade,
  node text not null,
  result jsonb not null,
  created_at timestamptz default now()
);

create index if not exists analysis_results_request_id_idx
  on analysis_results(request_id);

alter table analysis_requests
add column if not exists user_id uuid;

alter table analysis_results
add column if not exists user_id uuid;

alter table analysis_requests enable row level security;
alter table analysis_results enable row level security;

create policy "user can read own requests"
on analysis_requests
for select
using (auth.uid() = user_id);

create policy "user can insert own requests"
on analysis_requests
for insert
with check (auth.uid() = user_id);

create policy "user can read own results"
on analysis_results
for select
using (auth.uid() = user_id);

create policy "user can insert own results"
on analysis_results
for insert
with check (auth.uid() = user_id);
