# 切换到基于 Debian 的 slim 镜像，自带 Python 3.11，完美解决版本兼容问题
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装必要的编译工具（Debian 使用 apt-get）
# build-essential 包含了编译 C++ 代码所需的 gcc/g++ 等工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 拷贝项目文件
COPY . /app

# 设置 pip 国内源并安装依赖
# 注意：这里去掉了 --user，因为在容器里直接装在系统环境更稳健
RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
&& pip config set global.trusted-host mirrors.cloud.tencent.com \
&& pip install --upgrade pip \
&& pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 80

# 执行启动命令
CMD ["python3", "run.py"]
