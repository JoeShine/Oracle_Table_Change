# Oracle 数据批量修改工具 Docker 镜像
# 基于 Ubuntu 22.04，支持 VNC/noVNC 浏览器访问
# 使用 Easy Connect 方式连接数据库，无需配置文件

FROM ubuntu:22.04

LABEL maintainer="Oracle Table Change Tool"
LABEL version="2.7"
LABEL description="Oracle数据批量修改工具 - Docker版本，支持Easy Connect浏览器访问"

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
    curl \
    libaio1 \
    libaio-dev \
    fonts-noto-cjk \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# 创建 Oracle Instant Client 目录（仅用于库文件）
RUN mkdir -p /opt/oracle/instantclient_21_15

# 设置 Oracle 环境变量（仅库路径，无需TNS_ADMIN）
ENV ORACLE_HOME=/opt/oracle
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_15:$LD_LIBRARY_PATH

# 安装 Python 依赖
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt --break-system-packages

# 复制应用代码
COPY . /app/

# 设置工作目录
WORKDIR /app

# 创建启动脚本
RUN echo '#!/bin/bash\n\
set -e\n\
echo "========================================"\n\
echo "Oracle 数据批量修改工具"\n\
echo "========================================"\n\
echo ""\n\
echo "连接方式: Easy Connect (无需配置文件)"\n\
echo "连接字符串格式: host:port/service_name"\n\
echo "示例: oracle-server:1521/ORCL"\n\
echo ""\n\
\n\
# 检查 Oracle Instant Client\n\
if [ -d "/opt/oracle/instantclient_21_15" ] && [ "$(ls -A /opt/oracle/instantclient_21_15/*.so* 2>/dev/null)" ]; then\n\
    echo "Oracle Instant Client 已安装."\n\
else\n\
    echo "警告: Oracle Instant Client 未安装"\n\
    echo "请挂载 instantclient_21_15 目录到 /opt/oracle/instantclient_21_15"\n\
fi\n\
echo ""\n\
\n\
# 启动 VNC Server\n\
echo "启动 VNC Server..."\n\
vncserver :0 -geometry 1280x800 -depth 24 -SecurityTypes None -PasswordFile "" &\n\
sleep 2\n\
\n\
# 启动 noVNC\n\
echo "启动 noVNC..."\n\
cd /usr/share/novnc && websockify --web=/usr/share/novnc 6080 localhost:5900 &\n\
sleep 2\n\
\n\
echo ""\n\
echo "========================================"\n\
echo "服务已启动!"\n\
echo "========================================"\n\
echo "访问方式:"\n\
echo "  - 浏览器: http://localhost:6080"\n\
echo "  - VNC客户端: localhost:5900"\n\
echo ""\n\
echo "数据库连接 (Easy Connect):"\n\
echo "  格式: host:port/service_name"\n\
echo "  示例: 192.168.1.100:1521/ORCL"\n\
echo "========================================"\n\
echo ""\n\
\n\
# 启动应用\n\
cd /app && python3 main.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# 创建 VNC 配置
RUN mkdir -p /root/.vnc && \
    echo "" > /root/.vnc/passwd && \
    chmod 600 /root/.vnc/passwd

# 创建日志和数据目录
RUN mkdir -p /app/logs /app/data /app/backups

# 暴露端口
# 6080: noVNC Web 端口 (浏览器访问)
# 5900: VNC 端口 (VNC 客户端访问)
EXPOSE 6080 5900

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:6080/ || exit 1

# 启动命令
CMD ["/app/start.sh"]