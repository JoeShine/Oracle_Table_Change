#!/bin/bash
# Oracle Instant Client 安装脚本
# 用于 Docker 构建前准备 Oracle Instant Client（仅需Basic包，无需配置文件）

set -e

echo "========================================"
echo "Oracle Instant Client 安装脚本"
echo "========================================"
echo ""
echo "注意: 使用 Easy Connect 方式，无需配置文件"
echo "连接字符串格式: host:port/service_name"
echo ""

ORACLE_VERSION="21.15.0.0.0"
ORACLE_ZIP="instantclient-basic-linux.x64-${ORACLE_VERSION}dbru.zip"
ORACLE_DIR="instantclient_21_15"
TARGET_DIR="/opt/oracle"

# 检查是否已有zip文件
if [ -f "$ORACLE_ZIP" ]; then
    echo "发现已下载的Oracle Instant Client: $ORACLE_ZIP"
else
    echo ""
    echo "请从Oracle官网下载Instant Client Basic包:"
    echo "  https://www.oracle.com/database/technologies/instant-client/downloads.html"
    echo ""
    echo "下载后，将文件放到当前目录:"
    echo "  $ORACLE_ZIP"
    echo ""
    echo "注意: 只需要 Basic 包，无需配置文件（tnsnames.ora等）"
    echo ""
    exit 1
fi

# 解压
echo "解压Oracle Instant Client..."
mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"
unzip -o "../$ORACLE_ZIP"

# 配置库路径
echo "配置库路径..."
echo "$TARGET_DIR/$ORACLE_DIR" | sudo tee /etc/ld.so.conf.d/oracle-instantclient.conf
sudo ldconfig

echo ""
echo "========================================"
echo "Oracle Instant Client 安装完成!"
echo "========================================"
echo ""
echo "安装位置: $TARGET_DIR/$ORACLE_DIR"
echo ""
echo "环境变量设置:"
echo "  export LD_LIBRARY_PATH=$TARGET_DIR/$ORACLE_DIR:\$LD_LIBRARY_PATH"
echo ""
echo "连接方式: Easy Connect"
echo "连接字符串格式: host:port/service_name"
echo "示例: 192.168.1.100:1521/ORCL"
echo ""
echo "无需配置 tnsnames.ora 等文件!"
echo ""