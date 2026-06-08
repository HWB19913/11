FROM python:3.11-slim

WORKDIR /app

# 1. 更新源并安装所有必要的 C++ 编译环境
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

# 2. 关键步骤：在安装前先升级这些构建工具，确保能识别各种预编译包
RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
    && pip config set global.trusted-host mirrors.cloud.tencent.com \
    && pip install --upgrade pip setuptools wheel

# 3. 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

CMD ["python3", "run.py"]
