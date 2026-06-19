"""
Demo API handler — 故意包含多种安全漏洞，用于 ReviewPilot 检测演示。
请勿在生产环境中使用！
"""
import os
import pickle
import sqlite3
import subprocess
from flask import request, jsonify, render_template_string


# ============================================================
# 硬编码密码/密钥
# ============================================================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "SuperSecret@2024"
JWT_SECRET = "my-jwt-secret-key-do-not-use-in-production"
STRIPE_API_KEY = "sk_live_abc123xyz789"
DATABASE_URL = "postgresql://admin:P@ssw0rd@localhost:5432/proddb"


def login():
    """用户登录 — 存在多个安全漏洞"""
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()

    # VULNERABLE: SQL 注入 — 字符串拼接
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"status": "ok", "token": JWT_SECRET})
    return jsonify({"status": "error"}), 401


def search_products():
    """商品搜索 — SQL 注入 + XSS"""
    keyword = request.args.get("keyword", "")
    sort = request.args.get("sort", "price")

    # VULNERABLE: f-string SQL 注入
    sql = f"SELECT id, name, price FROM products WHERE name LIKE '%{keyword}%' ORDER BY {sort}"
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()

    # VULNERABLE: XSS — 未转义的用户输入直接渲染到 HTML
    html = "<h1>Search results for: " + keyword + "</h1>"
    for row in rows:
        html += f"<div class='product'><h3>{row[1]}</h3><p>${row[2]}</p></div>"

    return render_template_string(html)


def export_data(fmt: str):
    """导出用户数据 — 命令注入 + eval"""
    export_id = request.args.get("id", "")

    # VULNERABLE: eval 动态执行
    config = eval(request.args.get("config", "{}"))

    if fmt == "csv":
        cmd = f"python export.py --format csv --id {export_id}"
        # VULNERABLE: subprocess shell=True
        subprocess.call(cmd, shell=True)
    elif fmt == "json":
        cmd = f"python export.py --format json --id {export_id}"
        subprocess.run(cmd, shell=True)

    return jsonify({"status": "exporting", "config": config})


def upload_file():
    """文件上传 — 不安全反序列化 + 路径遍历"""
    uploaded = request.files.get("file")
    if uploaded:
        # VULNERABLE: 未验证文件名，路径遍历
        save_path = os.path.join("/var/uploads", uploaded.filename)
        uploaded.save(save_path)

        # VULNERABLE: pickle.loads 反序列化
        data = uploaded.read()
        obj = pickle.loads(data)
        return jsonify({"status": "ok", "parsed": str(obj)})
    return jsonify({"status": "no file"}), 400


def get_stats():
    """获取统计数据 — 裸 except 掩盖错误"""
    try:
        conn = sqlite3.connect("app.db")
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor = conn.execute("SELECT COUNT(*) FROM orders")
        order_count = cursor.fetchone()[0]
        # VULNERABLE: 文件句柄未关闭 — 手动 open/close 无 with
        f = open("/tmp/stats.log", "a")
        f.write(f"Stats requested: users={user_count}, orders={order_count}\n")
        f.close()
        conn.close()
        return jsonify({"users": user_count, "orders": order_count})
    except:
        # VULNERABLE: 裸 except 掩盖所有错误
        return jsonify({"users": 0, "orders": 0})
    finally:
        try:
            conn.close()
        except:
            pass


def process_payment(amount: float, stripe_token: str):
    """处理支付 — SQL 注入(formatted string %) + 硬编码密钥"""
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()

    # VULNERABLE: % 格式化 SQL 注入
    query = "INSERT INTO payments (amount, status, token) VALUES (%s, 'pending', '%s')" % (amount, stripe_token)
    cursor.execute(query)
    conn.commit()
    conn.close()

    return jsonify({"status": "charged", "key": STRIPE_API_KEY})
