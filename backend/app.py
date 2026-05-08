import os
import socket
import secrets
from functools import wraps
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.errors

load_dotenv()

app = Flask(__name__)
CORS(app)

sessions: dict[str, str] = {}


# ── DB ヘルパー ────────────────────────────────────────────────

def get_db_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        dbname=os.getenv("DB_NAME", "postgres"),
        connect_timeout=3,
    )


def check_db_connection() -> dict:
    try:
        conn = get_db_conn()
        conn.close()
        return {"connected": True, "message": "接続OK"}
    except Exception as e:
        return {"connected": False, "message": str(e)}


def init_db():
    """起動時にテーブルを自動作成し、ユーザーが0件なら管理者を初期登録する。"""
    try:
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id           SERIAL PRIMARY KEY,
                    username     VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at   TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("SELECT COUNT(*) FROM users")
            (count,) = cur.fetchone()
            if count == 0:
                admin_user = os.getenv("ADMIN_USERNAME", "admin")
                admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
                cur.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                    (admin_user, generate_password_hash(admin_pass)),
                )
                print(f"[DB] 初期管理者ユーザー '{admin_user}' を作成しました")
        conn.commit()
        conn.close()
        print("[DB] テーブル初期化完了")
    except Exception as e:
        print(f"[DB] 初期化スキップ（DB未接続時は起動のみ継続）: {e}")


# ── 認証デコレーター ──────────────────────────────────────────

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token not in sessions:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper


# ── ユーティリティ ────────────────────────────────────────────

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Unknown"


# ── エンドポイント ────────────────────────────────────────────

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/status")
def status():
    db = check_db_connection()
    return jsonify({"api": {"connected": True}, "db": db})


@app.route("/api/register", methods=["POST"])
def register():
    data     = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "message": "ユーザー名とパスワードは必須です"}), 400
    if len(username) > 50:
        return jsonify({"success": False, "message": "ユーザー名は50文字以内にしてください"}), 400
    if len(password) < 6:
        return jsonify({"success": False, "message": "パスワードは6文字以上にしてください"}), 400

    try:
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, generate_password_hash(password)),
            )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"ユーザー '{username}' を登録しました"})
    except psycopg2.errors.UniqueViolation:
        return jsonify({"success": False, "message": "そのユーザー名はすでに使われています"}), 409
    except Exception as e:
        return jsonify({"success": False, "message": f"DB エラー: {e}"}), 500


@app.route("/api/login", methods=["POST"])
def login():
    data     = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "message": "ユーザー名とパスワードを入力してください"}), 400

    try:
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
        conn.close()

        if row and check_password_hash(row[0], password):
            token = secrets.token_hex(32)
            sessions[token] = username
            return jsonify({"success": True, "token": token})

        return jsonify({"success": False, "message": "ユーザー名またはパスワードが違います"}), 401
    except Exception as e:
        return jsonify({"success": False, "message": f"DB エラー: {e}"}), 500


@app.route("/api/server-info")
@require_auth
def server_info():
    hostname = socket.gethostname()
    local_ip = get_local_ip()
    db       = check_db_connection()
    return jsonify({"hostname": hostname, "local_ip": local_ip, "db": db})


@app.route("/api/logout", methods=["POST"])
def logout():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    sessions.pop(token, None)
    return jsonify({"success": True})


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
