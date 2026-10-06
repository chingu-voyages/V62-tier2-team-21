CREATE TABLE IF NOT EXISTS users (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name text NOT NULL,
    email text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- The backend connects directly with DATABASE_URL. Enabling RLS with no policies
-- blocks access through Supabase's public REST API (anon/authenticated roles).
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
