# 使用您本地的完整 Python 镜像
FROM python:3.9.25-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 设置国内 PyPI 镜像加速
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "app.py"]