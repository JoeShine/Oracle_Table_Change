#!/bin/bash
# Oracle 数据批量修改工具 - 便携版启动脚本 (Linux)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}/App"
DATA_DIR="${SCRIPT_DIR}/Data"

export PATH="${APP_DIR}:${PATH}"
export PYTHONPATH="${APP_DIR}/src"

# 可选Oracle客户端
if [ -d "${SCRIPT_DIR}/OracleClient/instantclient"* ]; then
    export LD_LIBRARY_PATH="${SCRIPT_DIR}/OracleClient:${LD_LIBRARY_PATH}"
fi

echo "正在启动 Oracle 数据批量修改工具..."
cd "${APP_DIR}"
./OracleBatchUpdater
