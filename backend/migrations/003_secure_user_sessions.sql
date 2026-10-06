-- Sessions are accessed only by the backend's database connection, never via Supabase REST.
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- Supabase creates these REST roles; a plain PostgreSQL test database may not.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL PRIVILEGES ON TABLE user_sessions FROM anon;
        REVOKE ALL PRIVILEGES ON SEQUENCE user_sessions_id_seq FROM anon;
    END IF;

    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL PRIVILEGES ON TABLE user_sessions FROM authenticated;
        REVOKE ALL PRIVILEGES ON SEQUENCE user_sessions_id_seq FROM authenticated;
    END IF;
END $$;
