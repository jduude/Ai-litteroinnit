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
    user_id INTEGER REFERENCES users
);
