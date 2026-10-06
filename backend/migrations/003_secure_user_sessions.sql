-- Sessions are accessed only by the backend's database connection, never via Supabase REST.
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
REVOKE ALL PRIVILEGES ON TABLE user_sessions FROM anon, authenticated;
REVOKE ALL PRIVILEGES ON SEQUENCE user_sessions_id_seq FROM anon, authenticated;
