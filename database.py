import MySQLdb
import hashlib
import datetime
import os

# Get MySQL credentials from environment variables (for Elastic Beanstalk)
MYSQL_HOST = os.environ.get('RDS_HOST')
MYSQL_USER = os.environ.get('RDS_USER')
MYSQL_PASSWORD = os.environ.get('RDS_PASSWORD')
MYSQL_DB = os.environ.get('RDS_DB_NAME')

# Establish a connection to the MySQL database
def connect_to_db():
    return MySQLdb.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        passwd=MYSQL_PASSWORD,
        db=MYSQL_DB
    )

# List all users from the database
def list_users():
    _conn = connect_to_db()
    _c = _conn.cursor()

    _c.execute("SELECT id FROM users;")
    result = [x[0] for x in _c.fetchall()]

    _conn.close()
    return result

# Verify user credentials
def verify(id, pw):
    _conn = connect_to_db()
    _c = _conn.cursor()

    _c.execute("SELECT pw FROM users WHERE id = %s;", (id,))
    result = _c.fetchone()
    
    if result:
        password_hash = result[0]
        is_verified = password_hash == hashlib.sha256(pw.encode()).hexdigest()
    else:
        is_verified = False

    _conn.close()
    return is_verified

# Delete a user from the database (and associated notes/images)
def delete_user_from_db(id):
    _conn = connect_to_db()
    _c = _conn.cursor()
    _c.execute("DELETE FROM users WHERE id = %s;", (id,))
    _conn.commit()
    _conn.close()

    # Delete the user's notes from the notes table
    _conn = connect_to_db()
    _c = _conn.cursor()
    _c.execute("DELETE FROM notes WHERE user = %s;", (id,))
    _conn.commit()
    _conn.close()

    # Delete the user's images from the images table
    _conn = connect_to_db()
    _c = _conn.cursor()
    _c.execute("DELETE FROM images WHERE owner = %s;", (id,))
    _conn.commit()
    _conn.close()

# Add a new user to the database
def add_user(id, pw):
    _conn = connect_to_db()
    _c = _conn.cursor()

    hashed_pw = hashlib.sha256(pw.encode()).hexdigest()
    _c.execute("INSERT INTO users (id, pw) VALUES (%s, %s)", (id.upper(), hashed_pw))
    
    _conn.commit()
    _conn.close()

# Read all notes for a specific user
def read_note_from_db(id):
    _conn = connect_to_db()
    _c = _conn.cursor()

    _c.execute("SELECT note_id, timestamp, note FROM notes WHERE user = %s;", (id.upper(),))
    result = _c.fetchall()

    _conn.close()
    return result

# Match user ID with note ID to confirm ownership
def match_user_id_with_note_id(note_id):
    _conn = connect_to_db()
    _c = _conn.cursor()

    _c.execute("SELECT user FROM notes WHERE note_id = %s;", (note_id,))
    result = _c.fetchone()[0]

    _conn.close()
    return result

# Write a new note into the database
def write_note_into_db(id, note_to_write):
    _conn = connect_to_db()
    _c = _conn.cursor()

    current_timestamp = str(datetime.datetime.now())
    note_id = hashlib.sha1((id.upper() + current_timestamp).encode()).hexdigest()
    _c.execute("INSERT INTO notes (note_id, timestamp, note, user) VALUES (%s, %s, %s, %s)", 
               (note_id, current_timestamp, note_to_write, id.upper()))

    _conn.commit()
    _conn.close()

# Delete a note from the database
def delete_note_from_db(note_id):
    _conn = connect_to_db()
    _c = _conn.cursor()

    _c.execute("DELETE FROM notes WHERE note_id = %s;", (note_id,))
    _conn.commit()
    _conn.close()

# Record an image upload in the database
def image_upload_record(uid, owner, image_name, timestamp):
    _conn = connect_to_db()
    _c = _conn.cursor()

    _c.execute("INSERT INTO images (uid, owner, name, timestamp) VALUES (%s, %s, %s, %s)", 
               (uid, owner, image_name, timestamp))

    _conn.commit()
    _conn.close()

# List all images for a specific user
def list_images_for_user(owner):
    _conn = connect_to_db()
    _c = _conn.cursor()

    _c.execute("SELECT uid, timestamp, name FROM images WHERE owner = %s;", (owner,))
    result = _c.fetchall()

    _conn.close()
    return result

# Match user ID with image UID to confirm ownership
def match_user_id_with_image_uid(image_uid):
    _conn = connect_to_db()
    _c = _conn.cursor()

    _c.execute("SELECT owner FROM images WHERE uid = %s;", (image_uid,))
    result = _c.fetchone()[0]

    _conn.close()
    return result

# Delete an image from the database
def delete_image_from_db(image_uid):
    _conn = connect_to_db()
    _c = _conn.cursor()

    _c.execute("DELETE FROM images WHERE uid = %s;", (image_uid,))
    _conn.commit()
    _conn.close()
