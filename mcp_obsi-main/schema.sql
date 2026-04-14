PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS memories (
    rowid INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id TEXT NOT NULL UNIQUE,
    schema_version TEXT NOT NULL DEFAULT '2.0',
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    roles_json TEXT NOT NULL CHECK (json_valid(roles_json)),
    topics_json TEXT NOT NULL CHECK (json_valid(topics_json)),
    entities_json TEXT NOT NULL CHECK (json_valid(entities_json)),
    projects_json TEXT NOT NULL CHECK (json_valid(projects_json)),
    tags_json TEXT NOT NULL CHECK (json_valid(tags_json)),
    raw_refs_json TEXT NOT NULL CHECK (json_valid(raw_refs_json)),
    relations_json TEXT NOT NULL CHECK (json_valid(relations_json)),
    tags_text TEXT NOT NULL DEFAULT '',
    topics_text TEXT NOT NULL DEFAULT '',
    entities_text TEXT NOT NULL DEFAULT '',
    projects_text TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    status TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    due_at TEXT,
    language TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_memories_status_occurred_at
    ON memories(status, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_source
    ON memories(source);
CREATE INDEX IF NOT EXISTS idx_memories_due_at
    ON memories(due_at);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    title,
    content,
    tags_text,
    topics_text,
    entities_text,
    projects_text,
    content='memories',
    content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(
        rowid, title, content, tags_text, topics_text, entities_text, projects_text
    ) VALUES (
        new.rowid, new.title, new.content, new.tags_text, new.topics_text, new.entities_text, new.projects_text
    );
END;

CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
    INSERT INTO memories_fts(
        memories_fts, rowid, title, content, tags_text, topics_text, entities_text, projects_text
    ) VALUES (
        'delete', old.rowid, old.title, old.content, old.tags_text, old.topics_text, old.entities_text, old.projects_text
    );
END;

CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
    INSERT INTO memories_fts(
        memories_fts, rowid, title, content, tags_text, topics_text, entities_text, projects_text
    ) VALUES (
        'delete', old.rowid, old.title, old.content, old.tags_text, old.topics_text, old.entities_text, old.projects_text
    );
    INSERT INTO memories_fts(
        rowid, title, content, tags_text, topics_text, entities_text, projects_text
    ) VALUES (
        new.rowid, new.title, new.content, new.tags_text, new.topics_text, new.entities_text, new.projects_text
    );
END;
