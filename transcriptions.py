import db


def get_transcriptions():
    sql = """SELECT t.id, t.title, t.genre, t.source_path, t.created, t.last_modified
             FROM transcriptions t
             ORDER BY t.id DESC"""
    return db.query(sql)


def add_transcription(title, source_path, source, genre, raw_content, user_id):
    sql = """INSERT INTO transcriptions 
    (title, source_path, source, genre, raw_content, user_id, created, last_modified) 
    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"""
    db.execute(sql, [title, source_path, source, genre, raw_content, user_id])
    transcription_id = db.last_insert_id()
    return transcription_id


def get_transcription(transcription_id):
    sql = """SELECT id, title,  source_path, source, 
        genre, raw_content, user_id, created, last_modified
        FROM transcriptions WHERE id = ?"""
    return db.query(sql, [transcription_id])[0]


def remove_transcription(transcription_id):
    sql = "DELETE FROM transcriptions WHERE id = ?"
    db.execute(sql, [transcription_id])


def update_transcription(transcription_id, title, source_path, source, genre):
    sql = "UPDATE transcriptions SET title = ?, source_path = ?, source = ?, genre = ?  WHERE id = ?"
    db.execute(sql, [title, source_path, source, genre, transcription_id])


def get_text_fragments(transcription_id):
    sql = "SELECT id, start_ms, words FROM text_fragments WHERE transcription_id = ?  AND trashed is NULL"
    return db.query(sql, [transcription_id])

def get_text_fragments_paginated( transcription_id, page, page_size):
    sql = "SELECT id, start_ms, words FROM text_fragments WHERE transcription_id = ?  AND trashed is NULL LIMIT ? OFFSET ?"
    limit = page_size
    offset = page_size * (page - 1)
    return db.query(sql, [transcription_id, limit, offset])

def get_text_fragments_count(transcription_id):
    sql = "SELECT count(id) as count FROM text_fragments WHERE transcription_id = ?  AND trashed is NULL"
    return db.query(sql, [transcription_id])[0]

def get_text_fragment(text_fragment_id):
    sql = "SELECT id, start_ms, words, transcription_id FROM text_fragments WHERE id = ?"
    return db.query(sql, [text_fragment_id])[0]


def add_text_fragment(start_ms, words, transcription_id):
    sql = """INSERT INTO text_fragments (start_ms, words, transcription_id) VALUES
             (?, ?, ?)"""
    db.execute(sql, [start_ms, words, transcription_id])

def remove_text_fragment(text_fragment_id):
    sql = "UPDATE text_fragments SET trashed = 1 WHERE id = ?"
    db.execute(sql, [text_fragment_id])


def remove_transcription_split_text(transcription_id):
    sql = "DELETE FROM text_fragments WHERE transcription_id = ?"
    db.execute(sql, [transcription_id])

def update_text(id, words):
    sql = "UPDATE text_fragments SET words = ? WHERE id = ?"
    db.execute(sql, [words, id])

    
def search(query):
    sql = """SELECT t.id, t.start_ms, t.words, t.transcription_id, tr.title
             FROM text_fragments t, transcriptions tr
             WHERE  tr.id= t.transcription_id AND t.words LIKE ?
            """
    return db.query(sql, ["%" + query + "%"])
    
def get_text_fragment_context(id):
    start = id- 5
    end = id + 5
    if start < 0:
        start = 0
    sql = """SELECT t.id, t.start_ms, t.words, t.transcription_id, tr.title
             FROM text_fragments t, transcriptions tr
             WHERE tr.id= t.transcription_id AND t.trashed is NULL AND t.id >= ? and   t.id <= ?
            """
    return db.query(sql, [start, end])