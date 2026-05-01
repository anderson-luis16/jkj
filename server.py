from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
DB = "saas.db"

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
    key = data["key"]
    days = data.get("days", 0)

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
    key = data["key"]
    hwid = data["hwid"]

    conn = db()
    c = conn.cursor()
    c.execute("SELECT hwid, expires, active FROM licenses WHERE key=?", (key,))
    row = c.fetchone()

    if not row:
        return jsonify({"status": "invalid"})

    db_hwid, expires, active = row

    if active == 0:
        return jsonify({"status": "blocked"})

    if expires:
        if datetime.now().strftime("%Y-%m-%d") > expires:
            return jsonify({"status": "expired"})

    if db_hwid == "" or db_hwid == hwid:
        c.execute("UPDATE licenses SET hwid=? WHERE key=?", (hwid, key))
        conn.commit()
        return jsonify({"status": "ok"})

    return jsonify({"status": "wrong_device"})

# ================= ADMIN LIST =================
@app.route("/list", methods=["GET"])
def list_keys():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM licenses")
    return jsonify(c.fetchall())

# ================= BLOCK =================
@app.route("/block", methods=["POST"])
def block():
    key = request.json["key"]
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE licenses SET active=0 WHERE key=?", (key,))
    conn.commit()
    return jsonify({"status": "blocked"})

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)