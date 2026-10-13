ALTER TABLE saved_learning_path_items
    ADD COLUMN IF NOT EXISTS completed boolean NOT NULL DEFAULT false;
