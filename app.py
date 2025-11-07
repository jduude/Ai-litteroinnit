import sqlite3
import json
from flask import Flask, redirect, render_template, request, session
from werkzeug.security import generate_password_hash
import db
import users, config, transcriptions

app = Flask(__name__)
app.secret_key = config.secret_key

MEGABYTE = (2 ** 10) ** 2
app.config['MAX_CONTENT_LENGTH'] = None
app.config['MAX_FORM_MEMORY_SIZE'] = 5 * MEGABYTE


@app.route("/")
def index():
    user_id = session["user_id"]
    user = users.get_user(user_id)
    transcription_array = transcriptions.get_transcriptions()
    return render_template("index.html", transcriptions=transcription_array, user= user)


@app.route("/new_transcription", methods=["POST"])
def new_transcription():
    title = request.form["title"]
    source_path = request.form["source_path"]
    source = request.form["source"]
    genre = request.form["genre"]
    raw_content = request.form["raw_content"]
    user_id = session["user_id"]

    transcription_id = transcriptions.add_transcription(title, source_path, source, genre, raw_content, user_id)
    return redirect("/transcription/" + str(transcription_id))


@app.route("/transcription/<int:transcription_id>")
def show_transcription(transcription_id):
    text_fragments = transcriptions.get_text_fragments(transcription_id)
    text_fragments_with_secs= [ ( id, int(start_ms/1000), start_ms, words) for id, start_ms, words in text_fragments]

    transcription = transcriptions.get_transcription(transcription_id)
    return render_template("transcription.html", transcription=transcription,  text_fragments=text_fragments_with_secs)

@app.route("/text_fragments/<int:transcription_id>")
def text_fragments(transcription_id):
    text_fragments = transcriptions.get_text_fragments(transcription_id)
    text_fragments_with_secs= [ ( id, int(start_ms/1000), start_ms, words) for id, start_ms, words in text_fragments]
    transcription = transcriptions.get_transcription(transcription_id)
    print(len(text_fragments))
    if len(text_fragments) > 0:
        return render_template("transcription.html", transcription=transcription,
                               text_fragments=text_fragments_with_secs)

    raw_content = transcription['raw_content']
    if transcription['source'] == 'youtube':
        timed_text_dict = json.loads(raw_content)
        events = timed_text_dict['events']
        test_fragments_with_timestamps = [(e['tStartMs'], "".join([s['utf8'] for s in e['segs']])) for e in events if
                                          'segs' in e]
        test_fragments_with_timestamps = [(tStartMsm, text) for tStartMsm, text in test_fragments_with_timestamps if
                                          text.strip() != '']

        transcription_id = transcription['id']
        for start_ms, words in test_fragments_with_timestamps:
            transcriptions.add_text_fragment( start_ms, words, transcription_id )

    return redirect("/transcription/" + str(transcription["id"]))

@app.route("/search")
def search():
    query = request.args.get("query")
    if not query:
        query = ""
    results = transcriptions.search(query) if query else []
    return render_template("search.html", query=query, results=results)

@app.route("/show_search_result_context/<int:id>")
def show_search_result_context(id):

    text_context=transcriptions.get_text_fragment_context(id)
    title= ""
    transcription_id = None
    if len(text_context) > 0:
        title= text_context[0]['title']
        transcription_id= text_context[0]['transcription_id']
   
    return render_template("show_search_result_context.html", text_context=text_context, title=title, transcription_id=transcription_id, id=id)

@app.route("/edit_text_fragment/<int:text_fragment_id>", methods=["GET", "POST"])
def edit_text_fragment(text_fragment_id):
    text_fragment = transcriptions.get_text_fragment(text_fragment_id)

    if request.method == "GET":
        return render_template("edit_text_fragment.html", text_fragment=text_fragment)

@app.route("/remove/<int:transcription_id>", methods=["GET", "POST"])
def remove_transcription(transcription_id):
    transcription = transcriptions.get_transcription(transcription_id)

    if request.method == "GET":
        return render_template("remove.html", transcription=transcription)

    if request.method == "POST":
        if "continue" in request.form:
            transcriptions.remove_transcription(transcription["id"])
        return redirect("/")


@app.route("/edit/<int:transcription_id>", methods=["GET", "POST"])
def edit_transcription(transcription_id):
    transcription = transcriptions.get_transcription(transcription_id)

    if request.method == "GET":
        return render_template("edit.html", transcription=transcription)

    if request.method == "POST":
        title = request.form["title"]
        source_path = request.form["source_path"]
        source = request.form["source"]
        genre = request.form["genre"]
        raw_content = request.form["raw_content"]
        transcriptions.update_transcription(transcription["id"],  title, source_path, source, genre)
        return redirect("/transcription/" + str(transcription["id"]))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user_id = users.check_login(username, password)
        if user_id:
            session["user_id"] = user_id
            return redirect("/")
        else:
            return "VIRHE: väärä tunnus tai salasana"


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]

        if password1 != password2:
            return "VIRHE: salasanat eivät ole samat"

        try:
            users.create_user(username, password1)
            return "Tunnus luotu"
        except sqlite3.IntegrityError:
            return "VIRHE: tunnus on jo varattu"


@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        return "VIRHE: salasanat eivät ole samat"
    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return "VIRHE: tunnus on jo varattu"

    return "Tunnus luotu"
