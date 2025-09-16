from flask import Flask, request, redirect, jsonify
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
                created_at INTEGER NOT NULL
            )
        """)
init_db()

def normalize_url(u: str) -> str:
    u = u.strip()
    if not re.match(r"^https?://", u, re.I):
        u = "https://" + u
    return u

def gen_code(url: str) -> str:
    # short, deterministic-ish code with timestamp salt
    raw = f"{url}|{time.time_ns()}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:7]

@app.post("/shorten")
def shorten():
    data = request.get_json(force=True, silent=True) or {}
    url = data.get("url")
    if not url:
        return jsonify(error="missing url"), 400
    url = normalize_url(url)
    code = gen_code(url)
    with sqlite3.connect(DB_PATH) as con:
        con.execute("INSERT INTO urls(code,url,created_at) VALUES(?,?,?)",
                    (code, url, int(time.time())))
    return jsonify(code=code)

@app.get("/<code>")
def follow(code):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute("SELECT url FROM urls WHERE code=?", (code,))
        row = cur.fetchone()
        if not row:
            return jsonify(error="not found"), 404
        return redirect(row[0], code=302)

@app.get("/admin/recent")
def recent():
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute("SELECT code,url,created_at FROM urls ORDER BY id DESC LIMIT 20")
        rows = [{"code":c, "url":u, "created_at":ts} for (c,u,ts) in cur.fetchall()]
    return jsonify(rows)

@app.get("/")
def home():
    return jsonify({"ok": True, "message": "Use POST /shorten, GET /<code>, GET /admin/recent"})

from flask import render_template
@app.get("/ui")
def ui():
    return render_template("index.html")
