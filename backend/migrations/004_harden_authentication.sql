ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL PRIVILEGES ON TABLE users FROM anon;
        REVOKE ALL PRIVILEGES ON SEQUENCE users_id_seq FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL PRIVILEGES ON TABLE users FROM authenticated;
        REVOKE ALL PRIVILEGES ON SEQUENCE users_id_seq FROM authenticated;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS login_rate_limits (
    client_hash text PRIMARY KEY,
    window_started_at timestamptz NOT NULL DEFAULT now(),
    attempt_count integer NOT NULL DEFAULT 0
);

ALTER TABLE login_rate_limits ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL PRIVILEGES ON TABLE login_rate_limits FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL PRIVILEGES ON TABLE login_rate_limits FROM authenticated;
    END IF;
END $$;
