# Oracle 数据批量修改工具 Docker 镜像
# 基于 Ubuntu 22.04，支持 VNC/noVNC 浏览器访问

FROM ubuntu:22.04

LABEL maintainer="Oracle Table Change Tool"
LABEL version="2.6"
LABEL description="Oracle数据批量修改工具 - Docker版本，支持浏览器访问"

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:0
ENV HOME=/root
ENV NO_VNC_PORT=6080
ENV VNC_PORT=5900

# 安装基础依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-tk \
    tigervnc-standalone-server \
    tigervnc-common \
    novnc \
    websockify \
    x11-utils \
    x11-apps \
    wget \
    unzip \
    libaio1 \
    libaio-dev \
    fonts-noto-cjk \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# 安装 Oracle Instant Client (基础版)
RUN mkdir -p /opt/oracle && \
    cd /opt/oracle && \
    wget -q https://download.oracle.com/otn_software/linux/instantclient/2115000/instantclient-basic-linux.x64-21.15.0.0.0dbru.zip -O instantclient.zip && \
    unzip instantclient.zip && \
    rm instantclient.zip && \
    echo "/opt/oracle/instantclient_21_15" > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_15:$LD_LIBRARY_PATH
ENV TNS_ADMIN=/opt/oracle/instantclient_21_15/network/admin

# 安装 Python 依赖
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt --break-system-packages

# 复制应用代码
COPY . /app/

# 设置工作目录
WORKDIR /app

# 创建启动脚本
RUN echo '#!/bin/bash\n\
# 启动 VNC Server\n\
vncserver :0 -geometry 1280x800 -depth 24 -SecurityTypes None -PasswordFile "" &\n\
sleep 2\n\
\n\
# 启动 noVNC\n\
cd /usr/share/novnc && websockify --web=/usr/share/novnc 6080 localhost:5900 &\n\
sleep 2\n\
\n\
# 启动应用\n\
cd /app && python3 main.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# 创建 VNC 配置
RUN mkdir -p /root/.vnc && \
    echo "" > /root/.vnc/passwd && \
    chmod 600 /root/.vnc/passwd

# 暴露端口
# 6080: noVNC Web 端口 (浏览器访问)
# 5900: VNC 端口 (VNC 客户端访问)
EXPOSE 6080 5900

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:6080/ || exit 1

# 启动命令
CMD ["/app/start.sh"]