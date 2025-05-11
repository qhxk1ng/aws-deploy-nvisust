import MySQLdb
from MySQLdb import cursors
from mysql.connector import pooling
import os
import time
import signal
import hashlib
import datetime
from contextlib import contextmanager
from flask import current_app as app

# Database configuration
def connect_to_db():
    return MySQLdb.connect(
        host=os.environ.get('RDS_HOST'),
        user=os.environ.get('RDS_USER'),
        passwd=os.environ.get('RDS_PASSWORD'),
        db=os.environ.get('RDS_DB_NAME'),
        connect_timeout=5,  # Add connection timeout
        read_timeout=10,     # Add read timeout
        write_timeout=10     # Add write timeout
    )
# Create connection pool
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="flask_pool",
        pool_size=5,
        pool_reset_session=True,
        **dbconfig
    )
except Exception as e:
    app.logger.error(f"Failed to create connection pool: {str(e)}")
    raise

class DatabaseTimeout(Exception):
    pass

def timeout_handler(signum, frame):
    raise DatabaseTimeout("Database operation timed out")

@contextmanager
def db_cursor(timeout=5):
    conn = None
    try:
        conn = connection_pool.get_connection()
        cursor = conn.cursor(cursors.DictCursor)
        
        # Set timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        yield cursor
        
        signal.alarm(0)  # Disable timeout
    except MySQLdb.Error as e:
        app.logger.error(f"Database error: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def list_users():
    with db_cursor() as cursor:
        cursor.execute("SELECT id FROM users;")
        return [x['id'] for x in cursor.fetchall()]

def verify(id, pw):
    with db_cursor() as cursor:
        cursor.execute("SELECT pw FROM users WHERE id = %s;", (id.upper(),))
        result = cursor.fetchone()
        return result and result['pw'] == hashlib.sha256(pw.encode()).hexdigest()

# [Add all your other functions here following the same pattern]
# [Keep all your existing functions but rewrite them using the db_cursor context manager]