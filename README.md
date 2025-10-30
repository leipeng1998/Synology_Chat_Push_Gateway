群晖消息推送网关系统
系统简介
群晖消息推送网关系统是一个基于 Flask 的 Web 应用，用于监控群晖 Chat 的未读消息并通过 Gotify 推送到移动设备。系统支持多用户管理，自动处理会话过期，提供完整的 Web 管理界面。

功能特性
🔔 核心功能
实时消息监控 - 自动监控群晖 Chat 的未读消息

多平台推送 - 通过 Gotify 推送到移动设备

多用户支持 - 支持多个群晖账户同时监控

智能会话管理 - 自动检测和刷新过期的 SID

🛡️ 系统管理
Web 管理界面 - 完整的用户和系统管理

自动容错 - 单个用户故障不影响整体系统

定期维护 - 自动清理过期数据

实时状态监控 - 系统运行状态可视化

🔒 安全特性
密码加密存储 - 用户密码安全存储

会话自动刷新 - 避免频繁重新登录

访问控制 - 用户封禁管理

系统架构
text
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  群晖 DSM   │◄──►│  推送网关   │◄──►│  Gotify服务器 │
└─────────────┘    └─────────────┘    └─────────────┘
                            │
                    ┌─────────────┐
                    │   SQLite    │
                    │   数据库     │
                    └─────────────┘
快速开始
环境要求
Python 3.8+

群晖 DSM 7.0+

Gotify 服务器

安装步骤
克隆项目

bash
git clone <项目地址>
cd synology_chat_push_gateway
安装依赖

bash
pip install -r requirements.txt
初始化系统

访问 http://localhost:5000

填写群晖 DSM 信息：

DSM 地址（如：https://192.168.1.100:5001）

管理员用户名和密码

添加推送用户

在用户管理页面添加需要监控的群晖用户

配置对应的 Gotify URL 和 Token

配置文件
系统使用 SQLite 数据库自动管理配置，无需手动配置文件。

核心模块说明
📁 文件结构
text
synology_chat_push_gateway/
├── app.py                 # Flask 主应用
├── syno_func.py          # 群晖 API 功能
├── use_sql.py            # 数据库操作
├── init_sql.py           # 数据库初始化
├── templates/            # HTML 模板
│   ├── base.html
│   ├── users.html
│   ├── init.html
│   └── login.html
└── push_gateway.db       # 数据库文件（自动生成）
🔧 主要模块
app.py - Web 应用
Flask Web 服务器

用户管理界面

系统状态监控

API 接口

syno_func.py - 业务逻辑
群晖 API 集成

消息监控循环

SID 自动管理

Gotify 推送

use_sql.py - 数据层
用户信息管理

消息记录存储

系统配置管理

SID 状态跟踪
