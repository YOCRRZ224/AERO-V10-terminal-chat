# main.py
import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, send_from_directory, abort
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import requests, re
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import yt_dlp
import logging
import time
import json
logging.getLogger('eventlet.wsgi.server').setLevel(logging.ERROR)
# --- Config ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'users.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
AVATAR_FOLDER = os.path.join(UPLOAD_FOLDER, 'avatars')
ALLOWED_AVATAR_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_FILE_EXT = None  # allow any with secure_filename
STICKER_FOLDER = os.path.join(UPLOAD_FOLDER, 'stickers')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AVATAR_FOLDER, exist_ok=True)
os.makedirs(STICKER_FOLDER, exist_ok=True)
# --- App init ---
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'aero-v10-super-secret'  # change this in production
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# --- In-memory stores (chat & music) ---
CHAT_HISTORY = []   # list of {user,msg,time,color,is_html}
MUSIC_QUEUE = []
NOW_PLAYING = None

# --- Database helpers ---
def dict_from_row(row):
    return dict(row) if row else {}
def db_connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db_connect()
    c = conn.cursor()

    # --- users table (now includes 'links') ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        display TEXT,
        color TEXT DEFAULT '#00ffaa',
        bio TEXT DEFAULT '',
        profile_pic TEXT DEFAULT '',
        links TEXT DEFAULT '[]',
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # --- notes table (user-owned) ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT,
        body TEXT,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    # --- work table (user-owned) ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS work (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT,
        status TEXT DEFAULT 'pending',
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    # --- chat history table ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        display TEXT,
        color TEXT,
        msg TEXT,
        is_html INTEGER DEFAULT 0,
        time TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # --- DM system tables ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS dm_connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1_id INTEGER,
        user2_id INTEGER,
        UNIQUE(user1_id, user2_id)
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS dm_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        msg TEXT,
        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # --- uploads metadata (file uploads) ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    # ✅ Ensure `links` column exists (for backward compatibility)
    try:
        c.execute("ALTER TABLE users ADD COLUMN links TEXT DEFAULT '[]'")
    except:
        pass  # column already exists

    conn.commit()
    conn.close()

# ---------------------- DM System Helpers ----------------------

def ensure_dm_connection(uid1, uid2):
    """Ensure a DM connection row exists between two user IDs."""
    conn = db_connect()
    c = conn.cursor()
    a, b = sorted((uid1, uid2))
    c.execute(
        'INSERT OR IGNORE INTO dm_connections (user1_id, user2_id) VALUES (?, ?)',
        (a, b)
    )
    conn.commit()
    conn.close()

# ---------------------- DM System Helpers ----------------------

def ensure_dm_connection(uid1, uid2):
    """Ensure a DM connection row exists between two user IDs."""
    conn = db_connect()
    c = conn.cursor()
    a, b = sorted((uid1, uid2))
    c.execute('INSERT OR IGNORE INTO dm_connections (user1_id, user2_id) VALUES (?, ?)', (a, b))
    conn.commit()
    conn.close()


def get_dm_connections(uid):
    """Return a list of users this user has DM connections with."""
    conn = db_connect()
    c = conn.cursor()
    c.execute('''
        SELECT u.username, u.display, u.color, u.profile_pic
        FROM users u
        WHERE u.id IN (
            SELECT CASE WHEN user1_id = ? THEN user2_id ELSE user1_id END
            FROM dm_connections
            WHERE user1_id = ? OR user2_id = ?
        )
    ''', (uid, uid, uid))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def save_dm_message(sender_id, receiver_id, msg):
    """Save a direct message between two users."""
    conn = db_connect()
    c = conn.cursor()
    c.execute('INSERT INTO dm_messages (sender_id, receiver_id, msg) VALUES (?, ?, ?)',
              (sender_id, receiver_id, msg))
    conn.commit()
    conn.close()


def get_dm_history(uid1, uid2, limit=50):
    """Get chat history between two users."""
    conn = db_connect()
    c = conn.cursor()
    c.execute('''
        SELECT sender_id, receiver_id, msg, time
        FROM dm_messages
        WHERE (sender_id = ? AND receiver_id = ?)
           OR (sender_id = ? AND receiver_id = ?)
        ORDER BY id ASC LIMIT ?
    ''', (uid1, uid2, uid2, uid1, limit))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_user_by_username(username):
    conn = db_connect()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id):
    conn = db_connect()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(username, password, color='#00ffaa', display=None, bio='', profile_pic=''):
    pw_hash = generate_password_hash(password)
    conn = db_connect()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password, display, color, bio, profile_pic) VALUES (?, ?, ?, ?, ?, ?)',
                  (username, pw_hash, display or username, color, bio, profile_pic))
        conn.commit()
        uid = c.lastrowid
        return uid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def verify_user(username, password):
    u = get_user_by_username(username)
    if not u:
        return False
    return check_password_hash(u['password'], password)

def update_profile(user_id, display=None, color=None, bio=None, links=None, profile_pic=None):
    conn = db_connect()
    c = conn.cursor()

    # Build update statement dynamically
    updates, values = [], []

    if display is not None:
        updates.append("display=?")
        values.append(display)
    if color is not None:
        updates.append("color=?")
        values.append(color)
    if bio is not None:
        updates.append("bio=?")
        values.append(bio)
    if links is not None:
        updates.append("links=?")
        values.append(links)
    if profile_pic is not None:
        updates.append("profile_pic=?")
        values.append(profile_pic)

    if not updates:
        conn.close()
        return None

    values.append(user_id)
    c.execute(f"UPDATE users SET {', '.join(updates)} WHERE id=?", values)
    conn.commit()

    # Fetch updated record
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = dict_from_row(c.fetchone())
    conn.close()
    return user

def delete_user_and_data(user_id):
    # Remove avatar & uploaded files from disk, then remove DB rows
    user = get_user_by_id(user_id)
    if not user:
        return False
    conn = db_connect()
    c = conn.cursor()
    # delete uploads files from disk
    c.execute('SELECT filename FROM uploads WHERE user_id = ?', (user_id,))
    rows = c.fetchall()
    for r in rows:
        fn = r['filename']
        path = os.path.join(app.config['UPLOAD_FOLDER'], fn)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
    # delete avatar file if exists
    if user.get('profile_pic'):
        apath = os.path.join(AVATAR_FOLDER, user['profile_pic'])
        try:
            if os.path.exists(apath):
                os.remove(apath)
        except Exception:
            pass
    # delete rows
    c.execute('DELETE FROM notes WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM work WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM uploads WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return True


# ✅ now new helper begins at the left margin
def save_chat_message(username, display, color, msg, is_html=False):
    conn = db_connect()
    c = conn.cursor()
    c.execute('INSERT INTO chat_history (username, display, color, msg, is_html) VALUES (?, ?, ?, ?, ?)',
              (username, display, color, msg, 1 if is_html else 0))
    conn.commit()
    conn.close()


def load_recent_chats(limit=30):
    conn = db_connect()
    c = conn.cursor()
    c.execute(
        'SELECT username, display, color, msg, is_html, time FROM chat_history ORDER BY id DESC LIMIT ?',
        (limit,))
    rows = [dict(r) for r in c.fetchall()][::-1]
    conn.close()
    return rows

# initialize DB
init_db()

CHAT_HISTORY = load_recent_chats(30)

def update_profile(user_id, display=None, color=None, bio=None, links=None, profile_pic=None):
    conn = db_connect()
    c = conn.cursor()

    updates, values = [], []

    if display is not None:
        updates.append("display=?")
        values.append(display)
    if color is not None:
        updates.append("color=?")
        values.append(color)
    if bio is not None:
        updates.append("bio=?")
        values.append(bio)
    if links is not None:
        updates.append("links=?")
        values.append(links)
    if profile_pic is not None:
        updates.append("profile_pic=?")
        values.append(profile_pic)

    if not updates:
        conn.close()
        return None

    values.append(user_id)
    c.execute(f"UPDATE users SET {', '.join(updates)} WHERE id=?", values)
    conn.commit()

    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = dict_from_row(c.fetchone())
    conn.close()
    return user

    # fetch updated row
    u = c.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    conn.close()
    return dict(u) if u else None
# --- yt-dlp helper ---
def fetch_track(query_or_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'skip_download': True,
        'default_search': 'ytsearch1',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query_or_url, download=False)
            if not info:
                return None
            if 'entries' in info:
                info = info['entries'][0]
            audio_url = None
            formats = info.get('formats') or []
            for f in formats[::-1]:
                if f.get('acodec') and f.get('acodec') != 'none' and f.get('url'):
                    audio_url = f.get('url')
                    break
            if not audio_url:
                audio_url = info.get('url')
            return {
                'title': info.get('title'),
                'url': audio_url,
                'webpage_url': info.get('webpage_url'),
                'duration': info.get('duration')
            }
    except Exception as e:
        print("yt-dlp error:", e)
        return None

# --- Routes: register/login/logout ---
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        color = request.form.get('color') or '#00ffaa'
        bio = request.form.get('bio') or ''
        if not username or not password:
            return "username and password required", 400
        uid = create_user(username, password, color=color, display=username, bio=bio)
        if not uid:
            return "username already exists", 400
        return redirect(url_for('login'))
    return """
    <!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
 <link
      rel="stylesheet"
      type="text/css"
      href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/regular/style.css"
    />
    <link
      rel="stylesheet"
      type="text/css"
      href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/fill/style.css"
    />
<title>Auth Form</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@400;600&display=swap');

  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: "Source Code Pro", monospace;
  }

  body {
    min-height: 100vh;
    background: radial-gradient(circle at top, #001010, #000);
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
  }

  .glow-ring {
    position: absolute;
    width: 500px;
    height: 500px;
    border-radius: 50%;
    background: conic-gradient(#00ffaa55, transparent, #00ffaa55);
    filter: blur(80px);
    animation: rotate 10s linear infinite;
  }

  @keyframes rotate {
    0% { transform: rotate(0deg);}
    100% { transform: rotate(360deg);}
  }

  .auth-container {
    position: relative;
    z-index: 2;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    backdrop-filter: blur(15px);
    padding: 30px;
    width: 90%;
    max-width: 380px;
    box-shadow: 0 0 30px rgba(0,255,170,0.15);
    animation: fadeIn 1s ease;
  }

  @keyframes fadeIn {
    from {opacity:0; transform: translateY(15px);}
    to {opacity:1; transform: translateY(0);}
  }

  h2 {
    color: #00ffaa;
    text-align: center;
    margin-bottom: 20px;
  }

  input, textarea {
    width: 100%;
    background: rgba(0,0,0,0.4);
    border: 1px solid rgba(255,255,255,0.1);
    color: #00ffaa;
    padding: 10px;
    margin: 8px 0;
    border-radius: 8px;
    outline: none;
    transition: border-color 0.3s;
  }

  input:focus, textarea:focus {
    border-color: #00ffaa;
  }

  button {
    width: 100%;
    background: linear-gradient(90deg, #00ffaa, #00997f);
    border: none;
    color: #000;
    font-weight: bold;
    padding: 10px;
    border-radius: 8px;
    margin-top: 10px;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
  }

  button:hover {
    transform: translateY(-2px);
    box-shadow: 0 0 20px #00ffaa77;
  }

  p {
    text-align: center;
    margin-top: 15px;
    color: #aaa;
  }

  a {
    color: #00ffaa;
    text-decoration: none;
  }

  .password-container {
    position: relative;
  }

  .toggle-pass {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    color: #00ffaaaa;
    cursor: pointer;
    user-select: none;
    transition: color 0.3s;
  }

  .toggle-pass:hover {
    color: #00ffaa;
  }

  .strength {
    height: 5px;
    width: 100%;
    border-radius: 5px;
    margin-top: 5px;
    background: rgba(255,255,255,0.1);
    overflow: hidden;
  }

  .strength-bar {
    height: 100%;
    width: 0%;
    background: red;
    transition: width 0.4s, background 0.4s;
  }

  @media (max-width: 480px) {
    .auth-container {
      padding: 20px;
      border-radius: 15px;
    }
    h2 { font-size: 1.5em; }
  }
</style>
</head>
<body>
  <div class="glow-ring"></div>
  <form method="POST" class="auth-container">
    <h2>Create Account</h2>
    <input type="text" name="username" placeholder="Username" required>

    <div class="password-container">
      <input type="password" id="password" name="password" placeholder="Password" required>
      <i id="toggleIcon" class="ph ph-eye-closed" 
     style="position:absolute; right:12px; top:50%; transform:translateY(-50%);
            cursor:pointer; font-size:1.2rem; color:#aaa;"
     onclick="togglePassword()"></i>
    </div>

    <div class="strength"><div class="strength-bar" id="strengthBar"></div></div>

    <label style="display:block;text-align:left;margin-top:10px;color:#aaa;">Pick Color</label>
    <input type="color" name="color" value="#00ffaa">

    <textarea name="bio" placeholder="Short bio (optional)" rows="3"></textarea>
    <button type="submit">Register</button>
    <p>Already have an account? <a href="/login">Login</a></p>
  </form>

  <script>
  const password = document.getElementById("password");
  const strengthBar = document.getElementById("strengthBar");
  const form = document.querySelector("form");
  const toggleIcon = document.getElementById("toggleIcon");

  // ✅ Password input strength detection
  password.addEventListener("input", () => {
    const val = password.value;
    let strength = 0;

    // check for digits
    const digits = (val.match(/\d/g) || []).length;
    if (digits >= 2) strength += 1;

    // check for length
    if (val.length >= 6 && val.length < 10) strength += 1;
    if (val.length >= 10) strength += 2;

    // update bar
    const width = (strength / 3) * 100;
    strengthBar.style.width = width + "%";
    strengthBar.style.transition = "width 0.3s ease";

    // color change
    if (strength === 0) strengthBar.style.background = "#ff3b30"; // weak
    else if (strength === 1) strengthBar.style.background = "orange"; // medium
    else if (strength === 2) strengthBar.style.background = "#ffd700"; // good
    else strengthBar.style.background = "#00ffaa"; // strong
  });

  // ✅ Toggle visibility and icon
  function togglePassword() {
    if (password.type === "password") {
      password.type = "text";
      toggleIcon.className = "ph ph-eye"; // 👁 visible
    } else {
      password.type = "password";
      toggleIcon.className = "ph ph-eye-closed"; // 🙈 hidden
    }
  }

  // ✅ Prevent weak passwords
  form.addEventListener("submit", (e) => {
    const val = password.value;
    const digits = (val.match(/\d/g) || []).length;

    if (val.length < 6 || digits < 2) {
      e.preventDefault();
      alert("Password must be at least 6 characters long and include at least 2 numbers.");
    }
  });
</script>
</body>
</html>
    """  # keep simplified; same as previous version (you can keep the full HTML from earlier)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        if not username or not password:
            return "username & password required", 400
        if not verify_user(username, password):
            return "invalid credentials", 401
        u = get_user_by_username(username)
        session['username'] = u['username']
        session['user_id'] = u['id']
        session['color'] = u.get('color') or '#00ffaa'
        session['display'] = u.get('display') or u['username']
        return redirect(url_for('index'))
    return """
    <!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
 <link
      rel="stylesheet"
      type="text/css"
      href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/regular/style.css"
    />
    <link
      rel="stylesheet"
      type="text/css"
      href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/fill/style.css"
    />
<title>Login</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@400;600&display=swap');

  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: "Source Code Pro", monospace;
  }

  body {
    min-height: 100vh;
    background: radial-gradient(circle at top, #001010, #000);
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
  }

  .glow-ring {
    position: absolute;
    width: 550px;
    height: 550px;
    border-radius: 50%;
    background: conic-gradient(#00ffaa55, transparent, #00ffaa55);
    filter: blur(100px);
    animation: spin 12s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .auth-container {
    position: relative;
    z-index: 2;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 24px;
    backdrop-filter: blur(18px);
    padding: 45px 35px;
    width: 90%;
    max-width: 420px;
    min-height: 460px;
    box-shadow: 0 0 35px rgba(0,255,170,0.15);
    display: flex;
    flex-direction: column;
    justify-content: center;
    animation: fadeIn 1.2s ease;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
  }

  .auth-container:hover {
    transform: translateY(-5px);
    box-shadow: 0 0 40px rgba(0,255,170,0.3);
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  h2 {
    color: #00ffaa;
    text-align: center;
    margin-bottom: 30px;
    font-size: 1.8em;
    letter-spacing: 1px;
  }

  input {
    width: 100%;
    background: rgba(0,0,0,0.35);
    border: 1px solid rgba(255,255,255,0.08);
    color: #00ffaa;
    padding: 12px;
    margin: 10px 0;
    border-radius: 10px;
    outline: none;
    transition: border-color 0.3s, box-shadow 0.3s;
  }

  input:focus {
    border-color: #00ffaa;
    box-shadow: 0 0 10px #00ffaa55;
  }

  .password-container {
    position: relative;
  }

  .toggle-pass {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: #00ffaaaa;
    cursor: pointer;
    user-select: none;
    font-size: 1.1em;
    transition: color 0.3s;
  }

  .toggle-pass:hover {
    color: #00ffaa;
  }

  button {
    width: 100%;
    background: linear-gradient(90deg, #00ffaa, #00cc99);
    border: none;
    color: #000;
    font-weight: bold;
    padding: 12px;
    border-radius: 10px;
    margin-top: 25px;
    cursor: pointer;
    transition: transform 0.25s, box-shadow 0.25s;
  }

  button:hover {
    transform: translateY(-2px);
    box-shadow: 0 0 25px #00ffaa77;
  }

  p {
    text-align: center;
    margin-top: 25px;
    color: #aaa;
    font-size: 0.95em;
  }

  a {
    color: #00ffaa;
    text-decoration: none;
    transition: color 0.3s;
  }
  /* Animated red error box */
.error-box {
  text-align: center;
  color: #ff5555;
  font-size: 0.95em;
  margin-top: 15px;
  background: rgba(255, 50, 50, 0.1);
  border: 1px solid rgba(255, 50, 50, 0.2);
  padding: 10px;
  border-radius: 8px;
  display: none;
  animation: shake 0.4s ease;
}

@keyframes shake {
  10%, 90% { transform: translateX(-2px); }
  20%, 80% { transform: translateX(4px); }
  30%, 50%, 70% { transform: translateX(-8px); }
  40%, 60% { transform: translateX(8px); }
}

  a:hover {
    color: #00ffcc;
  }

  @media (max-width: 480px) {
    .auth-container {
      padding: 30px 20px;
      border-radius: 18px;
      min-height: 400px;
    }
    h2 { font-size: 1.5em; }
  }
</style>
</head>
<body>
  <div class="glow-ring"></div>
  <form method="POST" class="auth-container">
    <h2>Welcome Back</h2>
    <input type="text" name="username" placeholder="Username" required>

    <div class="password-container">
      <input type="password" id="password" name="password" placeholder="Password" required>
      <i id="toggleIcon" class="ph ph-eye-closed" 
     style="position:absolute; right:12px; top:50%; transform:translateY(-50%);
            cursor:pointer; font-size:1.2rem; color:#aaa;"
     onclick="togglePassword()"></i>
    </div>

    <button type="submit">Login</button>
    <div id="errorBox" class="error-box"></div>
    <p>Don’t have an account? <a href="/register">Register</a></p>
  </form>

  <script>
function togglePassword() {
  const pass = document.getElementById("password");
  const icon = document.getElementById("toggleIcon");

  if (pass.type === "password") {
    pass.type = "text";
    icon.className = "ph ph-eye"; // 👁 show password
  } else {
    pass.type = "password";
    icon.className = "ph ph-eye-closed"; // 🙈 hide password
  }
}

// Animated red error box for invalid login
const form = document.querySelector('form');
const err = document.createElement('div');
err.id = 'errorBox';
err.className = 'error-box';
form.appendChild(err);

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  err.style.display = 'none';

  const res = await fetch('/login', {
    method: 'POST',
    body: new FormData(form)
  });

  if (res.redirected) {
    window.location.href = res.url;
  } else {
    const text = await res.text();
    err.style.display = 'block';
    if (text.includes('invalid credentials')) {
      err.innerText = 'Invalid username or password ❌';
    } else if (text.includes('username & password required')) {
      err.innerText = 'Please enter both fields ⚠️';
    } else {
      err.innerText = 'Login failed. Try again.';
    }
  }
});
</script>
</body>
</html>
    """

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Whoami endpoint ---

@app.route('/_whoami', methods=['GET'])
def whoami():
    if 'user_id' not in session:
        return jsonify({})
    u = get_user_by_id(session['user_id'])
    if not u:
        return jsonify({})
    profile_pic = ''
    if u.get('profile_pic'):
        profile_pic = url_for('avatar_file', filename=u['profile_pic'])
    return jsonify({
        'username': u['username'],
        'display': u['display'],
        'color': u['color'],
        'bio': u['bio'],
        'profile_pic': profile_pic,
        'created': u['created']
    })


# --- Main page ---
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template(
        'index.html',
        username=session['username'],
        color=session.get('color', '#00ffaa'),
        display=session.get('display', session.get('username', ''))
    )


# --- Profile update route (persisted) ---
@app.route('/profile', methods=['POST'])
def profile():
    if 'user_id' not in session:
        return jsonify({'error': 'not logged in'}), 401

    data = request.json or {}
    display = data.get('display')
    color = data.get('color')
    bio = data.get('bio')
    links = data.get('links', [])

    # 🔧 Accept both list and dict formats
    if isinstance(links, dict):
        links_json = json.dumps(links)
    elif isinstance(links, list):
        links_json = json.dumps(links)
    else:
        return jsonify({'error': 'invalid links format'}), 400

    u = update_profile(session['user_id'], display=display, color=color, bio=bio, links=links_json)
    if not u:
        return jsonify({'error': 'update failed'}), 500

    session['display'] = u.get('display')
    session['color'] = u.get('color')

    return jsonify({
        'ok': True,
        'display': u.get('display'),
        'color': u.get('color'),
        'bio': u.get('bio'),
        'links': json.loads(u.get('links') or '[]')
    })

# --- Profile picture upload ---
def allowed_avatar(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in ALLOWED_AVATAR_EXT

@app.route('/upload_profile_pic', methods=['POST'])
def upload_profile_pic():
    if 'user_id' not in session:
        return jsonify({'error': 'not logged in'}), 401
    if 'file' not in request.files:
        return jsonify({'error': 'no file'}), 400

    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': 'empty filename'}), 400

    fn = secure_filename(f.filename)
    if not allowed_avatar(fn):
        return jsonify({'error': 'bad ext'}), 400

    username = session['username']
    ext = fn.rsplit('.', 1)[-1]
    new_name = f"{username}_{int(datetime.utcnow().timestamp())}.{ext}"

    # ✅ Save inside uploads/avatars/
    save_path = os.path.join('uploads', 'avatars', new_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    f.save(save_path)

    # ✅ The web-accessible path (what the browser should see)
    web_path = f"/uploads/avatars/{new_name}"

    # ✅ Update the DB with web_path (not the internal path)
    u = update_profile(session['user_id'], profile_pic=web_path)

    # ✅ Sync session
    session['display'] = u.get('display')

    return jsonify({'ok': True, 'profile_pic': web_path})

@app.route('/avatars/<path:filename>')
def avatar_file(filename):
    return send_from_directory(AVATAR_FOLDER, filename)

# --- File uploads (general) ---
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return jsonify({'error': 'not logged in'}), 401
    if 'file' not in request.files:
        return jsonify({'error':'no file provided'}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error':'empty filename'}), 400
    safe_name = secure_filename(f.filename)
    # to avoid collisions: prefix with username + timestamp
    prefix = session['username'] + '_' + str(int(datetime.utcnow().timestamp()))
    final_name = f"{prefix}_{safe_name}"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], final_name)
    f.save(save_path)
    # store metadata
    conn = db_connect()
    c = conn.cursor()
    c.execute('INSERT INTO uploads (user_id, filename) VALUES (?, ?)', (session['user_id'], final_name))
    conn.commit()
    conn.close()
    # broadcast to chat (marked as HTML)
    file_url = url_for('uploaded_file', filename=final_name)
    payload = {
        'user': session.get('display', session.get('username')),
        'msg': f'Shared a file: <a href="{file_url}" download>{safe_name}</a>',
        'time': datetime.now().strftime('%H:%M'),
        'color': session.get('color', '#ffffff'),
        'is_html': True
    }
    CHAT_HISTORY.append(payload)
    socketio.emit('chat_message', payload, room='global')
    return jsonify({'ok': True, 'url': file_url, 'name': final_name})

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)

@app.route('/uploads', methods=['GET'])
def list_uploads():
    # returns list of filenames
    files = []
    for fn in os.listdir(app.config['UPLOAD_FOLDER']):
        # ignore avatars folder
        if fn == 'avatars': continue
        if fn.startswith('.'): continue
        files.append(fn)
    return jsonify(sorted(files))

# --- Notes endpoints (DB-backed) ---
@app.route('/notes', methods=['GET','POST','DELETE'])
def notes_api():
    if 'user_id' not in session:
        return jsonify({'error':'not logged in'}), 401
    uid = session['user_id']
    conn = db_connect()
    c = conn.cursor()
    if request.method == 'GET':
        c.execute('SELECT id, title, body, created FROM notes WHERE user_id = ? ORDER BY created DESC', (uid,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify(rows)
    if request.method == 'POST':
        payload = request.json or {}
        title = payload.get('title','')
        body = payload.get('body','')
        c.execute('INSERT INTO notes (user_id, title, body) VALUES (?, ?, ?)', (uid, title, body))
        conn.commit()
        nid = c.lastrowid
        conn.close()
        return jsonify({'id': nid, 'title': title, 'body': body, 'created': datetime.utcnow().isoformat()})
    if request.method == 'DELETE':
        payload = request.json or {}
        nid = payload.get('id')
        c.execute('DELETE FROM notes WHERE id = ? AND user_id = ?', (nid, uid))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})

# --- Work endpoints (DB-backed) ---
@app.route('/work', methods=['GET','POST','DELETE','PATCH'])
def work_api():
    if 'user_id' not in session:
        return jsonify({'error':'not logged in'}), 401
    uid = session['user_id']
    conn = db_connect()
    c = conn.cursor()
    if request.method == 'GET':
        c.execute('SELECT id, title, status, created FROM work WHERE user_id = ? ORDER BY created DESC', (uid,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify(rows)
    if request.method == 'POST':
        payload = request.json or {}
        title = payload.get('title','')
        c.execute('INSERT INTO work (user_id, title) VALUES (?, ?)', (uid, title))
        conn.commit()
        wid = c.lastrowid
        conn.close()
        return jsonify({'id': wid, 'title': title, 'status': 'pending', 'created': datetime.utcnow().isoformat()})
    if request.method == 'DELETE':
        payload = request.json or {}
        wid = payload.get('id')
        c.execute('DELETE FROM work WHERE id = ? AND user_id = ?', (wid, uid))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})
    if request.method == 'PATCH':
        payload = request.json or {}
        wid = payload.get('id')
        status = payload.get('status')
        c.execute('UPDATE work SET status = ? WHERE id = ? AND user_id = ?', (status, wid, uid))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})

# --- Search users (simple) ---
@app.route('/search_users')
def search_users():
    q = request.args.get('q', '').strip().lower()
    if not q:
        return jsonify([])

    conn = db_connect()
    c = conn.cursor()
    c.execute("""
        SELECT username, display, profile_pic
        FROM users
        WHERE LOWER(username) LIKE ? OR LOWER(display) LIKE ?
        LIMIT 20
    """, (f"%{q}%", f"%{q}%"))
    rows = [dict_from_row(r) for r in c.fetchall()]
    conn.close()

    results = []
    for u in rows:
        # ✅ normalize profile_pic path
        if u.get("profile_pic"):
            u["profile_pic"] = f"/uploads/avatars/{os.path.basename(u['profile_pic'])}"
        else:
            u["profile_pic"] = "/static/default.png"
        results.append(u)

    return jsonify(results)

# --- Public user profile (JSON) ---

@app.route('/user/<username>')
def public_profile(username):
    u = get_user_by_username(username)
    if not u:
        return jsonify({'error': 'not found'}), 404

    # ✅ Build correct avatar path
    if u.get('profile_pic'):
        u['profile_pic'] = f"/uploads/avatars/{os.path.basename(u['profile_pic'])}"
    else:
        u['profile_pic'] = "/static/default.png"

    # ✅ Parse links safely (default empty dict)
    try:
        links = json.loads(u.get('links') or '{}')
    except:
        links = {}

    return jsonify({
        'username': u['username'],
        'display': u['display'],
        'bio': u['bio'],
        'color': u['color'],
        'profile_pic': u['profile_pic'],
        'created': u['created'],
        'links': links
    })

# --- Delete account ---
@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return jsonify({'error': 'not logged in'}), 401
    uid = session['user_id']
    success = delete_user_and_data(uid)
    session.clear()
    if success:
        return jsonify({'ok': True})
    return jsonify({'error': 'failed'}), 500

# --- Music endpoints (unchanged) ---

@app.route('/music/play', methods=['POST'])
def music_play():
    global NOW_PLAYING
    if 'user_id' not in session:
        return jsonify({'error': 'not logged in'}), 401

    payload = request.json or {}
    query = payload.get('query')
    if not query:
        return jsonify({'error': 'no query'}), 400

    track = fetch_track(query)
    if not track:
        return jsonify({'error': 'could not fetch track'}), 500

    MUSIC_QUEUE.append({
        'id': int(datetime.now(timezone.utc).timestamp() * 1000),
        'title': track['title'],
        'url': track['url'],
        'webpage_url': track.get('webpage_url'),
        'requested_by': session.get('username')
    })

    # start playback if nothing currently playing
    if not NOW_PLAYING:
        _start_next_track()

    # emit to all clients (broadcast is implicit now)
    socketio.emit('queue_update', MUSIC_QUEUE, room='global')
    return jsonify({'ok': True, 'queued': MUSIC_QUEUE[-1]})


@app.route('/music/skip', methods=['POST'])
def music_skip():
    global NOW_PLAYING
    if MUSIC_QUEUE:
        # remove currently playing track
        if NOW_PLAYING and MUSIC_QUEUE[0].get('id') == NOW_PLAYING.get('id'):
            MUSIC_QUEUE.pop(0)
        _start_next_track()
        socketio.emit('queue_update', MUSIC_QUEUE, room='global')
        socketio.emit('now_playing', NOW_PLAYING, room='global')
        return jsonify({'ok': True, 'now_playing': NOW_PLAYING})
    else:
        NOW_PLAYING = None
        socketio.emit('now_playing', None, room='global')
        return jsonify({'ok': True, 'now_playing': None})


def _start_next_track():
    global NOW_PLAYING
    NOW_PLAYING = MUSIC_QUEUE[0] if MUSIC_QUEUE else None
    socketio.emit('now_playing', NOW_PLAYING, room='global')
@app.route('/dm/list')
def dm_list():
    # ✅ use correct session key
    if 'username' not in session:
        return jsonify([])

    conn = db_connect()
    c = conn.cursor()

    # ✅ use session['username'] consistently
    c.execute("""
        SELECT DISTINCT u.username, u.display, u.profile_pic
        FROM users u
        JOIN dm_messages m
          ON u.id = m.sender_id OR u.id = m.receiver_id
        WHERE (m.sender_id = (SELECT id FROM users WHERE username=?)
           OR  m.receiver_id = (SELECT id FROM users WHERE username=?))
          AND u.username != ?
        ORDER BY m.time DESC
    """, (session['username'], session['username'], session['username']))

    users = c.fetchall()
    conn.close()

    # ✅ fix avatar path logic
    user_list = []
    for u in users:
        avatar = u["profile_pic"]
        avatar_url = f"/avatars/{os.path.basename(avatar)}" if avatar else "/static/default.png"
        user_list.append({
            "username": u["username"],
            "display": u["display"] or u["username"],
            "avatar": avatar_url
        })

    return jsonify(user_list)


@app.route('/dm/history/<username>')
def dm_history(username):
    if 'user_id' not in session:
        return jsonify({'error': 'not logged in'}), 401

    other = get_user_by_username(username)
    if not other:
        return jsonify({'error': 'user not found'}), 404

    user_id = session['user_id']
    msgs = get_dm_history(user_id, other['id'])

    conn = db_connect()
    c = conn.cursor()

    for m in msgs:
        sender = c.execute(
            'SELECT username, display, profile_pic FROM users WHERE id=?',
            (m['sender_id'],)
        ).fetchone()

        if sender:
            sender_name = sender['display'] or sender['username']
            sender_pic = (sender['profile_pic'] or '').strip()

            # 🧩 Force exact rules for avatar vs default
            if not sender_pic or 'default.png' in sender_pic or 'static/' in sender_pic:
                sender_pic = "/static/default.png"
            else:
                # Clean and rebuild safe avatar path
                clean_name = sender_pic.replace('/avatars/', '')
                safe_name = os.path.basename(clean_name)
                avatar_path = os.path.join('avatars', safe_name)

                if os.path.exists(avatar_path):
                    sender_pic = f"/avatars/{safe_name}"
                else:
                    sender_pic = "/static/default.png"

            m['sender_name'] = sender_name
            m['sender_pic'] = sender_pic

        # ⏰ Timestamp fix
        if 'time' not in m:
            m['time'] = datetime.now().strftime("%H:%M")

    conn.close()
    return jsonify(msgs)

@app.route('/dm/send', methods=['POST'])
def dm_send():
    if 'user_id' not in session:
        return jsonify({'error': 'not logged in'}), 401

    data = request.get_json() or {}
    receiver_username = data.get('to')
    msg = (data.get('msg') or '').strip()
    if not receiver_username or not msg:
        return jsonify({'error': 'missing data'}), 400

    conn = db_connect()
    c = conn.cursor()
    receiver = c.execute('SELECT id FROM users WHERE username=?', (receiver_username,)).fetchone()
    if not receiver:
        conn.close()
        return jsonify({'error': 'user not found'}), 404

    # ✅ Insert message
    c.execute('''
        INSERT INTO dm_messages (sender_id, receiver_id, msg)
        VALUES (?, ?, ?)
    ''', (session['user_id'], receiver['id'], msg))

    # ✅ Ensure connection exists
    c.execute('''
        INSERT OR IGNORE INTO dm_connections (user1_id, user2_id)
        VALUES (?, ?)
    ''', (session['user_id'], receiver['id']))

    conn.commit()
    conn.close()

    return jsonify({'status': 'sent'})
# --- Socket.IO Chat handlers ---
@socketio.on('connect')
def on_connect():
    user_id = session.get('user_id')
    username = session.get('username')
    display = session.get('display', username)

    if not user_id or not username:
        return

    # --- Join rooms ---
    join_room(f"user_{user_id}")   # private DM room
    join_room('global')            # main chat room

    # --- Normalize chat history before sending ---
    history = []
    for msg in CHAT_HISTORY[-20:]:  # limit to 20
        history.append({
            'user': msg.get('user') or msg.get('display') or msg.get('username') or 'Unknown',
            'msg': msg.get('msg') or msg.get('message') or '',
            'time': msg.get('time') or msg.get('timestamp') or '',
            'color': msg.get('color', '#ffffff'),
            'is_html': msg.get('is_html', False)
        })

    emit('chat_history', history)
    emit('queue_update', MUSIC_QUEUE)
    emit('now_playing', NOW_PLAYING)

    # --- Announce to everyone except self ---
    socketio.emit(
        'system',
        {
            'msg': f'{display} joined the chat.',
            'time': datetime.now().strftime('%H:%M')
        },
        room='global',
        include_self=False
    )

    # --- Optional (confirmation just for user) ---
    emit('system', {'msg': f'Welcome back, {display}!', 'time': datetime.now().strftime('%H:%M')})

@socketio.on('disconnect')
def on_disconnect():
    if 'username' in session:
        socketio.emit('system', {'msg': f'{session.get("display", session.get("username"))} left.', 'time': datetime.now().strftime('%H:%M')}, room='global')

@socketio.on('send_chat')
def handle_chat(data):
    user = session.get('username')
    if not user:
        return

    text = (data.get('text') or '').strip()
    if not text:
        return

    # ✅ Detect HTML messages (stickers, system embeds, etc.)
    is_html = bool(data.get('html') or data.get('is_html'))

    payload = {
        'user': session.get('display', user),
        'msg': text,
        'time': datetime.now().strftime('%H:%M'),
        'color': session.get('color', '#ffffff'),
        'is_html': is_html
    }

    # ✅ Keep chat history limited
    CHAT_HISTORY.append(payload)
    if len(CHAT_HISTORY) > 30:
        CHAT_HISTORY.pop(0)

    # ✅ Only save normal text to DB (skip stickers or embedded HTML)
    if not is_html:
        save_chat_message(
            session.get('username'),
            session.get('display'),
            session.get('color'),
            text
        )

    # ✅ Broadcast message to everyone
    socketio.emit('chat_message', payload, room='global')
    import sqlite3

def get_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

db = get_db()

@socketio.on('send_dm')
def handle_dm(data):
    sender_id = session.get('user_id')
    sender_name = session.get('username')
    msg = (data.get('msg') or '').strip()
    to_user = data.get('to')

    # --- Basic validation ---
    if not sender_id or not msg or not to_user:
        return

    conn = db_connect()
    cur = conn.cursor()

    # --- Get receiver info ---
    cur.execute("SELECT id, profile_pic FROM users WHERE username=?", (to_user,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return

    receiver_id = row["id"]
    receiver_pic = row["profile_pic"]

    # --- Store message in database ---
    cur.execute("""
        INSERT INTO dm_messages (sender_id, receiver_id, msg)
        VALUES (?, ?, ?)
    """, (sender_id, receiver_id, msg))
    conn.commit()

    # --- Get sender's profile pic ---
    cur.execute("SELECT profile_pic FROM users WHERE id=?", (sender_id,))
    srow = cur.fetchone()
    sender_pic = srow["profile_pic"] if srow and srow["profile_pic"] else None

    conn.close()

    # --- Clean paths to avoid duplication ---
    def clean_avatar_path(pic):
        if not pic:
            return "/static/default.png"
        # avoid double "avatars/avatars"
        base = os.path.basename(pic)
        return f"/avatars/{base}"

    sender_pic_url = clean_avatar_path(sender_pic)

    # --- DM packet payload ---
    dm_packet = {
        "from": sender_name,
        "to": to_user,
        "msg": msg,
        "time": datetime.now().strftime("%H:%M"),
        "pic": sender_pic_url
    }

    # --- Emit message to both participants ---
    socketio.emit("dm_message", dm_packet, room=f"user_{receiver_id}")
    socketio.emit("dm_message", dm_packet, room=f"user_{sender_id}")

@socketio.on('typing')
def handle_typing(data):
    username = session.get('display') or session.get('username')
    emit('user_typing', {'user': username}, broadcast=True, include_self=False)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    username = session.get('display') or session.get('username')
    emit('user_stop_typing', {'user': username}, broadcast=True, include_self=False)
    # --- Commands handled here (play/skip) ---
    if text.startswith('/'):
        parts = text.split(' ', 1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ''
        if cmd == '/play' and arg:
            track = fetch_track(arg)
            if track:
                MUSIC_QUEUE.append({
                    'id': int(datetime.utcnow().timestamp()*1000),
                    'title': track['title'],
                    'url': track['url'],
                    'webpage_url': track.get('webpage_url'),
                    'requested_by': user
                })
                if not NOW_PLAYING:
                    _start_next_track()
                socketio.emit('queue_update', MUSIC_QUEUE, broadcast=True)
                socketio.emit('now_playing', NOW_PLAYING, broadcast=True)
        elif cmd == '/skip':
            if MUSIC_QUEUE:
                if NOW_PLAYING and MUSIC_QUEUE and MUSIC_QUEUE[0].get('id') == NOW_PLAYING.get('id'):
                    MUSIC_QUEUE.pop(0)
                _start_next_track()
                socketio.emit('queue_update', MUSIC_QUEUE, broadcast=True)
                socketio.emit('system', {'msg': f'{session.get("display", user)} skipped the track', 'time': datetime.now().strftime('%H:%M')}, room='global')
    # commands handled here (play/skip)

@app.route('/upload_sticker', methods=['POST'])
def upload_sticker():
    if 'user_id' not in session:
        return jsonify({'error':'not logged in'}), 401
    if 'file' not in request.files:
        return jsonify({'error':'no file'}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error':'empty filename'}), 400
    fn = secure_filename(f.filename)
    new_name = f"{session['username']}_{int(datetime.utcnow().timestamp())}_{fn}"
    path = os.path.join(STICKER_FOLDER, new_name)
    f.save(path)
    return jsonify({'ok': True, 'url': url_for('sticker_file', filename=new_name)})

@app.route('/stickers', methods=['GET'])
def list_stickers():
    files = []
    for fn in os.listdir(STICKER_FOLDER):
        if fn.startswith('.'): continue
        files.append({'url': url_for('sticker_file', filename=fn)})
    return jsonify(sorted(files, key=lambda x:x['url']))

@app.route('/stickers/<path:filename>')
def sticker_file(filename):
    return send_from_directory(STICKER_FOLDER, filename)

@app.route('/link_preview')
def link_preview():
    url = request.args.get('url')
    if not url: return jsonify({})
    try:
        r = requests.get(url, timeout=3, headers={'User-Agent':'Mozilla/5.0'})
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.title.string if soup.title else ''
        desc = ''
        image = ''
        if (meta := soup.find('meta', attrs={'name':'description'})):
            desc = meta.get('content', '')
        if (og := soup.find('meta', property='og:image')):
            image = og.get('content', '')
        return jsonify({'title': title, 'desc': desc[:120], 'image': image})
    except Exception:
        return jsonify({})
# --- Run server ---
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)