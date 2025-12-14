import db


def get_transcriptions():
    sql = """SELECT t.id, t.title, t.genre, t.source_path, t.created, t.last_modified,
             t.license, t.record_date, t.duration_sec, t.extra_meta_data, u.id as user_id, u.username
             FROM transcriptions t
             JOIN users u ON u.id =  t.user_id
             ORDER BY t.id DESC"""
    return db.query(sql)


def get_transcriptions_paginated(page, page_size):
    sql = """SELECT t.id, t.title, t.genre, t.source_path, t.created, t.last_modified,
             t.license, t.record_date, t.duration_sec, t.extra_meta_data, u.id as user_id, u.username
             FROM transcriptions t
             JOIN users u ON u.id =  t.user_id
             ORDER BY t.id DESC
             LIMIT ? OFFSET ?"""

    limit = page_size
    offset = page_size * (page - 1)
    return db.query(sql, [limit, offset])


def get_transcriptions_count():
    sql = "SELECT count(id) as count FROM transcriptions;"
    result = db.query(sql)
    return result[0]["count"] if result else 0


def add_transcription(
        title,
        source_path,
        source,
        genre,
        raw_content,
        user_id,
        license,
        record_date,
        duration_sec,
        extra_meta_data, allow_collaboration):
    sql = """INSERT INTO transcriptions
    (title, source_path, source, genre, raw_content, user_id, license,
     record_date, duration_sec, extra_meta_data, allow_collaboration, created, last_modified)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"""
    db.execute(sql,
               [title,
                source_path,
                source,
                genre,
                raw_content,
                user_id,
                license,
                record_date,
                duration_sec,
                extra_meta_data, allow_collaboration])
    transcription_id = db.last_insert_id()
    return transcription_id


def get_transcription(transcription_id):
    sql = """SELECT id, title,  source_path, source,
        genre, raw_content, user_id, created, last_modified, license, record_date, duration_sec, extra_meta_data, allow_collaboration
        FROM transcriptions WHERE id = ?"""
    result = db.query(sql, [transcription_id])
    return result[0] if result else None


def remove_transcription(transcription_id):
    sql = "DELETE FROM transcriptions WHERE id = ?"
    db.execute(sql, [transcription_id])


def update_transcription(
        transcription_id,
        title,
        source_path,
        source,
        genre,
        license,
        raw_content,
        record_date,
        duration_sec,
        extra_meta_data, allow_collaboration):
    sql = """UPDATE transcriptions SET title = ?, source_path = ?, source = ?,
            genre = ?, last_modified=CURRENT_TIMESTAMP, license = ?, raw_content= ?,  record_date= ?,
            duration_sec= ?, extra_meta_data= ?, allow_collaboration = ? WHERE id = ?"""
    db.execute(sql,
               [title,
                source_path,
                source,
                genre,
                license,
                raw_content,
                record_date,
                duration_sec,
                extra_meta_data, allow_collaboration,
                transcription_id])


def get_text_fragments(transcription_id):
    sql = "SELECT id, start_ms, words FROM text_fragments WHERE transcription_id = ?  AND trashed is NULL"
    return db.query(sql, [transcription_id])


def get_text_fragments_paginated(transcription_id, page, page_size):
    sql = """SELECT id, start_ms, words, 0 as version
          FROM text_fragments WHERE transcription_id = ?
          AND trashed is NULL ORDER BY start_ms
          LIMIT ? OFFSET ?"""
    limit = page_size
    offset = page_size * (page - 1)
    result =  db.query(sql, [transcription_id, limit, offset])
    if result is None:
        return []

    text_ids = [row['id'] for row in result]
    id_placeholders = ','.join('?' for _ in text_ids)
    edits_sql = f"""SELECT tfe.text_fragment_id as id, tfe.start_ms, tfe.words, tfe.version
                            FROM text_fragment_edits tfe
                            WHERE tfe.text_fragment_id IN ({id_placeholders})
                              AND tfe.version = (
                                  SELECT MAX(tfe2.version)
                                  FROM text_fragment_edits tfe2
                                  WHERE tfe2.text_fragment_id = tfe.text_fragment_id
                              )"""
    edits = db.query(edits_sql, text_ids)
    edits_ids = [row['id'] for row in edits]
    results_with_edits = []
    for row in  result:
        if row['id'] in edits_ids:
            edited_row = [edit for edit in edits if edit['id'] == row['id']][0]
            results_with_edits.append(edited_row)
        else:
            results_with_edits.append(row)
    return results_with_edits




def get_text_fragments_count(transcription_id):
    sql = "SELECT count(id) as count FROM text_fragments WHERE transcription_id = ?  AND trashed is NULL"
    result = db.query(sql, [transcription_id])
    return result[0] if result else 0


def get_text_fragment(text_fragment_id):

    sql = """SELECT tfe.start_ms, tfe.words, tfe.version, tfe.text_fragment_id as id, tfe.created_at, tfe.user_id, tf.transcription_id
            FROM text_fragment_edits tfe, text_fragments tf 
            WHERE text_fragment_id = ? and tf.id = tfe.text_fragment_id
            ORDER BY version DESC LIMIT 1"""
    result = db.query(sql, [text_fragment_id])
    if result:
        return result[0]
    sql = "SELECT id, start_ms, words, transcription_id FROM text_fragments WHERE id = ?"
    result = db.query(sql, [text_fragment_id])
    return result[0] if result else None


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


def add_versioned_text_fragment(original_id, start_ms, version, words, user_id):
    sql = """INSERT INTO text_fragment_edits 
        (start_ms, version, words, text_fragment_id, created_at, user_id) 
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)"""
    db.execute(sql, [start_ms, version, words, original_id, user_id])


def search(query):
    sql = """SELECT t.id, t.start_ms, t.words, t.transcription_id, tr.title
             FROM text_fragments t, transcriptions tr
             WHERE  tr.id= t.transcription_id AND t.words LIKE ?
            """
    result = db.query(sql, ["%" + query + "%"])
    sql2 = """SELECT t.id, te.start_ms, te.words, t.transcription_id, tr.title
             FROM text_fragment_edits te, text_fragments t, transcriptions tr
             WHERE te.text_fragment_id = t.id and tr.id= t.transcription_id AND
             te.version = (
                            SELECT MAX(tfe2.version)
                            FROM text_fragment_edits tfe2
                            WHERE tfe2.text_fragment_id = te.text_fragment_id
                            )
             AND te.words LIKE ?
            """
    result2 = db.query(sql2, ["%" + query + "%"])
    text_ids2 = [row['id'] for row in result2]   
    result_filtered = [row for row in result if row['id'] not in text_ids2]
    result2.extend(result_filtered)
    result2.sort(key=lambda x: x['id'])
    return result2


def search_titles(query):
    sql = """SELECT id, title,  source_path, source,
                genre, raw_content, user_id, created, last_modified, license,
                record_date, duration_sec, extra_meta_data
             FROM transcriptions
             WHERE  title LIKE ?
            """
    return db.query(sql, ["%" + query + "%"])


def search_file_name(query):
    sql = """SELECT id, title,  source_path, source,
                genre, raw_content, user_id, created, last_modified, license,
                record_date, duration_sec, extra_meta_data
             FROM transcriptions
             WHERE  source_path LIKE ?
            """
    return db.query(sql, ["%" + query + "%"])


def get_text_fragment_context(id):
    start = id - 5
    end = id + 5
    if start < 0:
        start = 0
    sql = """SELECT t.id, t.start_ms, t.words, t.transcription_id, tr.title
             FROM text_fragments t, transcriptions tr
             WHERE tr.id= t.transcription_id AND t.trashed is NULL AND t.id >= ? and   t.id <= ?
            """
    return db.query(sql, [start, end])


def get_duplicate_files():
    sql = """SELECT t.id, t.source_path
            FROM transcriptions t
            JOIN (
                SELECT source_path
                FROM transcriptions
                GROUP BY source_path
                HAVING COUNT(id) > 1
            ) dup ON t.source_path = dup.source_path"""
    return db.query(sql)


def get_genre_stats():
    sql = """select count(id) as count, genre
            from transcriptions
            group by genre order by count desc;"""
    return db.query(sql)


def get_source_stats():
    sql = """select count(id) as count, source
            from transcriptions
            group by source order by count desc;"""
    return db.query(sql)


def get_user_stats():
    sql = """select count(t.id) as count, t.user_id, u.username
            from transcriptions t
            JOIN users u ON u.id = user_id
            group by t.user_id order by count desc;
            """
    return db.query(sql)


def get_transcriptions_of_user(user_id):
    sql = """SELECT t.id, t.title, t.genre, t.source_path, t.created, t.last_modified
             FROM transcriptions t
             WHERE t.user_id = ?
             ORDER BY t.last_modified DESC"""
    return db.query(sql, [user_id])


def get_transcriptions_by_genre(genre):
    sql = """SELECT t.id, t.title, t.genre, t.source_path, t.created, t.last_modified
             FROM transcriptions t
             WHERE t.genre = ?
             ORDER BY t.last_modified DESC"""
    return db.query(sql, [genre])

def get_transcriptions_by_source(source):
    sql = """SELECT t.id, t.title, t.genre, t.source_path, t.created, t.last_modified
             FROM transcriptions t
             WHERE t.source = ?
             ORDER BY t.last_modified DESC"""
    return db.query(sql, [source])
