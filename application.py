import os
import datetime
import hashlib
from flask import Flask, session, url_for, redirect, render_template, request, abort, flash
from database import list_users, verify, delete_user_from_db, add_user
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
        notes_table = zip([x[0] for x in notes_list],
                          [x[1] for x in notes_list],
                          [x[2] for x in notes_list],
                          ["/delete_note/" + x[0] for x in notes_list])

        images_list = list_images_for_user(session['current_user'])
        images_table = zip([x[0] for x in images_list],
                           [x[1] for x in images_list],
                           [x[2] for x in images_list],
                           ["/delete_image/" + str(x[0]) for x in images_list])

        return render_template("private_page.html", notes=notes_table, images=images_table)
    else:
        return abort(401)

@app.route("/admin/")
def FUN_admin():
    if session.get("current_user", None) == "ADMIN":
        user_list = list_users()
        user_table = zip(range(1, len(user_list)+1),
                         user_list,
                         [x + y for x, y in zip(["/delete_user/"] * len(user_list), user_list)])
        return render_template("admin.html", users=user_table)
    else:
        return abort(401)

@app.route("/write_note", methods=["POST"])
def FUN_write_note():
    text_to_write = request.form.get("text_note_to_take")
    write_note_into_db(session['current_user'], text_to_write)
    return redirect(url_for("FUN_private"))

@app.route("/delete_note/<note_id>", methods=["GET"])
def FUN_delete_note(note_id):
    if session.get("current_user", None) == match_user_id_with_note_id(note_id):
        delete_note_from_db(note_id)
    else:
        return abort(401)
    return redirect(url_for("FUN_private"))

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload_image", methods=['POST'])
def FUN_upload_image():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', category='danger')
            return redirect(url_for("FUN_private"))
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', category='danger')
            return redirect(url_for("FUN_private"))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_time = str(datetime.datetime.now())
            image_uid = hashlib.sha1((upload_time + filename).encode()).hexdigest()
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_uid + "-" + filename))
            image_upload_record(image_uid, session['current_user'], filename, upload_time)
            return redirect(url_for("FUN_private"))
    return redirect(url_for("FUN_private"))

@app.route("/delete_image/<image_uid>", methods=["GET"])
def FUN_delete_image(image_uid):
    if session.get("current_user", None) == match_user_id_with_image_uid(image_uid):
        delete_image_from_db(image_uid)
        image_to_delete_from_pool = [y for y in os.listdir(app.config['UPLOAD_FOLDER']) if y.split("-", 1)[0] == image_uid][0]
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_to_delete_from_pool))
    else:
        return abort(401)
    return redirect(url_for("FUN_private"))

@app.route("/login", methods=["POST"])
def FUN_login():
    id_submitted = request.form.get("id", "").upper()
    password = request.form.get("password", "")
    if (id_submitted in list_users()) and verify(id_submitted, password):
        session['current_user'] = id_submitted
        return redirect(url_for("FUN_root"))
    else:
        return "Login failed. Invalid credentials.", 401

@app.route("/logout/")
def FUN_logout():
    session.pop("current_user", None)
    return redirect(url_for("FUN_root"))

@app.route("/delete_user/<id>/", methods=['GET'])
def FUN_delete_user(id):
    if session.get("current_user", None) == "ADMIN":
        if id == "ADMIN":
            return abort(403)
        images_to_remove = [str(x[0]) for x in list_images_for_user(id)]
        for f in images_to_remove:
            image_to_delete_from_pool = [y for y in os.listdir(app.config['UPLOAD_FOLDER']) if y.split("-", 1)[0] == f][0]
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_to_delete_from_pool))
        delete_user_from_db(id)
        return redirect(url_for("FUN_admin"))
    else:
        return abort(401)

@app.route("/add_user", methods=["POST"])
def FUN_add_user():
    if session.get("current_user", None) == "ADMIN":
        new_id = request.form.get('id').upper()
        if new_id in list_users():
            user_list = list_users()
            user_table = zip(range(1, len(user_list)+1),
                             user_list,
                             [x + y for x, y in zip(["/delete_user/"] * len(user_list), user_list)])
            return render_template("admin.html", id_to_add_is_duplicated=True, users=user_table)
        if " " in new_id or "'" in new_id:
            user_list = list_users()
            user_table = zip(range(1, len(user_list)+1),
                             user_list,
                             [x + y for x, y in zip(["/delete_user/"] * len(user_list), user_list)])
            return render_template("admin.html", id_to_add_is_invalid=True, users=user_table)
        else:
            add_user(new_id, request.form.get('password'))
            return redirect(url_for("FUN_admin"))
    else:
        return abort(401)

@app.route("/signup", methods=["GET", "POST"])
def FUN_signup():
    if request.method == "GET":
        return render_template("signup.html")
    elif request.method == "POST":
        user_id = request.form.get("id", "").upper()
        password = request.form.get("password", "")
        if not user_id or not password:
            flash("Username and password are required.", "danger")
            return render_template("signup.html")
        if user_id in list_users():
            flash("Username already exists. Please choose a different one.", "warning")
            return render_template("signup.html")
        if " " in user_id or "'" in user_id:
            flash("Username cannot contain spaces or quotes.", "danger")
            return render_template("signup.html")
        add_user(user_id, password)
        flash("Sign-up successful. Please log in.", "success")
        return redirect(url_for("FUN_root"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
