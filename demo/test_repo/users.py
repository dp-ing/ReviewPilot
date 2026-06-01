"""
Demo users module — 故意包含 SQL 注入漏洞，用于测试 ReviewPilot 检测能力。
请勿在生产环境中使用此代码！
"""
import sqlite3
from flask import request, jsonify


def search_users():
    """搜索用户 — 存在 SQL 注入漏洞（字符串拼接）"""
    name = request.args.get("name", "")
    conn = sqlite3.connect("app.db")
    # VULNERABLE: 用户输入直接拼接到 SQL 查询中
    query = "SELECT * FROM users WHERE name = '" + name + "'"
    cursor = conn.execute(query)
    results = cursor.fetchall()
    conn.close()
    return jsonify(results)


def delete_user(user_id):
    """删除用户 — 存在 SQL 注入漏洞（f-string 拼接）"""
    conn = sqlite3.connect("app.db")
    # VULNERABLE: 用户输入直接拼接到 SQL 中
    query = f"DELETE FROM users WHERE id = {user_id}"
    conn.execute(query)
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})


def update_email(user_id, new_email):
    """更新邮箱 — 存在 SQL 注入漏洞"""
    conn = sqlite3.connect("app.db")
    # VULNERABLE: 字符串格式化拼接 SQL
    query = "UPDATE users SET email = '%s' WHERE id = %s" % (new_email, user_id)
    conn.execute(query)
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})


def get_user_by_id(user_id):
    """根据ID获取用户 — 缺少异常处理和参数校验"""
    conn = sqlite3.connect("app.db")
    try:
        cursor = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        )
        result = cursor.fetchone()
    except:
        # VULNERABLE: 裸 except 捕获了所有异常，掩盖错误
        result = None
    conn.close()
    return jsonify(result)
