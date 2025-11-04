import sqlite3
from flask import Flask,redirect,  render_template, request, session
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
    transcription_array =  transcriptions.get_transcriptions()
    return render_template("index.html", transcriptions=transcription_array)



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
    transcription = transcriptions.get_transcription(transcription_id)
    return render_template("transcription.html", transcription=transcription )


@app.route("/remove/<int:transcription_id>", methods=["GET", "POST"])
def remove_transcription(transcription_id):
    transcription = transcriptions.get_transcription(transcription_id)

    if request.method == "GET":
        return render_template("remove.html", transcription=transcription)

    if request.method == "POST":
        if "continue" in request.form:
            transcriptions.remove_transcription(transcription["id"])
        return redirect("/")




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
