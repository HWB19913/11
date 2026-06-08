# 基础镜像
FROM alpine:3.13

# 安装 HTTPS 证书支持
RUN apk add ca-certificates

# 核心修正：一次性完成源切换和编译环境安装
# build-base: 提供 GCC/G++ 编译器，用来编译 CoolProp
# python3-dev: 提供 Python 头文件，编译必须
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tencent.com/g' /etc/apk/repositories \
&& apk add --update --no-cache python3 py3-pip build-base python3-dev \
&& rm -rf /var/cache/apk/*

# 拷贝项目文件
COPY . /app
WORKDIR /app

# 设置 pip 国内源并安装依赖
RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
&& pip config set global.trusted-host mirrors.cloud.tencent.com \
&& pip install --upgrade pip \
&& pip install --user -r requirements.txt

# 暴露端口
EXPOSE 80

# 启动命令
CMD ["python3", "run.py"]
