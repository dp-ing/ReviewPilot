"""
Demo auth service — 故意包含多种安全漏洞和代码质量问题。
仅用于 ReviewPilot 演示，切勿在生产环境使用！
"""
import sqlite3
import os
from flask import request, jsonify, make_response

# VULNERABLE: 硬编码数据库凭据
DB_HOST = "192.168.1.100"
DB_USER = "admin"
DB_PASSWORD = "P@ssw0rd123!"
API_SECRET = "sk-4a7b9c2d8e6f1a3b5c7d9e0f"


def login():
    """用户登录 — SQL 注入 + 弱密码验证"""
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    conn = sqlite3.connect("app.db")
    # VULNERABLE: SQL 注入（f-string 拼接）
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor = conn.execute(query)
    user = cursor.fetchone()
    conn.close()

    if user:
        resp = make_response(jsonify({"status": "ok", "user": user}))
        # VULNERABLE: Cookie 未设置 HttpOnly/Secure
        resp.set_cookie("session", username)
        return resp
    return jsonify({"error": "invalid credentials"}), 401


def get_user_profile():
    """获取用户资料 — XSS 漏洞"""
    user_id = request.args.get("id", "")
    conn = sqlite3.connect("app.db")
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor = conn.execute(query)
    user = cursor.fetchone()
    conn.close()

    if user:
        # VULNERABLE: XSS — 用户输入直接渲染到 HTML
        html = f"<h1>Welcome, {user[1]}</h1><p>Email: {user[2]}</p>"
        return html
    return "User not found", 404


def upload_avatar():
    """上传头像 — 路径遍历漏洞"""
    file = request.files.get("avatar")
    if file:
        filename = file.filename
        # VULNERABLE: 路径遍历 — 未校验文件名
        save_path = os.path.join("/var/www/uploads/", filename)
        file.save(save_path)
        return jsonify({"path": save_path})
    return jsonify({"error": "no file"}), 400


def search_orders():
    """搜索订单 — SQL 注入（字符串拼接）"""
    keyword = request.args.get("q", "")
    status = request.args.get("status", "all")

    conn = sqlite3.connect("app.db")
    # VULNERABLE: SQL 注入
    sql = "SELECT * FROM orders WHERE name LIKE '%" + keyword + "%'"
    if status != "all":
        sql += " AND status = '" + status + "'"
    cursor = conn.execute(sql)
    results = cursor.fetchall()

    # VULNERABLE: 资源泄漏 — 异常时 conn 未关闭
    return jsonify(results)


def delete_account(user_id):
    """删除账号 — 缺乏权限校验"""
    conn = sqlite3.connect("app.db")
    try:
        # VULNERABLE: SQL 注入 + 无权限校验
        conn.execute(f"DELETE FROM users WHERE id = {user_id}")
        conn.execute(f"DELETE FROM orders WHERE user_id = {user_id}")
        conn.commit()
    except:
        # VULNERABLE: 裸 except 掩盖错误
        pass
    conn.close()
    return jsonify({"status": "deleted"})


def get_db_stats():
    """获取数据库统计 — 信息泄露"""
    conn = sqlite3.connect("app.db")
    try:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        stats = {}
        for table in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
            stats[table[0]] = count
        # VULNERABLE: 暴露数据库结构
        return jsonify({"tables": stats, "db_path": "app.db"})
    except:
        return jsonify({"error": "stats unavailable"})
