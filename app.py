"""Flask application for managing ai transcriptions.

This app provides a web application for adding, editing, and searching
transcriptions. It supports various transcription formats (YouTube, Word, WebVTT)
and allows users to view, edit, and organize transcription text fragments with timestamps.

Key features:
    - User authentication and registration
    - Transcription upload with metadata
    - Text fragment management with timestamps
    - Search functionality for transcriptions and content
    - Statistics and user profiles
    - Audio file handling and playback
"""

 
import os
import time
import sqlite3
import math
from flask import Flask, redirect, render_template, request, session, abort, g, flash
from werkzeug.utils import secure_filename
import db
import users
import config
import transcriptions
import text_splitter_help_functions
import help_functions
from user_routes import user_bp, require_login


UPLOAD_FOLDER = './static/audio'

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.register_blueprint(user_bp)

MEGABYTE = (2 ** 10) ** 2
app.config['MAX_CONTENT_LENGTH'] = None
app.config['MAX_FORM_MEMORY_SIZE'] = 5 * MEGABYTE
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.before_request
def before_request():
    """Store the request start time for performance monitoring."""
    g.start_time = time.time()


@app.after_request
def after_request(response):
    """Calculate and log the elapsed time for each request.

    Args:
        response: The Flask response object.

    Returns:
        The unmodified response object.
    """
    elapsed_time = round(time.time() - g.start_time, 2)
    print("elapsed time:", elapsed_time, "s")
    return response


def check_csrf():
    """Validate CSRF token from form matches the session token.

    Raises:
        403: If CSRF token is missing or doesn't match.
    """
    if "csrf_token" not in request.form or "csrf_token" not in session or request.form[
            "csrf_token"] != session["csrf_token"]:
        abort(403)

@app.route("/")
@app.route("/<int:page>")
def index(page=1):
    """Display paginated list of transcriptions on the home page.

    Args:
        page: The page number to display (default: 1).

    Returns:
        Rendered template with transcriptions list.
    """
    user = None
    page_size = 10
    if "user_id" in session:
        user_id = session["user_id"]
        user = users.get_user(user_id)

    transcriptions_count = transcriptions.get_transcriptions_count()
    page_count = math.ceil(transcriptions_count / page_size)
    page_count = max(page_count, 1)
    if page < 1:
        return redirect("/1")
    if page > page_count:
        return redirect("/" + str(page_count))

    transcription_array = transcriptions.get_transcriptions_paginated(
        page, page_size)

    return render_template(
        "index.html",
        transcriptions=transcription_array,
        user=user,
        page=page,
        page_count=page_count)



@app.route("/transcriptions_by_genre/<string:genre>")
def transcriptions_by_genre(genre):
    """Filter transcriptions by genre.

    Args:
        genre: The genre to filter by.

    Returns:
        Redirect to transcriptions_by_filter template.
    """
    require_login()

    transcriptions_list = transcriptions.get_transcriptions_by_genre(genre)
    return render_template("transcriptions_by_filter.html", filter_key=genre, transcriptions=transcriptions_list)



@app.route("/transcriptions_by_source/<string:source>")
def transcriptions_by_source(source):
    """Filter transcriptions by source.

    Args:
        source: The source to filter by.

    Returns:
        Redirect to transcriptions_by_filter template.
    """
    require_login()
    print(source)

    transcriptions_list = transcriptions.get_transcriptions_by_source(source)
    return render_template("transcriptions_by_filter.html", filter_key=source, transcriptions=transcriptions_list)



@app.route("/create_transcription", methods=["GET"])
def create_transcription():
    """Display the form for creating a new transcription.

    Returns:
        Rendered template with transcription creation form.
    """
    require_login()
    return render_template("create.html")


@app.route("/new_transcription", methods=["POST"])
def new_transcription():
    """Process form submission to create a new transcription.

    Validates form data, handles file upload if present, and creates
    a new transcription record in the database.

    Returns:
        Redirect to the newly created transcription page.

    Raises:
        400: If form data exceeds maximum allowed lengths.
    """
    require_login()
    check_csrf()
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
    if 'allow_collaboration' in request.form:
        allow_collaboration = True
    else:
        allow_collaboration = False
    if len(title) > 250:
        abort(
            400,
            description='Otsikkoteksti liian pitkä. Maksimi pituus on 250 merkkiä')
    if len(source_path) > 250:
        abort(
            400,
            description='Tiedoston nimi tai url liian pitkä. Maksimi pituus on 250 merkkiä')
    if len(genre) > 100:
        abort(
            400,
            description='Lajityypin nimi liian pitkä. Maksimi pituus on 100 merkkiä')
    if len(record_date) > 30:
        abort(400, description='Päivämäärä liian pitkä. Maksimi pituus on 30 merkkiä')
    if len(duration_sec) > 30:
        abort(400, description='Pituus liian pitkä. Maksimi pituus on 30 merkkiä')
    if len(license) > 30:
        abort(400, description='Lisenssi liian pitkä. Maksimi pituus on 100 merkkiä')
    if len(extra_meta_data) > 500:
        abort(400, description='Metadata liian pitkä. Maksimi pituus on 500 merkkiä')

    file = request.files['file']

    if file and help_functions.allowed_file(file.filename):
        filename = secure_filename(file.filename)
        new_filename = filename[:]
        target_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        counter = 1
        while os.path.exists(target_file_path):
            new_filename = str(counter) + "--" + filename
            target_file_path = os.path.join(
                app.config['UPLOAD_FOLDER'], new_filename)
            counter += 1

        file.save(target_file_path)
        source_path = new_filename

    if ':' in duration_sec:
        duration_sec = help_functions.convert_hms_to_seconds(duration_sec)

    transcription_id = transcriptions.add_transcription(
        title,
        source_path,
        source,
        genre,
        raw_content,
        user_id,
        license,
        record_date,
        duration_sec,
        extra_meta_data, allow_collaboration)
    return redirect("/transcription/" + str(transcription_id))


@app.route("/transcription/<int:transcription_id>")
@app.route("/transcription/<int:transcription_id>/<int(signed=True):page>")
def show_transcription(transcription_id, page=1):
    """Display a transcription with its text fragments paginated.

    Args:
        transcription_id: The ID of the transcription to display.
        page: The page number of text fragments (default: 1).

    Returns:
        Rendered template with transcription details and text fragments.

    Raises:
        404: If transcription is not found.
    """
    require_login()
    page_size = 20
    audiotime = request.args.get('audiotime')
    text_fragments_count = transcriptions.get_text_fragments_count(
        transcription_id)
    # text_fragments_count = len(text_fragments)
    text_fragments_count = text_fragments_count["count"]
    page_count = math.ceil(text_fragments_count / page_size)
    page_count = max(page_count, 1)
    print(page_count, text_fragments_count)
    if page < 1:
        return redirect("/transcription/" + str(transcription_id) + "/1")
    if page > page_count:
        return redirect(
            "/transcription/" +
            str(transcription_id) +
            "/" +
            str(page_count))

    text_fragments = transcriptions.get_text_fragments_paginated(
        transcription_id, page, page_size)
    text_fragments_with_secs = [(id,
                                 int(start_ms / 1000),
                                 help_functions.convert_seconds_to_hms(int(start_ms / 1000)),
                                 start_ms,
                                 words, version) for id,
                                start_ms,
                                words,  version in text_fragments]
    transcription = transcriptions.get_transcription(transcription_id)
    if not transcription:
        abort(404)

    user = None
    if transcription['user_id']:
        user_id = transcription['user_id']
        user = users.get_user(user_id)
    source_path = transcription['source_path']
    local_audio_file_copy_exists = False
    audio_file_path = None
    if source_path:
        source_path_file_name = os.path.basename(source_path)
        local_audio_file_copy = os.path.join(
            'static/audio', source_path_file_name)
        local_audio_file_copy_exists = os.path.exists(local_audio_file_copy)
        audio_file_path = f"audio/{source_path_file_name}"
        if not local_audio_file_copy_exists:
            # filenames from the whole source_path string
            source_path_fallback = source_path.replace("\\", '--')
            local_audio_file_copy = os.path.join(
                'static/audio', source_path_fallback)
            local_audio_file_copy_exists = os.path.exists(
                local_audio_file_copy)
            audio_file_path = f"audio/{source_path_fallback}"

    return render_template(
        "transcription.html",
        transcription=transcription,
        text_fragments=text_fragments_with_secs,
        convert_seconds_to_hms=help_functions.convert_seconds_to_hms,
        page=page,
        page_count=page_count,
        local_audio_file_copy_exists=local_audio_file_copy_exists,
        audio_file_path=audio_file_path,
        audiotime=audiotime,
        user=user)


@app.route("/add_text_fragment/<int:transcription_id>",
           methods=["GET", "POST"])
def add_text_fragment(transcription_id):
    """Add a new text fragment to a transcription.

    GET: Display form to add text fragment.
    POST: Process form and create new text fragment.

    Args:
        transcription_id: The ID of the transcription.

    Returns:
        GET: Rendered form template.
        POST: Redirect to transcription page.

    Raises:
        400: If duplicate text fragment is detected.
    """
    require_login()
    return_page = request.args.get("return_page")
    start_id = request.args.get("start_id")
    
    start_fragment=transcriptions.get_text_fragment(start_id)
    print(start_fragment['start_ms'] if start_fragment else "no start fragment")
    if start_fragment:
        # fetch default start time from the selected fragment with +1 second offset
        start_time_seconds = int(start_fragment['start_ms'] / 1000) + 1
        start_time_hms = help_functions.convert_seconds_to_hms(start_time_seconds)
    if request.method == "GET":
        return render_template(
            "add_text_fragment.html",
            transcription_id=transcription_id,
            return_page=return_page, start_time_hms=start_time_hms if start_fragment else "")
    if request.method == "POST":
        check_csrf()
        return_page = request.form["return_page"]
        start_time = request.form["start_time"]
        start_ms = help_functions.convert_hms_to_seconds(start_time) * 1000

        words = request.form["words"]
        try:
            transcriptions.add_text_fragment(start_ms, words, transcription_id)
        except sqlite3.IntegrityError:
            abort(400)
        page = '/' + str(return_page) if return_page else ''
        # id_anchor = '#t-id-' + str(text_fragment_id)
        return redirect(
            "/transcription/" +
            str(transcription_id) +
            page)  # + id_anchor)
    return redirect("/transcription/" + str(transcription_id))


@app.route("/text_fragments/<int:transcription_id>")
def generate_text_fragments(transcription_id):
    """Generate text fragments from raw transcription content.

    Processes the raw content based on source type (YouTube, Word, WebVTT)
    and splits it into timestamped text fragments.

    Args:
        transcription_id: The ID of the transcription.

    Returns:
        Rendered transcription page with generated fragments or redirect.

    Raises:
        400: If duplicate fragments are detected.
        404: If transcription is not found.
    """
    require_login()
    text_fragments = transcriptions.get_text_fragments(transcription_id)
    text_fragments_with_secs = [(id,
                                 int(start_ms / 1000),
                                 start_ms,
                                 words) for id,
                                start_ms,
                                words in text_fragments]
    transcription = transcriptions.get_transcription(transcription_id)
    if not transcription:
        abort(404)

    if len(text_fragments) > 0:
        return render_template(
            "transcription.html",
            transcription=transcription,
            text_fragments=text_fragments_with_secs)

    raw_content = transcription['raw_content']
    if len(raw_content.strip()) == 0:
        try:
            transcriptions.add_text_fragment(0, 'Placeholder', transcription_id)
        except sqlite3.IntegrityError:
            abort(400)
        return redirect("/transcription/" + str(transcription["id"]))
   
    test_fragments_with_timestamps = []
    try:
        if transcription['source'] == 'youtube':
            test_fragments_with_timestamps = text_splitter_help_functions.split_youtube_transcription(
                raw_content)
        elif transcription['source'] == 'word':
            test_fragments_with_timestamps = text_splitter_help_functions.split_word_transcription(
                raw_content)
        elif transcription['source'] == 'webvtt':
            test_fragments_with_timestamps = text_splitter_help_functions.split_web_vtt(
                raw_content)
        else:
            print(transcription['source'], " text source not supported")
    except Exception:    
        flash('Tekstinjako epäonnistui. Tarkista että aikaleimattu lähdeteksti on eheä ja valitun ' + transcription['source'] + ' lähteen formaation mukainen ') 
        return redirect("/transcription/" + str(transcription["id"]))
    transcription_id = transcription['id']
    try:
        for start_ms, words in test_fragments_with_timestamps:
            transcriptions.add_text_fragment(start_ms, words, transcription_id)
    except sqlite3.IntegrityError:
        abort(400)
    return redirect("/transcription/" + str(transcription["id"]))


@app.route("/search")
def search():
    """Search for text within transcription content.

    Returns:
        Rendered search page with results.
    """
    require_login()
    text_query = request.args.get("query")
    if not text_query:
        text_query = ""
    results = transcriptions.search(text_query) if text_query else []
    return render_template(
        "search.html",
        text_query=text_query,
        results=results)


@app.route("/search_titles")
def search_titles():
    """Search for transcriptions by title.

    Returns:
        Rendered search page with title search results.
    """
    require_login()
    title_query = request.args.get("query")
    if not title_query:
        title_query = ""
    results = transcriptions.search_titles(title_query) if title_query else []
    return render_template(
        "search.html",
        title_query=title_query,
        title_search_results=results)


@app.route("/search_file_name")
def search_file_name():
    """Search for transcriptions by file name.

    Returns:
        Rendered search page with file name search results.
    """
    require_login()
    file_name_query = request.args.get("query")
    if not file_name_query:
        file_name_query = ""
    results = transcriptions.search_file_name(
        file_name_query) if file_name_query else []
    return render_template(
        "search.html",
        file_name_query=file_name_query,
        title_search_results=results)


@app.route("/show_search_result_context/<int:id>")
def show_search_result_context(id):
    """Display a text fragment with surrounding context from search results.

    Args:
        id: The ID of the text fragment.

    Returns:
        Rendered template with text fragment and context.
    """
    require_login()
    text_context = transcriptions.get_text_fragment_context(id)
    title = ""
    transcription_id = None
    if len(text_context) > 0:
        title = text_context[0]['title']
        transcription_id = text_context[0]['transcription_id']

    return render_template(
        "show_search_result_context.html",
        text_context=text_context,
        title=title,
        transcription_id=transcription_id,
        id=id)


@app.route("/edit_text_fragment/<int:text_fragment_id>",
           methods=["GET", "POST"])
def edit_text_fragment(text_fragment_id):
    """Edit an existing text fragment.

    GET: Display edit form.
    POST: Process form and update text fragment.

    Args:
        text_fragment_id: The ID of the text fragment to edit.

    Returns:
        GET: Rendered edit form.
        POST: Redirect to transcription page.

    Raises:
        404: If text fragment is not found.
    """
    require_login()
    return_page = request.args.get("return_page")
    text_fragment = transcriptions.get_text_fragment(text_fragment_id)
    version=None
    if 'version' in text_fragment:
        version =  text_fragment['version']

    if not text_fragment:
        abort(404)

    transcription_id = text_fragment['transcription_id']
    transcription = transcriptions.get_transcription(transcription_id)
    allow_collaboration = transcription['allow_collaboration']  
    if not allow_collaboration and transcription["user_id"] != session["user_id"]:
        abort(403)


    if request.method == "GET":
        return render_template(
            "edit_text_fragment.html",
            text_fragment=text_fragment,
            return_page=return_page)

    id_anchor = ''
    page = ''
    if request.method == "POST":
        check_csrf()
        return_page = request.form["return_page"]
        words = request.form["words"]
        start_ms = text_fragment["start_ms"]
        if version:
            version = version + 1
        else:
            version = 1
        text_fragment_id = text_fragment["id"]
        print(words)

        transcriptions.add_versioned_text_fragment(text_fragment_id, start_ms, version, words, session["user_id"])
        page = '/' + str(return_page) if return_page else ''
        id_anchor = '#t-id-' + str(text_fragment_id)


    return redirect("/transcription/" +
                   str(text_fragment["transcription_id"]) +
                   page +
                   id_anchor)


@app.route("/remove_text_fragment/<int:text_fragment_id>",
           methods=["GET", "POST"])
def remove_text_fragment(text_fragment_id):
    """Remove a text fragment from a transcription.

    GET: Display confirmation form.
    POST: Delete text fragment if confirmed.

    Args:
        text_fragment_id: The ID of the text fragment to remove.

    Returns:
        GET: Rendered confirmation template.
        POST: Redirect to transcription page.

    Raises:
        404: If text fragment is not found.
    """
    require_login()
    return_page = request.args.get("return_page")
    text_fragment = transcriptions.get_text_fragment(text_fragment_id)
    if not text_fragment:
        abort(404)

    
    transcription_id = text_fragment['transcription_id']
    transcription = transcriptions.get_transcription(transcription_id)
    allow_collaboration = transcription['allow_collaboration']  
    if not allow_collaboration and transcription["user_id"] != session["user_id"]:
        abort(403)

    transcription_id = text_fragment["transcription_id"]
    if request.method == "GET":
        return render_template(
            "remove_text.html",
            text_fragment=text_fragment,
            return_page=return_page)

    page = ''
    id_anchor = ''
    if request.method == "POST":
        return_page = request.form["return_page"]
        page = '/' + str(return_page) if return_page else ''
        id_anchor = ''
        if "continue" in request.form:
            transcriptions.remove_text_fragment(text_fragment["id"])
        else:
            id_anchor = '#t-id-' + str(text_fragment_id)
    return redirect(
        "/transcription/" +
        str(transcription_id) +
        page +
        id_anchor)


@app.route("/remove/<int:transcription_id>", methods=["GET", "POST"])
def remove_transcription(transcription_id):
    """Remove an entire transcription and its associated data.

    GET: Display confirmation form.
    POST: Delete transcription if confirmed.

    Args:
        transcription_id: The ID of the transcription to remove.

    Returns:
        GET: Rendered confirmation template.
        POST: Redirect to home page.

    Raises:
        403: If user doesn't own the transcription.
        404: If transcription is not found.
    """
    require_login()
    transcription = transcriptions.get_transcription(transcription_id)
    if not transcription:
        abort(404)

    # Only the owner can delete the transcription regardless of transcription collaboration setting
    if transcription["user_id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        return render_template("remove.html", transcription=transcription)

    if request.method == "POST":
        if "continue" in request.form:
            transcriptions.remove_transcription(transcription["id"])
    return redirect("/")


@app.route("/remove_transcription_split_text/<int:transcription_id>",
           methods=["GET", "POST"])
def remove_transcription_split_text(transcription_id):
    """Remove all split text fragments from a transcription.

    GET: Display confirmation form.
    POST: Delete all text fragments if confirmed.

    Args:
        transcription_id: The ID of the transcription.

    Returns:
        GET: Rendered confirmation template.
        POST: Redirect to transcription page.

    Raises:
        404: If transcription is not found.
    """
    require_login()
    transcription = transcriptions.get_transcription(transcription_id)

   
    allow_collaboration = transcription['allow_collaboration']  
    if not allow_collaboration and transcription["user_id"] != session["user_id"]:
        abort(403)

    if not transcription:
        abort(404)
    if request.method == "GET":
        return render_template(
            "remove_transcription_split_text.html",
            transcription=transcription)

    if request.method == "POST":
        if "continue" in request.form:
            transcriptions.remove_transcription_split_text(transcription["id"])
    return redirect("/transcription/" + str(transcription["id"]))


@app.route("/edit/<int:transcription_id>", methods=["GET", "POST"])
def edit_transcription(transcription_id):
    """Edit an existing transcription's metadata and content.

    GET: Display edit form with current transcription data.
    POST: Process form and update transcription.

    Args:
        transcription_id: The ID of the transcription to edit.

    Returns:
        GET: Rendered edit form.
        POST: Redirect to transcription page.
    """
    require_login()
    transcription = transcriptions.get_transcription(transcription_id)

    allow_collaboration = transcription["allow_collaboration"]
    if not allow_collaboration and transcription["user_id"] != session["user_id"]:
        abort(403)
 

    if request.method == "GET":
        return render_template("edit.html", transcription=transcription)

    if request.method == "POST":
        check_csrf()
        title = request.form["title"]
        source_path = request.form["source_path"]
        source = request.form["source"]
        genre = request.form["genre"]
        raw_content = request.form["raw_content"]
        license = request.form["license"]
        record_date = request.form["record_date"]
        duration_sec = request.form["duration_sec"]
        extra_meta_data = request.form["extra_meta_data"]
        if 'allow_collaboration' in request.form:
            allow_collaboration = True
        else:
            allow_collaboration = False
        if ':' in duration_sec:
            duration_sec = help_functions.convert_hms_to_seconds(duration_sec)

        # file = request.files['sound_file']
        file = request.files['file']

        if file and help_functions.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            new_filename = filename[:]
            target_file_path = os.path.join(
                app.config['UPLOAD_FOLDER'], filename)
            counter = 1
            while os.path.exists(target_file_path):
                new_filename = str(counter) + "--" + filename
                target_file_path = os.path.join(
                    app.config['UPLOAD_FOLDER'], new_filename)
                counter += 1

            file.save(target_file_path)
            source_path = new_filename

        transcriptions.update_transcription(
            transcription["id"],
            title,
            source_path,
            source,
            genre,
            license,
            raw_content,
            record_date,
            duration_sec,
            extra_meta_data, allow_collaboration)
    return redirect("/transcription/" + str(transcription["id"]))


@app.route("/stats")
def stats():
    """Display statistics about transcriptions in the system.

    Shows duplicate files, genre statistics, source statistics,
    and user statistics.

    Returns:
        Rendered statistics template.
    """
    require_login()
    duplicates = transcriptions.get_duplicate_files()
    genre_stats = transcriptions.get_genre_stats()
    source_stats = transcriptions.get_source_stats()
    user_stats = transcriptions.get_user_stats()
    return render_template(
        "statistics.html",
        duplicates=duplicates,
        genre_stats=genre_stats,
        source_stats=source_stats,
        user_stats=user_stats)



