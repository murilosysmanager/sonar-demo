"""Aplicação Flask de demonstração para testar o SonarQube Cloud.

ATENÇÃO: este código contém falhas de segurança PROPOSITAIS, apenas para que
o scanner tenha o que encontrar. Nunca publique isto em produção.
"""
import hashlib
import os
import sqlite3
import subprocess

from flask import Flask, request

app = Flask(__name__)

# [FALHA PROPOSITAL] Segredo fixo no código (OWASP A02/A07, CWE-798)
SECRET_KEY = "super-secret-key-123"
app.config["SECRET_KEY"] = SECRET_KEY

DB_PATH = os.environ.get("DB_PATH", "demo.db")


def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_db()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users "
        "(id INTEGER PRIMARY KEY, name TEXT, password TEXT)"
    )
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return {"status": "ok", "app": "sonar-demo"}


@app.route("/user")
def get_user():
    name = request.args.get("name", "")
    conn = get_db()
    # [FALHA PROPOSITAL] SQL Injection por concatenação (OWASP A03, CWE-89)
    query = "SELECT id, name FROM users WHERE name = '" + name + "'"
    rows = conn.execute(query).fetchall()
    conn.close()
    return {"users": rows}


@app.route("/safe/user")
def get_user_safe():
    """Versão correta, com query parametrizada, para comparação."""
    name = request.args.get("name", "")
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name FROM users WHERE name = ?", (name,)
    ).fetchall()
    conn.close()
    return {"users": rows}


@app.route("/hello")
def hello():
    name = request.args.get("name", "mundo")
    # [FALHA PROPOSITAL] XSS refletido, entrada sem escape (OWASP A03, CWE-79)
    return "<h1>Olá, " + name + "</h1>"


@app.route("/ping")
def ping():
    host = request.args.get("host", "localhost")
    # [FALHA PROPOSITAL] Injeção de comando com shell=True (OWASP A03, CWE-78)
    return subprocess.check_output("ping -c 1 " + host, shell=True)


@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    password = request.form["password"]
    # [FALHA PROPOSITAL] Hash fraco (MD5) para senha (OWASP A02, CWE-327)
    hashed = hashlib.md5(password.encode()).hexdigest()
    conn = get_db()
    conn.execute(
        "INSERT INTO users (name, password) VALUES (?, ?)", (name, hashed)
    )
    conn.commit()
    conn.close()
    return {"registered": name}, 201


if __name__ == "__main__":
    init_db()
    # [FALHA PROPOSITAL] Debug ligado e escutando em todas as interfaces
    # (OWASP A05, CWE-489)
    app.run(debug=True, host="0.0.0.0")
