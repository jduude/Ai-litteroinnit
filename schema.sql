CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);



CREATE TABLE transcriptions (
    id INTEGER PRIMARY KEY,
    title TEXT,
    source_path TEXT,
    source TEXT,
    genre TEXT,
    raw_content TEXT,
    user_id INTEGER REFERENCES users,
    created DATETIME DEFAULT NULL, 
    last_modified DATETIME DEFAULT NULL,
    license TEXT,
    record_date DATE NULL,
    duration_sec INTEGER NULL,
    extra_meta_data TEXT,
    allow_collaboration BOOLEAN DEFAULT FALSE
);

CREATE TABLE text_fragments (
    id INTEGER PRIMARY KEY,
    start_ms INTEGER,
    words TEXT,
    transcription_id INTEGER REFERENCES transcriptions,
    trashed BOOLEAN 
);

CREATE TABLE text_fragment_edits (
    id INTEGER PRIMARY KEY,
    start_ms INTEGER,
    words TEXT,
    version INTEGER,
    text_fragment_id INTEGER REFERENCES text_fragments DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users
);

CREATE INDEX idx_transcriptions_text_fragments ON text_fragments (transcription_id);