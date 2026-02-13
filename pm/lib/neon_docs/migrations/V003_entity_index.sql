-- V003_entity_index.sql
-- Entity Index: universal entity registry with event sourcing
-- Uses Postgres 18 native uuidv7() for time-ordered UUIDs
-- Idempotent: safe to re-run (IF NOT EXISTS / OR REPLACE)

-- ── Entity Type Dictionary ─────────────────────────────────────────────
-- Monotonically increasing ID. Append-only: never reuse or delete IDs.
-- To add a type: INSERT with next sequential ID.

CREATE TABLE IF NOT EXISTS entity_type_dict (
    id              SMALLINT    PRIMARY KEY,
    name            TEXT        UNIQUE NOT NULL,
    description     TEXT,
    schema_version  TEXT        NOT NULL DEFAULT '1.0.0',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO entity_type_dict (id, name, description) VALUES
    (1, 'USERS',        'User accounts and profiles'),
    (2, 'REPOS',        'Git repositories'),
    (3, 'PROJECTS',     'Neon or PM projects'),
    (4, 'ORGS',         'Organizations'),
    (5, 'AUTH_PROCESS', 'Authentication processes and tokens'),
    (6, 'KEYS',         'API keys, secrets, credentials metadata'),
    (7, 'DOCUMENTS',    'Documents, canvases, files')
ON CONFLICT (id) DO NOTHING;

-- ── Entity Index (latest state per entity) ─────────────────────────────
-- One row = one unique entity instance. Updated in place on each event.

CREATE TABLE IF NOT EXISTS entity_index (
    entity_id                       UUID        PRIMARY KEY DEFAULT uuidv7(),
    entity_type                     SMALLINT    NOT NULL REFERENCES entity_type_dict(id),
    entity_json_blob                JSONB       NOT NULL DEFAULT '{"_v": "1.0.0"}',
    created_date_utc                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_system_json_blob        JSONB       NOT NULL DEFAULT '{}',
    last_updated_date               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated_system_json_blob   JSONB       NOT NULL DEFAULT '{}',
    entity_state                    TEXT        NOT NULL DEFAULT 'ACTIVE'
                                        CHECK (entity_state IN (
                                            'ACTIVE', 'INACTIVE', 'DEACTIVATED', 'PENDING'
                                        )),
    entity_is_test                  BOOLEAN     NOT NULL DEFAULT FALSE,
    entity_event_ids_list           UUID[]      NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_entity_type      ON entity_index (entity_type);
CREATE INDEX IF NOT EXISTS idx_entity_state     ON entity_index (entity_state) WHERE entity_state = 'ACTIVE';
CREATE INDEX IF NOT EXISTS idx_entity_is_test   ON entity_index (entity_is_test) WHERE entity_is_test = TRUE;
CREATE INDEX IF NOT EXISTS idx_entity_json_blob ON entity_index USING GIN (entity_json_blob);
CREATE INDEX IF NOT EXISTS idx_entity_updated   ON entity_index (last_updated_date DESC);

-- ── Entity Events (append-only event log) ──────────────────────────────
-- Every state transition is recorded. Never updated or deleted.

CREATE TABLE IF NOT EXISTS entity_events_idx (
    event_id                UUID        PRIMARY KEY DEFAULT uuidv7(),
    entity_id               UUID        NOT NULL REFERENCES entity_index(entity_id),
    entity_type             SMALLINT    NOT NULL REFERENCES entity_type_dict(id),
    event_type              TEXT        NOT NULL
                                CHECK (event_type IN ('CREATE', 'READ', 'UPDATE', 'DEACTIVATE')),
    entity_json_blob        JSONB       NOT NULL DEFAULT '{}',
    system_json_blob        JSONB       NOT NULL DEFAULT '{}',
    created_date_utc        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_event_entity     ON entity_events_idx (entity_id);
CREATE INDEX IF NOT EXISTS idx_event_type       ON entity_events_idx (event_type);
CREATE INDEX IF NOT EXISTS idx_event_created    ON entity_events_idx (created_date_utc DESC);
CREATE INDEX IF NOT EXISTS idx_event_etype      ON entity_events_idx (entity_type);

-- ── Helper: Create entity with initial event ───────────────────────────

CREATE OR REPLACE FUNCTION create_entity(
    p_entity_type   SMALLINT,
    p_json_blob     JSONB       DEFAULT '{}',
    p_system_blob   JSONB       DEFAULT '{}',
    p_is_test       BOOLEAN     DEFAULT FALSE
) RETURNS TABLE(entity_id UUID, event_id UUID) AS $$
DECLARE
    v_schema_version TEXT;
    v_entity_id      UUID;
    v_event_id       UUID;
    v_blob           JSONB;
BEGIN
    -- Get current schema version for this entity type
    SELECT schema_version INTO STRICT v_schema_version
    FROM entity_type_dict WHERE id = p_entity_type;

    -- Merge _v into the blob
    v_blob := jsonb_set(p_json_blob, '{_v}', to_jsonb(v_schema_version));

    -- Insert entity
    INSERT INTO entity_index (
        entity_type, entity_json_blob, entity_state, entity_is_test,
        created_system_json_blob, last_updated_system_json_blob
    ) VALUES (
        p_entity_type, v_blob, 'ACTIVE', p_is_test,
        p_system_blob, p_system_blob
    ) RETURNING entity_index.entity_id INTO v_entity_id;

    -- Record CREATE event
    INSERT INTO entity_events_idx (
        entity_id, entity_type, event_type, entity_json_blob, system_json_blob
    ) VALUES (
        v_entity_id, p_entity_type, 'CREATE', v_blob, p_system_blob
    ) RETURNING entity_events_idx.event_id INTO v_event_id;

    -- Link event to entity
    UPDATE entity_index
    SET entity_event_ids_list = array_append(entity_event_ids_list, v_event_id)
    WHERE entity_index.entity_id = v_entity_id;

    RETURN QUERY SELECT v_entity_id, v_event_id;
END;
$$ LANGUAGE plpgsql;

-- ── Helper: Update entity with event ───────────────────────────────────

CREATE OR REPLACE FUNCTION update_entity(
    p_entity_id     UUID,
    p_json_blob     JSONB       DEFAULT NULL,
    p_system_blob   JSONB       DEFAULT '{}',
    p_new_state     TEXT        DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_event_id      UUID;
    v_current_blob  JSONB;
    v_merged_blob   JSONB;
BEGIN
    -- Get current blob
    SELECT entity_json_blob INTO STRICT v_current_blob
    FROM entity_index WHERE entity_index.entity_id = p_entity_id;

    -- Merge new fields into existing blob (shallow merge, preserves _v)
    IF p_json_blob IS NOT NULL THEN
        v_merged_blob := v_current_blob || p_json_blob;
    ELSE
        v_merged_blob := v_current_blob;
    END IF;

    -- Update entity
    UPDATE entity_index SET
        entity_json_blob              = v_merged_blob,
        last_updated_date             = NOW(),
        last_updated_system_json_blob = p_system_blob,
        entity_state                  = COALESCE(p_new_state, entity_state)
    WHERE entity_index.entity_id = p_entity_id;

    -- Record UPDATE event
    INSERT INTO entity_events_idx (
        entity_id, entity_type, event_type, entity_json_blob, system_json_blob
    ) VALUES (
        p_entity_id,
        (SELECT entity_type FROM entity_index WHERE entity_index.entity_id = p_entity_id),
        'UPDATE', v_merged_blob, p_system_blob
    ) RETURNING entity_events_idx.event_id INTO v_event_id;

    -- Link event
    UPDATE entity_index
    SET entity_event_ids_list = array_append(entity_event_ids_list, v_event_id)
    WHERE entity_index.entity_id = p_entity_id;

    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;

-- ── Helper: Deactivate entity ──────────────────────────────────────────

CREATE OR REPLACE FUNCTION deactivate_entity(
    p_entity_id     UUID,
    p_system_blob   JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    v_event_id UUID;
BEGIN
    -- Update state
    UPDATE entity_index SET
        entity_state                  = 'DEACTIVATED',
        last_updated_date             = NOW(),
        last_updated_system_json_blob = p_system_blob
    WHERE entity_index.entity_id = p_entity_id;

    -- Record DEACTIVATE event
    INSERT INTO entity_events_idx (
        entity_id, entity_type, event_type, entity_json_blob, system_json_blob
    ) VALUES (
        p_entity_id,
        (SELECT entity_type FROM entity_index WHERE entity_index.entity_id = p_entity_id),
        'DEACTIVATE',
        (SELECT entity_json_blob FROM entity_index WHERE entity_index.entity_id = p_entity_id),
        p_system_blob
    ) RETURNING entity_events_idx.event_id INTO v_event_id;

    -- Link event
    UPDATE entity_index
    SET entity_event_ids_list = array_append(entity_event_ids_list, v_event_id)
    WHERE entity_index.entity_id = p_entity_id;

    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;
