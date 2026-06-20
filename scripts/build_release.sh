#!/bin/bash
# DBForge - v2.8.0 发布包构建脚本 (Linux)
# 在当前 Linux 环境中可构建的产物：
#   - Linux x86_64 发行版 tar.gz
#   - Linux 便携版 zip
#   - 用户手册 CHM/EPUB
#   - Excel 导入模板
#   - RELEASE_NOTES
#
# 以下产物需要其他环境构建：
#   - Windows exe / Windows 便携版 zip 需要在 Windows + PyInstaller 环境构建
#   - Docker 镜像 tar.gz 需要 Docker 环境

set -e

VERSION="2.9.0"
APP_NAME="DBForge"
RELEASE_DIR="release_v${VERSION}"
DIST_DIR="dist"

# ------------------------------------------------------------------
# 依赖说明（多数据库支持：Oracle / MySQL / SQL Server）
# ------------------------------------------------------------------
# 如需使用源码模式或开发模式，请安装以下 Python 依赖：
#   pip install oracledb pandas openpyxl pymysql pyodbc
#
# 其中：
#   - oracledb  : Oracle 数据库驱动（支持 Oracle 11g/12c/19c/21c）
#   - pymysql   : MySQL 数据库驱动（支持 MySQL 5.7+/8.0+，MariaDB 10.x）
#   - pyodbc    : SQL Server 数据库驱动（支持 SQL Server 2008 R2/2012+/2016/2019/2022）
#   - pandas    : Excel/CSV 数据处理
#   - openpyxl  : Excel .xlsx 文件读写
#
# 注意：pyodbc 在 Linux 上需要系统级 unixODBC 开发库：
#   Debian/Ubuntu: apt-get install unixodbc unixodbc-dev
#   CentOS/RHEL:   yum install unixODBC unixODBC-devel
#
# SQL Server 在 Linux 上需要额外安装 Microsoft ODBC Driver 17 for SQL Server。
# ------------------------------------------------------------------

echo "========================================"
echo "构建 DBForge v${VERSION} 发布包"
echo "========================================"
echo ""

# 创建发布目录
mkdir -p "${RELEASE_DIR}"

# ------------------------------------------------------------------
# 1. Linux x86_64 发行版 tar.gz
# ------------------------------------------------------------------
echo "[1/5] 构建 Linux x86_64 发行版..."
LINUX_DIR="${APP_NAME}_v${VERSION}_linux-x86_64"
rm -rf "${LINUX_DIR}"
mkdir -p "${LINUX_DIR}"

# 复制 Linux 可执行文件
cp "${DIST_DIR}/${APP_NAME}" "${LINUX_DIR}/"
chmod +x "${LINUX_DIR}/${APP_NAME}"

# 复制源码（便于调试和二次开发）
mkdir -p "${LINUX_DIR}/src"
cp src/*.py "${LINUX_DIR}/src/"
cp src/service/__init__.py "${LINUX_DIR}/src/service/" 2>/dev/null || true

# 复制依赖和配置
cp requirements.txt "${LINUX_DIR}/"
cp README.md "${LINUX_DIR}/"
cp RELEASE_NOTES_v${VERSION}.txt "${LINUX_DIR}/RELEASE_NOTES.txt"

# 创建数据目录
mkdir -p "${LINUX_DIR}/logs" "${LINUX_DIR}/backups" "${LINUX_DIR}/data"

# 打包
tar -czf "${RELEASE_DIR}/${LINUX_DIR}.tar.gz" "${LINUX_DIR}"
rm -rf "${LINUX_DIR}"
echo "        -> ${RELEASE_DIR}/${LINUX_DIR}.tar.gz"

# ------------------------------------------------------------------
# 2. Linux 便携版 zip
# ------------------------------------------------------------------
echo "[2/5] 构建 Linux 便携版..."
PORTABLE_DIR="${APP_NAME}_Portable_v${VERSION}"
rm -rf "${PORTABLE_DIR}"
mkdir -p "${PORTABLE_DIR}/App/src/service"
mkdir -p "${PORTABLE_DIR}/Data/logs"
mkdir -p "${PORTABLE_DIR}/Data/backups"
mkdir -p "${PORTABLE_DIR}/Data/config"
mkdir -p "${PORTABLE_DIR}/OracleClient"

# 复制应用文件
cp "${DIST_DIR}/${APP_NAME}" "${PORTABLE_DIR}/App/"
chmod +x "${PORTABLE_DIR}/App/${APP_NAME}"
cp src/*.py "${PORTABLE_DIR}/App/src/"
cp src/service/__init__.py "${PORTABLE_DIR}/App/src/service/" 2>/dev/null || true
cp requirements.txt "${PORTABLE_DIR}/App/"

# 复制模板
cp "DBForge_导入模板.xlsx" "${PORTABLE_DIR}/Data/" 2>/dev/null || true

# 创建 Linux 启动脚本
cat > "${PORTABLE_DIR}/${APP_NAME}_Portable.sh" << 'EOF'
#!/bin/bash
# DBForge - Linux 便携版启动脚本

set -e

APP_DIR="$(cd "$(dirname "$0")/App" && pwd)"
DATA_DIR="$(cd "$(dirname "$0")/Data" && pwd)"

export PYTHONPATH="${APP_DIR}/src:${PYTHONPATH}"

# 如有 Oracle Instant Client 则加入库路径
ORACLE_CLIENT_DIR="$(cd "$(dirname "$0")/OracleClient" && pwd)"
if [ -d "${ORACLE_CLIENT_DIR}" ] && [ "$(ls -A ${ORACLE_CLIENT_DIR}/*.so* 2>/dev/null)" ]; then
    export LD_LIBRARY_PATH="${ORACLE_CLIENT_DIR}:${LD_LIBRARY_PATH}"
fi

cd "${APP_DIR}"

# 优先使用 PyInstaller 打包的可执行文件
if [ -x "${APP_DIR}/DBForge" ]; then
    echo "正在启动 DBForge (可执行文件模式)..."
    ./DBForge "$@"
else
    echo "正在启动 DBForge (Python 源码模式)..."
    python3 "${APP_DIR}/src/main.py" "$@"
fi
EOF
chmod +x "${PORTABLE_DIR}/${APP_NAME}_Portable.sh"

# 创建配置文件模板
cat > "${PORTABLE_DIR}/Data/config/config.json.template" << 'EOF'
{
    "connections": [],
    "templates": [],
    "last_used": {
        "connection_name": "",
        "target_table": "",
        "key_column": "",
        "update_column": "",
        "schema": "APPS",
        "temp_schema": "APPS",
        "theme_style": "terminal",
        "theme_dark": false
    },
    "settings": {
        "log_level": "INFO",
        "backup_enabled": true,
        "max_backup_count": 10
    }
}
EOF

# 创建使用说明
cat > "${PORTABLE_DIR}/README_Portable.txt" << EOF
========================================
DBForge - Linux 便携版
版本: ${VERSION}
========================================

【使用说明】

1. 解压即用
   - 无需安装 Python，解压到任意目录即可运行
   - 已包含 Linux x86_64 可执行文件

2. 启动方式
   - 运行 ./${APP_NAME}_Portable.sh（推荐）
   - 或直接运行 App/${APP_NAME}

3. 数据存储
   - 所有数据保存在 Data 目录
   - logs: 运行日志
   - backups: 数据备份
   - config: 配置文件

4. Oracle 客户端
   - 如需使用 Oracle Instant Client，请将解压后的库文件
     放到 OracleClient 目录中
   - 或配置系统环境 LD_LIBRARY_PATH

5. 系统要求
   - Linux x86_64
   - glibc 2.17 及以上
   - 不需要安装 Python（便携版包含可执行文件）
   - 仅 Oracle Instant Client 需要单独配置

6. 连接数据库
   - 使用 Easy Connect 方式
   - 格式: host:port/service_name
   - 示例: 192.168.1.100:1521/ORCL

========================================
EOF

# 打包便携版
zip -rq "${RELEASE_DIR}/${PORTABLE_DIR}.zip" "${PORTABLE_DIR}"
rm -rf "${PORTABLE_DIR}"
echo "        -> ${RELEASE_DIR}/${PORTABLE_DIR}.zip"

# ------------------------------------------------------------------
# 3. 复制用户手册和模板
# ------------------------------------------------------------------
echo "[3/5] 复制用户手册..."
cp "docs/${APP_NAME}_UserManual.chm" "${RELEASE_DIR}/${APP_NAME}_UserManual_v${VERSION}.chm"
cp "docs/${APP_NAME}_UserManual.epub" "${RELEASE_DIR}/${APP_NAME}_UserManual_v${VERSION}.epub"
echo "        -> ${RELEASE_DIR}/${APP_NAME}_UserManual_v${VERSION}.chm"
echo "        -> ${RELEASE_DIR}/${APP_NAME}_UserManual_v${VERSION}.epub"

echo "[4/5] 复制 Excel 导入模板..."
cp "DBForge_导入模板.xlsx" "${RELEASE_DIR}/DBForge_导入模板_v${VERSION}.xlsx"
echo "        -> ${RELEASE_DIR}/DBForge_导入模板_v${VERSION}.xlsx"

echo "[5/5] 复制 RELEASE_NOTES..."
cp "RELEASE_NOTES_v${VERSION}.txt" "${RELEASE_DIR}/RELEASE_NOTES_v${VERSION}.txt"
echo "        -> ${RELEASE_DIR}/RELEASE_NOTES_v${VERSION}.txt"

echo ""
echo "========================================"
echo "发布包构建完成"
echo "========================================"
echo ""
ls -lh "${RELEASE_DIR}"
echo ""
echo ""
echo "========================================"
echo "多数据库支持说明（v2.9.0）"
echo "========================================"
echo ""
echo "DBForge v2.9.0 支持以下三种主流关系型数据库："
echo ""
echo "  [1] Oracle          11g / 12c / 19c / 21c     - 驱动: oracledb"
echo "  [2] MySQL           5.7 / 8.0 / MariaDB 10.x   - 驱动: pymysql"
echo "  [3] SQL Server      2008 R2 / 2012+ / 2019/2022 - 驱动: pyodbc + MS ODBC Driver 17"
echo ""
echo "核心特性："
echo "  - 自动 SQL 方言适配（根据数据库类型切换 DDL/DML 语句）"
echo "  - 统一的 DB-API 2.0 抽象层（同一套业务逻辑兼容三种数据库）"
echo "  - 连接管理页支持数据库类型选择（Oracle/MySQL/SQL Server）"
echo "  - 批量更新页 SQL 方言自动切换"
echo "  - 原型 demo 支持多数据库交互测试"
echo ""
echo "安装建议："
echo "  - Oracle: 只需 oracledb（纯 Python 实现，不需要 Instant Client 也可运行）"
echo "  - MySQL : 只需 pymysql（纯 Python 实现）"
echo "  - SQL Server: 需要 pyodbc + 系统级 Microsoft ODBC Driver 17 for SQL Server"
echo ""
echo "========================================"
