import random
import sqlite3

db = sqlite3.connect("database_test.db")

db.execute("DELETE FROM users")
db.execute("DELETE FROM transcriptions")
db.execute("DELETE FROM text_fragments")

user_count = 1000
transcriptions_count = 10**5
text_fragments_count = 10**7

for i in range(1, user_count + 1):
    db.execute("INSERT INTO users (username) VALUES (?)",
               ["user" + str(i)])

for i in range(1, transcriptions_count + 1):
    user_id = random.randint(1, user_count)
    db.execute("INSERT INTO transcriptions (title, user_id) VALUES (?, ?)",
               ["transcription " + str(i), user_id])

for i in range(1, text_fragments_count + 1):
    user_id = random.randint(1, user_count)
    transcription_id = random.randint(1, transcriptions_count)
    db.execute("""INSERT INTO text_fragments (start_ms, words, transcription_id)
                  VALUES (?, ?, ?)""",
               [i * 1000 + 2, "tekstitystä " + str(i),  transcription_id])

db.commit()
db.close()