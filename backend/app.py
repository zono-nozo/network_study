import os
import socket
import secrets
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

sessions: dict[str, str] = {}


def check_db_connection() -> dict:
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            dbname=os.getenv("DB_NAME", "postgres"),
            connect_timeout=3,
        )
        conn.close()
        return {"connected": True, "message": "接続OK"}
    except Exception as e:
        return {"connected": False, "message": str(e)}


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Unknown"


def require_auth(f):
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token not in sessions:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return wrapper


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/status")
def status():
    db = check_db_connection()
    return jsonify({
        "api": {"connected": True},
        "db": db,
    })


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")

    expected_user = os.getenv("ADMIN_USERNAME", "admin")
    expected_pass = os.getenv("ADMIN_PASSWORD", "admin123")

    if username == expected_user and password == expected_pass:
        token = secrets.token_hex(32)
        sessions[token] = username
        return jsonify({"success": True, "token": token})

    return jsonify({"success": False, "message": "ユーザー名またはパスワードが違います"}), 401


@app.route("/api/server-info")
@require_auth
def server_info():
    hostname = socket.gethostname()
    local_ip = get_local_ip()
    db = check_db_connection()
    return jsonify({
        "hostname": hostname,
        "local_ip": local_ip,
        "db": db,
    })


@app.route("/api/logout", methods=["POST"])
def logout():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    sessions.pop(token, None)
    return jsonify({"success": True})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
