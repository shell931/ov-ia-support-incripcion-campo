-- One case per call: makes POST /cases idempotent (the voice agent may retry).
create unique index if not exists cases_session_id_uniq on cases (session_id);
