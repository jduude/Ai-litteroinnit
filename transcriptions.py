import db

def get_transcriptions():
    sql = """SELECT t.id, t.title, t.genre, t.source_path
             FROM transcriptions t
             ORDER BY t.id DESC"""
    return db.query(sql)

def add_transcription(title, source_path, source, genre, raw_content, user_id):
    sql = "INSERT INTO transcriptions (title, source_path, source, genre, raw_content, user_id) VALUES (?, ?, ?, ?, ?, ?)"
    db.execute(sql, [title, source_path, source, genre, raw_content, user_id])
    transcription_id = db.last_insert_id()
    return transcription_id


def get_transcription(transcription_id):
    sql = "SELECT id, title,  source_path, source, genre, raw_content FROM transcriptions WHERE id = ?"
    return db.query(sql, [transcription_id])[0]


def remove_transcription(transcription_id):
    sql = "DELETE FROM transcriptions WHERE id = ?"
    db.execute(sql, [transcription_id])
