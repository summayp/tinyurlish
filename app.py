from flask import Flask, request, redirect, jsonify, render_template
import sqlite3, hashlib, time, os, re

DB_PATH = os.environ.get("TINYURLISH_DB", "tinyurlish.db")
app = Flask(__name__)

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                click_count INTEGER NOT NULL DEFAULT 0,
                last_access INTEGER
            )
        """)
        try:
            con.execute("ALTER TABLE urls ADD COLUMN click_count INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        try:
            con.execute("ALTER TABLE urls ADD COLUMN last_access INTEGER")
        except Exception:
            pass
init_db()

CODE_RE = re.compile(r"^[A-Za-z0-9_-]{3,32}$")

def normalize_url(u: str) -> str:
    u = u.strip()
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u
    return u

def gen_code(url: str) -> str:
    raw = f"{url}|{time.time_ns()}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:7]

def code_exists(code: str) -> bool:
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute("SELECT 1 FROM urls WHERE code=? LIMIT 1", (code,))
        return cur.fetchone() is not None

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/ui")
def ui():
    return render_template("index.html")

@app.post("/shorten")
def shorten():
    data = request.get_json(force=True, silent=True) or {}
    url = data.get("url", "")
    code = data.get("code", "")
    if not url:
        return jsonify(error="missing url"), 400
    url = normalize_url(url)
    if code:
        if not CODE_RE.match(code):
            return jsonify(error="invalid code"), 400
        if code_exists(code):
            return jsonify(error="code already exists"), 409
    else:
        code = gen_code(url)
        while code_exists(code):
            code = gen_code(url)
    with sqlite3.connect(DB_PATH) as con:
        con.execute("INSERT INTO urls(code,url,created_at) VALUES(?,?,?)",
                    (code, url, int(time.time())))
    return jsonify(code=code, url=url)

@app.get("/<code>")
def follow(code):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute("SELECT url FROM urls WHERE code=?", (code,))
        row = cur.fetchone()
        if not row:
            return jsonify(error="not found"), 404
        con.execute("UPDATE urls SET click_count = click_count + 1, last_access=? WHERE code=?",
                    (int(time.time()), code))
        return redirect(row[0], code=302)

@app.get("/admin/recent")
def recent():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute("SELECT code,url,created_at,click_count,last_access FROM urls ORDER BY id DESC LIMIT 20")
        rows = [{"code":c, "url":u, "created_at":ts, "clicks":cc, "last_access":la} for (c,u,ts,cc,la) in cur.fetchall()]
    return jsonify(rows)

@app.get("/admin/stats")
def stats():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute("SELECT code,url,click_count,last_access FROM urls ORDER BY click_count DESC, id DESC LIMIT 20")
        rows = [{"code":c, "url":u, "clicks":cc, "last_access":la} for (c,u,cc,la) in cur.fetchall()]
    return jsonify(rows)
