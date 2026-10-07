CREATE TABLE IF NOT EXISTS saved_learning_paths (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS saved_learning_paths_user_id_idx
    ON saved_learning_paths (user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS saved_learning_path_items (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    saved_learning_path_id bigint NOT NULL REFERENCES saved_learning_paths(id) ON DELETE CASCADE,
    step_order integer NOT NULL,
    title text NOT NULL,
    description text NOT NULL,
    estimated_time text NOT NULL
);

CREATE INDEX IF NOT EXISTS saved_learning_path_items_path_id_idx
    ON saved_learning_path_items (saved_learning_path_id, step_order);

-- The backend connects directly with DATABASE_URL, never via Supabase's public REST API.
ALTER TABLE saved_learning_paths ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_learning_path_items ENABLE ROW LEVEL SECURITY;

-- Supabase creates these REST roles; a plain PostgreSQL test database may not.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL PRIVILEGES ON TABLE saved_learning_paths FROM anon;
        REVOKE ALL PRIVILEGES ON SEQUENCE saved_learning_paths_id_seq FROM anon;
        REVOKE ALL PRIVILEGES ON TABLE saved_learning_path_items FROM anon;
        REVOKE ALL PRIVILEGES ON SEQUENCE saved_learning_path_items_id_seq FROM anon;
    END IF;

    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL PRIVILEGES ON TABLE saved_learning_paths FROM authenticated;
        REVOKE ALL PRIVILEGES ON SEQUENCE saved_learning_paths_id_seq FROM authenticated;
        REVOKE ALL PRIVILEGES ON TABLE saved_learning_path_items FROM authenticated;
        REVOKE ALL PRIVILEGES ON SEQUENCE saved_learning_path_items_id_seq FROM authenticated;
    END IF;
END $$;
