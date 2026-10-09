-- Title is now a required, non-blank field: the application no longer allows
-- saving or renaming a path without one. Run only after existing NULL/blank
-- titles have been backfilled, otherwise this migration will fail.
ALTER TABLE saved_learning_paths
    ALTER COLUMN title SET NOT NULL;

ALTER TABLE saved_learning_paths
    ADD CONSTRAINT saved_learning_paths_title_not_blank CHECK (btrim(title) <> '');
