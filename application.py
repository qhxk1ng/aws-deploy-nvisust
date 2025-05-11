import os
import datetime
import hashlib
from flask import Flask, session, url_for, redirect, render_template, request, abort, flash
from database import list_users, verify, delete_user_from_db, add_user, check_user_exists
from database import read_note_from_db, write_note_into_db, delete_note_from_db, match_user_id_with_note_id
from database import image_upload_record, list_images_for_user, match_user_id_with_image_uid, delete_image_from_db
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config.from_object('config')
app.config['DEBUG'] = True  # Enable debugging


@app.errorhandler(401)
def FUN_401(error):
    return render_template("page_401.html"), 401

@app.errorhandler(403)
def FUN_403(error):
    return render_template("page_403.html"), 403

@app.errorhandler(404)
def FUN_404(error):
    return render_template("page_404.html"), 404

@app.errorhandler(405)
def FUN_405(error):
    return render_template("page_405.html"), 405

@app.errorhandler(413)
def FUN_413(error):
    return render_template("page_413.html"), 413


@app.route("/")
def FUN_root():
    return render_template("index.html")

@app.route("/public/")
def FUN_public():
    return render_template("public_page.html")

@app.route("/private/")
def FUN_private():
    if "current_user" in session.keys():
        notes_list = read_note_from_db(session['current_user'])
        notes_table = zip([x[0] for x in notes_list],\
                          [x[1] for x in notes_list],\
                          [x[2] for x in notes_list],\
                          ["/delete_note/" + x[0] for x in notes_list])

        images_list = list_images_for_user(session['current_user'])
        images_table = zip([x[0] for x in images_list],\
                          [x[1] for x in images_list],\
                          [x[2] for x in images_list],\
                          ["/delete_image/" + x[0] for x in images_list])

        return render_template("private_page.html", notes=notes_table, images=images_table)
    else:
        return abort(401)

@app.route("/admin/")
def FUN_admin():
    if session.get("current_user", None) == "ADMIN":
        user_list = list_users()
        user_table = zip(range(1, len(user_list)+1),\
                        user_list,\
                        [x + y for x, y in zip(["/delete_user/"] * len(user_list), user_list)])
        return render_template("admin.html", users=user_table)
    else:
        return abort(401)

@app.route("/signup", methods=["GET", "POST"])
def FUN_signup():
    if request.method == "POST":
        # Get form data
        username = request.form.get("username").upper()
        password = request.form.get("password")
        email = request.form.get("email")

        # Check if username already exists
        if username in list_users():
            flash("Sorry, that username is already taken.", "danger")
            return render_template("signup.html")

        # Add the new user
        add_user(username, password, email)  # Ensure `add_user` also stores email in the database.
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("FUN_login"))

    return render_template("signup.html")

@app.route("/login", methods=["POST"])
def FUN_login():
    id_submitted = request.form.get("id", "").upper()
    password = request.form.get("pw", "")
    if (id_submitted in list_users()) and verify(id_submitted, password):
        session['current_user'] = id_submitted
        return redirect(url_for("FUN_root"))
    else:
        return "Login failed. Invalid credentials.", 401  # or re-render login template with error


@app.route("/logout/")
def FUN_logout():
    session.pop("current_user", None)
    return(redirect(url_for("FUN_root")))

# Rest of your code...

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
