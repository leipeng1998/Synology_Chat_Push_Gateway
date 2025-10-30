"""
Synology Chat Push Gateway
Copyright 2024 leipeng1998

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
import time
import atexit
import logging
from flask import Flask, render_template, request, redirect, url_for, jsonify
import use_sql
import init_sql
from syno_func import get_syno_sid, get_user_info, write_channel_info_sql, main_run, cleanup_old_messages
from threading import Thread

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_FILE = "push_gateway.db"

# 全局变量来跟踪线程状态
monitor_thread = None
monitor_running = False


def is_db_exist():
    return os.path.exists(DB_FILE)


def ensure_database_integrity():
    """确保数据库完整性"""
    if not is_db_exist():
        logger.info("数据库文件不存在")
        return False

    # 检查表结构是否完整
    if not init_sql.check_tables_exist():
        logger.warning("数据库表结构不完整，重新初始化")
        return init_sql.init_app()

    return True


def start_monitor_thread():
    """启动消息监控线程"""
    global monitor_thread, monitor_running

    if not is_db_exist():
        logger.info("数据库不存在，跳过启动监控线程")
        return False

    # 确保数据库完整性
    if not ensure_database_integrity():
        logger.error("数据库完整性检查失败，无法启动监控线程")
        return False

    if monitor_thread and monitor_thread.is_alive():
        logger.info("监控线程已在运行")
        return True

    try:
        # 检查数据库中是否有用户数据
        users = use_sql.get_user_info()
        if not users:
            logger.warning("数据库中没有用户数据，跳过启动监控线程")
            return False

        monitor_thread = Thread(target=main_run, daemon=True, name="MessageMonitor")
        monitor_thread.start()
        monitor_running = True
        logger.info("消息监控线程启动成功")
        return True

    except Exception as e:
        logger.error(f"启动监控线程失败: {e}")
        return False


def stop_monitor_thread():
    """停止监控线程"""
    global monitor_running
    monitor_running = False
    logger.info("监控线程停止")


# 注册退出时的清理函数
atexit.register(stop_monitor_thread)


@app.route('/api/status')
def system_status():
    """系统状态检查接口"""
    status = {
        'database_exists': is_db_exist(),
        'database_integrity': ensure_database_integrity(),
        'monitor_running': monitor_thread.is_alive() if monitor_thread else False,
        'users_count': len(use_sql.get_user_info()) if is_db_exist() and ensure_database_integrity() else 0
    }
    return jsonify(status)


# 原有的路由保持不变
@app.route("/")
def index():
    if is_db_exist() and ensure_database_integrity():
        logger.info("Database exists and integrity ok, redirecting to admin")
        return redirect(url_for("admin_users"))
    else:
        logger.info("Database does not exist or integrity failed, redirecting to init")
        return redirect(url_for("init_gateway"))


@app.route('/users')
def admin_users():
    if not ensure_database_integrity():
        return redirect(url_for("init_gateway"))

    users = use_sql.get_all_users_no_password()
    print(users)
    print(type(users))
    FIELDS = ["ID", "是否启用", "用户名", "gotify_url", "gotify_token"]
    return render_template("users.html", users=users, fields=FIELDS)


@app.route("/add_user", methods=["POST"])
def add_user():
    if not ensure_database_integrity():
        return redirect(url_for("init_gateway"))

    username = request.form.get("username")
    password = request.form.get("password")
    sid = request.form.get("sid")
    gotify_url = request.form.get("gotify_url")
    gotify_token = request.form.get("gotify_token")
    use_sql.add_push_users_info(username, password, sid, gotify_url, gotify_token)
    return redirect(url_for("admin_users"))


@app.route("/toggle_ban_ajax/<int:user_id>", methods=["POST"])
def toggle_ban_ajax(user_id):
    try:
        user = use_sql.get_user_by_id(user_id)
        if not user:
            return jsonify({"success": False, "message": "用户不存在"})
        new_status = 0 if user[1] == 1 else 1
        use_sql.update_user_status(user_id, new_status)
        return jsonify({"success": True, "new_status": new_status})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/edit_user/<int:user_id>", methods=["POST"])
def edit_user(user_id):
    if not ensure_database_integrity():
        return redirect(url_for("init_gateway"))

    username = request.form.get("username")
    password = request.form.get("password")
    gotify_url = request.form.get("gotify_url")
    gotify_token = request.form.get("gotify_token")
    use_sql.update_push_users_info(user_id, username, password, gotify_url, gotify_token)
    return redirect(url_for("admin_users"))


@app.route("/init_gateway")
def init_gateway():
    return render_template("init.html")


@app.route('/initialize', methods=['POST'])
def initialize():
    try:
        dsm_url = request.form.get("dsm_url")
        dsm_user = request.form.get('dsm_user')
        dsm_pass = request.form.get('dsm_pass')

        logger.info(f"开始初始化系统，DSM地址: {dsm_url}, 用户: {dsm_user}")

        # 执行数据库初始化
        if not init_sql.init_app():
            raise Exception("数据库初始化失败")

        # 保存系统配置到数据库
        use_sql.set_system_config("BASE_URL", dsm_url, "群晖DSM服务器地址")
        use_sql.set_system_config("INIT_USER", dsm_user, "初始化管理员用户")

        # 获取SID并创建管理员用户
        admin_sid = get_syno_sid(dsm_user, dsm_pass)
        use_sql.add_push_users_info(dsm_user, dsm_pass, admin_sid)

        # 同步用户和频道信息
        get_user_info(admin_sid)
        write_channel_info_sql(admin_sid)

        # 初始化完成后启动监控线程
        start_monitor_thread()

        logger.info("系统初始化完成")
        return redirect(url_for('admin_users'))

    except Exception as e:
        logger.error(f"初始化失败: {e}")
        return f"初始化失败: {str(e)}", 500


# 应用启动时的初始化
def initialize_app():
    """应用启动初始化"""
    logger.info("应用启动初始化...")

    if is_db_exist() and ensure_database_integrity():
        logger.info("数据库完整性检查通过")
        # 清理旧消息
        try:
            cleanup_old_messages(days=7)
        except Exception as e:
            logger.warning(f"清理旧消息失败: {e}，但继续启动")

        # 启动监控线程
        start_monitor_thread()
    else:
        logger.info("数据库不存在或完整性检查失败，等待初始化")


if __name__ == "__main__":
    # 应用启动初始化
    initialize_app()

    # 启动 Flask 应用
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    # 当使用 flask run 命令时也会执行初始化
    initialize_app()