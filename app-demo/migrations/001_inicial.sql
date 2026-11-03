-- Esquema inicial. Se aplica solo la primera vez que arranca el volumen de Postgres.
-- Regla: la cédula NUNCA se guarda completa (solo enmascarada).

create table if not exists sesiones (
    id            text primary key,              -- id de la llamada / sala
    telefono      text not null,
    estado        jsonb not null,                -- core.engine.Estado.a_dict()
    creada_en     timestamptz not null default now(),
    actualizada_en timestamptz not null default now()
);
create index if not exists sesiones_telefono_idx on sesiones (telefono);

create table if not exists casos (
    numero            bigserial primary key,
    sesion_id         text references sesiones (id),
    telefono          text not null,
    cedula_enmascarada text,
    flujo             text not null,
    destino           text not null,             -- mesa | direccion_censo | logistica
    prioridad         text not null default 'normal',
    motivo            text not null,             -- paso final que creó el caso
    pasos_intentados  jsonb not null default '[]',
    transcripcion     jsonb not null default '[]',-- turnos enmascarados
    estado            text not null default 'abierto', -- abierto | tomado | cerrado
    tomado_por        text,
    causa_cierre      text,
    notas             text,
    creado_en         timestamptz not null default now(),
    actualizado_en    timestamptz not null default now()
);
create index if not exists casos_cola_idx on casos (estado, prioridad, creado_en);

create table if not exists eventos (
    id         bigserial primary key,
    sesion_id  text,
    tipo       text not null,                    -- turno | dtmf | escalamiento | error
    datos      jsonb not null default '{}',
    creado_en  timestamptz not null default now()
);
create index if not exists eventos_sesion_idx on eventos (sesion_id, creado_en);
