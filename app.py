import os
import sqlite3
import math
from flask import Flask, redirect, render_template, request, session, abort
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import db
import users, config, transcriptions, text_splitter_help_functions, help_functions


UPLOAD_FOLDER='./static/audio' 

app = Flask(__name__)
app.secret_key = config.secret_key

MEGABYTE = (2 ** 10) ** 2
app.config['MAX_CONTENT_LENGTH'] = None
app.config['MAX_FORM_MEMORY_SIZE'] = 5 * MEGABYTE
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def index():
    user = None
    if "user_id" in session:
        user_id = session["user_id"]
        user = users.get_user(user_id)
    transcription_array = transcriptions.get_transcriptions()

    return render_template("index.html", transcriptions=transcription_array, user=user)


@app.route("/create_transcription", methods=["GET"])
def create_transcription():
    return render_template("create.html")


@app.route("/new_transcription", methods=["POST"])
def new_transcription():
    title = request.form["title"]
    source_path = request.form["source_path"]
    source = request.form["source"]
    genre = request.form["genre"]
    raw_content = request.form["raw_content"]
    user_id = session["user_id"]
    license = request.form["license"]
    record_date = request.form["record_date"] 
    duration_sec = request.form["duration_sec"]
    extra_meta_data = request.form["extra_meta_data"]

    file = request.files['file']
 
    if file and help_functions.allowed_file(file.filename):
        filename = secure_filename(file.filename)
        new_filename = filename[:]
        target_file_path= os.path.join(app.config['UPLOAD_FOLDER'], filename)
        counter = 1
        while os.path.exists(target_file_path):
            new_filename= str(counter) + "--" + filename 
            target_file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename) 
            counter += 1

        file.save(target_file_path)
        source_path= new_filename


    if ':' in duration_sec:
        duration_sec=help_functions.convert_hms_to_seconds(duration_sec)

    transcription_id = transcriptions.add_transcription(title, source_path, source, genre, raw_content, user_id,
                                                        license, record_date, duration_sec, extra_meta_data)
    return redirect("/transcription/" + str(transcription_id))


@app.route("/transcription/<int:transcription_id>")
@app.route("/transcription/<int:transcription_id>/<int:page>")
def show_transcription(transcription_id, page=1):
    page_size = 20
    audiotime = request.args.get('audiotime')
    text_fragments_count = transcriptions.get_text_fragments_count(transcription_id)
    # text_fragments_count = len(text_fragments)
    text_fragments_count = text_fragments_count["count"]
    page_count = math.ceil(text_fragments_count / page_size)
    page_count = max(page_count, 1)
    print(page_count, text_fragments_count)
    if page < 1:
        return redirect("/transcription/" + str(transcription_id) + "/1")
    if page > page_count:
        return redirect("/transcription/" + str(transcription_id) + "/" + str(page_count))
    

    text_fragments = transcriptions.get_text_fragments_paginated(transcription_id, page, page_size)
    text_fragments_with_secs = [
        (id, int(start_ms / 1000), help_functions.convert_seconds_to_hms(int(start_ms / 1000)), start_ms, words) for
        id, start_ms, words in text_fragments]

    transcription = transcriptions.get_transcription(transcription_id)
    if not transcription:
        abort(404)
    source_path=transcription['source_path']
    source_path_file_name = os.path.basename(source_path)
    local_audio_file_copy = os.path.join('static/audio', source_path_file_name)
    local_audio_file_copy_exists= os.path.exists(local_audio_file_copy)
    audio_file_path = f"audio/{source_path_file_name}"
    if not local_audio_file_copy_exists:
        # filenames from the whole source_path string
        source_path_fallback = source_path.replace("\\",'--')
        local_audio_file_copy = os.path.join('static/audio', source_path_fallback)
        local_audio_file_copy_exists= os.path.exists(local_audio_file_copy)
        audio_file_path = f"audio/{source_path_fallback}"


    return render_template("transcription.html", transcription=transcription, text_fragments=text_fragments_with_secs, 
                           convert_seconds_to_hms=help_functions.convert_seconds_to_hms,
                           page=page, page_count=page_count, local_audio_file_copy_exists=local_audio_file_copy_exists, audio_file_path=audio_file_path, audiotime=audiotime)


@app.route("/add_text_fragment/<int:transcription_id>", methods=["GET", "POST"])
def add_text_fragment(transcription_id):
    return_page = request.args.get("return_page")
    if request.method == "GET":
        return render_template("add_text_fragment.html", transcription_id=transcription_id, return_page=return_page)
    if request.method == "POST":
        return_page = request.form["return_page"]
        start_time = request.form["start_time"]
        start_ms = help_functions.convert_hms_to_seconds(start_time)  * 1000
  
        words = request.form["words"]
        try:
            transcriptions.add_text_fragment(start_ms, words, transcription_id)
        except sqlite3.IntegrityError:
            abort(400)
        page = '/' + str(return_page) if return_page else ''
        #id_anchor = '#t-id-' + str(text_fragment_id)
        return redirect("/transcription/" + str(transcription_id) + page) # + id_anchor)



@app.route("/text_fragments/<int:transcription_id>")
def text_fragments(transcription_id):
    text_fragments = transcriptions.get_text_fragments(transcription_id)
    text_fragments_with_secs = [(id, int(start_ms / 1000), start_ms, words) for id, start_ms, words in text_fragments]
    transcription = transcriptions.get_transcription(transcription_id)
    if not transcription:
        abort(404)
    
    if len(text_fragments) > 0:
        return render_template("transcription.html", transcription=transcription,
                               text_fragments=text_fragments_with_secs)

    raw_content = transcription['raw_content']
    test_fragments_with_timestamps = []
    if transcription['source'] == 'youtube':
        test_fragments_with_timestamps = text_splitter_help_functions.split_youtube_transcription(raw_content)
    elif transcription['source'] == 'word':
        test_fragments_with_timestamps = text_splitter_help_functions.split_word_transcription(raw_content)
    elif transcription['source'] == 'webvtt':
        test_fragments_with_timestamps = text_splitter_help_functions.split_web_vtt(raw_content)
    else:
        print(transcription['source'], " text source not supported")

    transcription_id = transcription['id']
    try:
        for start_ms, words in test_fragments_with_timestamps:
            transcriptions.add_text_fragment(start_ms, words, transcription_id)
    except sqlite3.IntegrityError:
            abort(400)
    return redirect("/transcription/" + str(transcription["id"]))


@app.route("/search")
def search():
    text_query = request.args.get("query")
    if not text_query:
        text_query = ""
    results = transcriptions.search(text_query) if text_query else []
    return render_template("search.html", text_query=text_query, results=results)

@app.route("/search_titles")
def search_titles():
    title_query = request.args.get("query")
    if not title_query:
        title_query = ""
    results = transcriptions.search_titles(title_query) if title_query else []
    return render_template("search.html", title_query=title_query, title_search_results=results)

@app.route("/search_file_name")
def search_file_name():
    file_name_query = request.args.get("query")
    if not file_name_query:
        file_name_query = ""
    results = transcriptions.search_file_name(file_name_query) if file_name_query else []
    return render_template("search.html", file_name_query=file_name_query, title_search_results=results)


@app.route("/show_search_result_context/<int:id>")
def show_search_result_context(id):
    text_context = transcriptions.get_text_fragment_context(id)
    title = ""
    transcription_id = None
    if len(text_context) > 0:
        title = text_context[0]['title']
        transcription_id = text_context[0]['transcription_id']

    return render_template("show_search_result_context.html", text_context=text_context, title=title,
                           transcription_id=transcription_id, id=id)


@app.route("/edit_text_fragment/<int:text_fragment_id>", methods=["GET", "POST"])
def edit_text_fragment(text_fragment_id):
    return_page = request.args.get("return_page")
    text_fragment = transcriptions.get_text_fragment(text_fragment_id)
 
    if not text_fragment:
        abort(404)

    if request.method == "GET":
        return render_template("edit_text_fragment.html", text_fragment=text_fragment, return_page=return_page)

    if request.method == "POST":
        return_page = request.form["return_page"]
        words = request.form["words"]
        transcriptions.update_text(text_fragment["id"], words)
        page = '/' + str(return_page) if return_page else ''
        id_anchor = '#t-id-' + str(text_fragment_id)
        return redirect("/transcription/" + str(text_fragment["transcription_id"]) + page + id_anchor)


@app.route("/remove_text_fragment/<int:text_fragment_id>", methods=["GET", "POST"])
def remove_text_fragment(text_fragment_id):
    return_page = request.args.get("return_page")
    text_fragment = transcriptions.get_text_fragment(text_fragment_id)
    if not text_fragment:
        abort(404)
    transcription_id = text_fragment["transcription_id"]
    if request.method == "GET":
        return render_template("remove_text.html", text_fragment=text_fragment, return_page=return_page)

    if request.method == "POST":
        return_page = request.form["return_page"]
        page = '/' + str(return_page) if return_page else ''
        id_anchor = ''
        if "continue" in request.form:
            transcriptions.remove_text_fragment(text_fragment["id"])
        else:
            id_anchor = '#t-id-' + str(text_fragment_id)
    return redirect("/transcription/" + str(transcription_id) + page + id_anchor)


@app.route("/remove/<int:transcription_id>", methods=["GET", "POST"])
def remove_transcription(transcription_id):
    transcription = transcriptions.get_transcription(transcription_id)
    if not transcription:
        abort(404)
    if transcription["user_id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        return render_template("remove.html", transcription=transcription)

    if request.method == "POST":
        if "continue" in request.form:
            transcriptions.remove_transcription(transcription["id"])
    return redirect("/")


@app.route("/remove_transcription_split_text/<int:transcription_id>", methods=["GET", "POST"])
def remove_transcription_split_text(transcription_id):
    transcription = transcriptions.get_transcription(transcription_id)
    if not transcription:
        abort(404)
    if request.method == "GET":
        return render_template("remove_transcription_split_text.html", transcription=transcription)

    if request.method == "POST":
        if "continue" in request.form:
            transcriptions.remove_transcription_split_text(transcription["id"])
    return redirect("/transcription/" + str(transcription["id"]))


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
        license = request.form["license"]
        record_date = request.form["record_date"]
        duration_sec = request.form["duration_sec"]
        extra_meta_data = request.form["extra_meta_data"]
        if ':' in duration_sec:
            duration_sec=help_functions.convert_hms_to_seconds(duration_sec)

        # file = request.files['sound_file']
        file = request.files['file']

        if file and help_functions.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            new_filename = filename[:]
            target_file_path= os.path.join(app.config['UPLOAD_FOLDER'], filename)
            counter = 1
            while os.path.exists(target_file_path):
                new_filename= str(counter) + "--" + filename 
                target_file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename) 
                counter += 1

            file.save(target_file_path)
            source_path= new_filename

        transcriptions.update_transcription(transcription["id"], title, source_path, source, genre, license,
                                            raw_content, record_date, duration_sec, extra_meta_data)
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

    return render_template("registered.html")


def require_login():
    if "user_id" not in session:
        abort(403)


@app.route("/logout")
def logout():
    require_login()

    del session["user_id"]
    return redirect("/")
