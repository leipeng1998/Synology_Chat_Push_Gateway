from flask import Flask, render_template, request, redirect, url_for
import change_sql
from flask import jsonify
app = Flask(__name__)


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


if __name__ == "__main__":
    app.run(debug=True)
