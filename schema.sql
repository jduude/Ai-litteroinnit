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
    extra_meta_data TEXT
);

CREATE TABLE text_fragments (
    id INTEGER PRIMARY KEY,
    start_ms INTEGER,
    words TEXT,
    transcription_id INTEGER REFERENCES transcriptions,
    trashed BOOLEAN 
);
