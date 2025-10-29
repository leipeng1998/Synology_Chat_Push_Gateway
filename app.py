import os

from flask import Flask, render_template, request, redirect, url_for
import change_sql
from flask import jsonify

import init_sql
from syno_func import get_syno_sid, get_user_info

app = Flask(__name__)

DB_FILE = "push_gateway.db"

# 检测数据库是否存在
def is_db_exist():
    return os.path.exists(DB_FILE)

# 存在入口就是后台，不存在就是初始化
@app.route("/")
def index():
    if is_db_exist():
        # 数据库存在 → 重定向到后台管理
        return redirect(url_for("admin_users"))
    else:
        # 数据库不存在 → 重定向到初始化页面
        return redirect(url_for("init_gateway"))

@app.route('/users')
def admin_users():
    """展示用户列表"""
    users = change_sql.get_all_users()
    # print(users)
    FIELDS = ["ID", "是否启用", "用户名", "密码", "gotify_url", "gotify_token"]
    return render_template("users.html", users=users, fields=FIELDS)


@app.route("/add_user", methods=["POST"])
def add_user():
    """添加新用户"""
    username = request.form.get("username")
    password = request.form.get("password")
    sid = request.form.get("sid")
    gotify_url = request.form.get("gotify_url")
    gotify_token = request.form.get("gotify_token")

    # 使用 change_sql 写入数据库
    change_sql.add_push_users_info(username, password, sid, gotify_url, gotify_token)

    return redirect(url_for("admin_users"))



@app.route("/toggle_ban_ajax/<int:user_id>", methods=["POST"])
def toggle_ban_ajax(user_id):
    try:
        user = change_sql.get_user_by_id(user_id)
        # print(user_id)
        if not user:
            return jsonify({"success": False, "message": "用户不存在"})

        new_status = 0 if user[1] == 1 else 1
        change_sql.update_user_status(user_id, new_status)
        return jsonify({"success": True, "new_status": new_status})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/edit_user/<int:user_id>", methods=["POST"])
def edit_user(user_id):
    # pass
    """修改用户信息"""
    username = request.form.get("username")
    password = request.form.get("password")
    gotify_url = request.form.get("gotify_url")
    gotify_token = request.form.get("gotify_token")
    change_sql.update_push_users_info(user_id, username, password, gotify_url, gotify_token)

    return redirect(url_for("admin_users"))

# 初始化页面
@app.route("/init_gateway")
def init_gateway():
    return render_template("init.html")

# 初始化数据库
@app.route('/initialize', methods=['POST'])
def initialize():
    try:
        dsm_url = request.form.get("dsm_url")
        dsm_user = request.form.get('dsm_user')
        dsm_pass = request.form.get('dsm_pass')
        # 可以在这里验证 DSM 账号密码（可选）
        print(f"收到 DSM地址: {dsm_url} , 用户名: {dsm_user}, 密码: {dsm_pass}")
        # 调用初始化方法
        init_sql.init_db()
        # 写入管理员
        admin_sid = get_syno_sid(dsm_url,dsm_user, dsm_pass)
        change_sql.add_push_users_info(dsm_user, dsm_pass,admin_sid)
        # 获得所有人员的信息
        get_user_info(dsm_url,admin_sid)


        return redirect(url_for('admin_users'))

    except Exception as e:
        return f"初始化失败: {str(e)}", 500


if __name__ == "__main__":
    app.run(debug=True)
