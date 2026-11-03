-- Initial schema. Applied only the first time the Postgres volume starts.
-- Rule: the ID number (cédula) is NEVER stored in full (masked only).

create table if not exists sessions (
    id               text primary key,             -- call / room id
    phone            text not null,
    state            jsonb not null,               -- core.engine.State.to_dict()
    masked_id_number text,                         -- never in full
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now()
);
create index if not exists sessions_phone_idx on sessions (phone);

create table if not exists cases (
    number           bigserial primary key,
    session_id       text references sessions (id),
    phone            text not null,
    masked_id_number text,
    flow             text not null,
    destination      text not null,                -- help_desk | census_office | logistics
    priority         text not null default 'normal', -- normal | high
    reason           text not null,                -- end step that created the case
    steps_tried      jsonb not null default '[]',
    transcript       jsonb not null default '[]',  -- masked turns
    status           text not null default 'open', -- open | taken | closed
    taken_by         text,
    close_reason     text,
    notes            text,
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now()
);
create index if not exists cases_queue_idx on cases (status, priority, created_at);

create table if not exists events (
    id          bigserial primary key,
    session_id  text,
    type        text not null,                     -- start | turn | escalation | error
    data        jsonb not null default '{}',
    created_at  timestamptz not null default now()
);
create index if not exists events_session_idx on events (session_id, created_at);
