from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# ================= HOME =================
@app.route("/")
def home():
    return "API SaaS online funcionando 🚀"

# ================= DB (Render-safe) =================
DB = "/tmp/saas.db"

def db():
    conn = sqlite3.connect(DB)
    return conn

def init():
    conn = db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            key TEXT PRIMARY KEY,
            hwid TEXT,
            expires TEXT,
            active INTEGER
        )
    """)
    conn.commit()
    conn.close()

init()

# ================= CREATE KEY =================
@app.route("/create", methods=["POST"])
def create():
    data = request.json
    key = data.get("key")
    days = data.get("days", 0)

    if not key:
        return jsonify({"status": "error", "msg": "missing key"})

    expires = None
    if days > 0:
        expires = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    conn = db()
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO licenses VALUES (?, '', ?, 1)",
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
    c.execute("SELECT hwid, expires, active FROM licenses WHERE key=?", (key,))
    row = c.fetchone()

    if not row:
        return jsonify({"status": "invalid"})

    db_hwid, expires, active = row

    if active == 0:
        return jsonify({"status": "blocked"})

    if expires and datetime.now().strftime("%Y-%m-%d") > expires:
        return jsonify({"status": "expired"})

    if db_hwid == "" or db_hwid == hwid:
        c.execute("UPDATE licenses SET hwid=? WHERE key=?", (hwid, key))
        conn.commit()
        return jsonify({"status": "ok"})

    return jsonify({"status": "wrong_device"})

# ================= LIST (ADMIN) =================
@app.route("/list", methods=["GET"])
def list_keys():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM licenses")
    return jsonify(c.fetchall())

# ================= BLOCK =================
@app.route("/block", methods=["POST"])
def block():
    key = request.json.get("key")

    conn = db()
    c = conn.cursor()
    c.execute("UPDATE licenses SET active=0 WHERE key=?", (key,))
    conn.commit()

    return jsonify({"status": "blocked"})

# ================= RENDER ENTRY =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)