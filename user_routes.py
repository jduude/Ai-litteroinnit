"""User profile routes for the application."""

import re
from flask import Blueprint, render_template, abort, session, redirect, flash, request
import users
import transcriptions
from werkzeug.security import secrets

user_bp = Blueprint('user_bp', __name__)


def require_login():
    """Ensure user is logged in before accessing protected routes.

    Raises:
        403: If user is not authenticated.
    """
    if "user_id" not in session:
        abort(403)



@user_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login.

    GET: Display login form.
    POST: Validate credentials and create session.

    Returns:
        GET: Rendered login form.
        POST: Redirect to home page on success, error message on failure.
    """
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user_id = users.check_login(username, password)
        if user_id:
            session["user_id"] = user_id
            session["csrf_token"] = secrets.token_hex(16)
            return redirect("/")

        flash("VIRHE: väärä tunnus tai salasana")
    return render_template("login.html")


@user_bp.route("/register", methods=["GET", "POST"])
def register():
    """Create a new user account.

    Returns:
        Rendered success template or error message.
    """
    if request.method == "GET":
        return render_template("register.html", filled={})

    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if len(username) < 3:
        flash("VIRHE: tunnuksen pituuden tulee olla vähintään 3 merkkiä")
        filled = {"username": username}
        return render_template("register.html", filled=filled)
    
    # Check for invalid characters in username
    if not re.match("^[A-Za-z0-9_]+$", username):
        flash("VIRHE: tunnus saa sisältää vain kirjaimia, numeroita ja alaviivoja")
        filled = {"username": username}
        return render_template("register.html", filled=filled)
   
    
    if password1 != password2:
        flash("VIRHE: salasanat eivät ole samat")
        filled = {"username": username}
        return render_template("register.html", filled=filled)

    # at least 8 characters, one uppercase, one lowercase, one digit
    if len(password1) < 8 or not re.search("[a-z]", password1   ) or not re.search("[A-Z]", password1) or not re.search("[0-9]", password1):
        flash("VIRHE: salasanan tulee olla vähintään 8 merkkiä pitkä ja sisältää ainakin yhden ison kirjaimen, yhden pienen kirjaimen ja yhden numeron")
        filled = {"username": username}
        return render_template("register.html", filled=filled)
           
    try:
        users.create_user(username, password1)
        flash("Tunnuksen luominen onnistui, voit nyt kirjautua sisään")
        return redirect("/")
    except sqlite3.IntegrityError:
        flash("VIRHE: Valitsemasi tunnus on jo varattu")
        filled = {"username": username}
        return render_template("register.html", filled=filled)

 


@user_bp.route("/logout")
def logout():
    """Log out the current user by destroying their session.

    Returns:
        Redirect to home page.
    """
    require_login()

    del session["user_id"]
    return redirect("/")


@user_bp.route("/user/<int:user_id>")
def show_user(user_id):
    """Display a user's profile and their transcriptions.

    Args:
        user_id: The ID of the user to display.

    Returns:
        Rendered user profile template.

    Raises:
        404: If user is not found.
    """
    user = users.get_user(user_id)
    if not user:
        abort(404)
    transcriptions_array = transcriptions.get_transcriptions_of_user(user_id)
    return render_template(
        "user.html",
        user=user,
        transcriptions=transcriptions_array)
