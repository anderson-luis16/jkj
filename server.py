from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__)

DB = "/tmp/saas.db"

# ================= DB =================
def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init():
    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS licenses (
        key TEXT PRIMARY KEY,
        hwid TEXT DEFAULT '',
        expires TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    conn.commit()
    conn.close()

init()

# ================= HOME =================
@app.route("/")
def home():
    return "SAAS API ONLINE 🚀"

# ================= CREATE KEY =================
@app.route("/create", methods=["POST"])
def create():
    data = request.json
    key = data.get("key")
    days = int(data.get("days", 0))

    if not key:
        return jsonify({"status": "error", "msg": "missing key"})

    expires = None
    if days > 0:
        expires = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")

    conn = db()
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO licenses (key, expires, active) VALUES (?, ?, 1)",
            (key, expires)
        )
        conn.commit()
        return jsonify({"status": "created"})
    except:
        return jsonify({"status": "exists"})

# ================= VALIDATE =================
@app.route("/validate", methods=["POST"])
def validate():
    data = request.json
    key = data.get("key")
    hwid = data.get("hwid")

    if not key or not hwid:
        return jsonify({"status": "error"})

    conn = db()
    c = conn.cursor()

    c.execute("SELECT * FROM licenses WHERE key=?", (key,))
    row = c.fetchone()

    if not row:
        return jsonify({"status": "invalid"})

    if row["active"] == 0:
        return jsonify({"status": "blocked"})

    if row["expires"]:
        if datetime.utcnow().strftime("%Y-%m-%d") > row["expires"]:
            return jsonify({"status": "expired"})

    if row["hwid"] == "" or row["hwid"] == hwid:
        c.execute("UPDATE licenses SET hwid=? WHERE key=?", (hwid, key))
        conn.commit()
        return jsonify({"status": "ok"})

    return jsonify({"status": "wrong_device"})

# ================= LIST =================
@app.route("/list", methods=["GET"])
def list_keys():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM licenses")
    return jsonify([dict(row) for row in c.fetchall()])

# ================= BLOCK =================
@app.route("/block", methods=["POST"])
def block():
    key = request.json.get("key")

    conn = db()
    c = conn.cursor()
    c.execute("UPDATE licenses SET active=0 WHERE key=?", (key,))
    conn.commit()

    return jsonify({"status": "blocked"})

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)