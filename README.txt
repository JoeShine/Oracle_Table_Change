# v2.9.1
DBForge (Database Forge) - 使用说明
版本: v2.9.0（多数据库支持版）

一、系统要求
------------
1. Windows 7 或更高版本
2. Windows Server 2008 R2 / 2012 / 2012 R2 / 2016 / 2019 / 2022
3. 无需安装 Python 环境（如果使用打包后的 exe）

支持数据库清单：
  [1] Oracle        11g / 12c / 19c / 21c
  [2] MySQL         5.7+ / 8.0+ / MariaDB 10.x
  [3] MS SQL Server 2008 R2 / 2012+ / 2016 / 2019 / 2022

二、快速开始
------------
方式一：使用源码
1. 安装 Python 3.8+
2. 运行 install.bat 安装依赖（或 `pip install -r requirements.txt`）
3. 额外安装多数据库驱动：`pip install pymysql pyodbc`
4. 运行 python main.py 启动程序

方式二：使用打包 exe
1. 运行 build.bat 打包程序
2. 找到 dist\DBForge.exe
3. 直接运行 exe 文件

三、使用流程
------------
1. 配置连接管理
   - 点击 "添加连接" 按钮
   - 选择数据库类型（Oracle / MySQL / SQL Server）
   - 填写连接信息：主机地址、端口、服务名/数据库名、用户名、密码
   - 点击 "测试连接" 验证连接
   - 保存连接信息

2. 准备 Excel 数据
   - 第一列：唯一标识列（如：USER_ID）
   - 第二列：待修改数据列（如：EMAIL）
   - 确保有表头
   - 示例：
     | USER_ID | EMAIL              |
     |---------|--------------------|
     | 1001    | test1@example.com  |
     | 1002    | test2@example.com  |

3. 配置更新参数
   - 选择已保存的连接管理
   - 输入目标表名（如：USER_INFO）
   - 输入唯一标识列名（如：USER_ID）
   - 输入待修改列名（如：EMAIL）
   - 选择 Excel 文件
   - 点击 "预览" 查看 Excel 数据

4. 执行更新
   - 点击 "开始更新"
   - 系统自动执行（SQL 方言随数据库类型自动切换）：
     a. 备份目标表（带时间戳）
     b. 创建临时表
     c. 导入 Excel 数据
     d. 执行数据更新（MERGE / ON DUPLICATE KEY UPDATE 等方言）
   - 查看运行日志
   - 导出失败记录（如有）

四、功能说明
------------
1. 连接管理管理
   - 支持添加、删除多个连接管理
   - 连接信息保存在 config.json
   - 支持测试连接功能
   - 支持数据库类型选择（Oracle / MySQL / SQL Server）

2. 数据备份
   - 更新前自动备份目标表
   - 备份表命名：原表名_BAK_YYYYMMDD_HHMMSS
   - 备份保存在对应 Schema / Database 下

3. 临时表
   - 自动创建临时表存储 Excel 数据
   - 临时表命名：TEMP_UPDATE_YYYYMMDD_HHMMSS
   - 操作完成后自动清理

4. 日志管理
   - 实时显示运行日志
   - 支持导出日志到 Excel
   - 支持导出失败记录到 Excel

5. 配置保存
   - 自动保存用户最近输入
   - 下次启动自动恢复

五、注意事项
------------
1. Excel 第一列必须是唯一标识列，且不能有重复值
2. 唯一标识列的值必须与目标表中的数据匹配
3. 更新前请确保已备份重要数据
4. 建议在大批量更新前先测试小批量数据
5. 失败记录会在弹窗中显示，并可导出

六、常见问题
------------
Q: 连接失败怎么办？
A: 检查主机地址、端口、服务名/数据库名、用户名、密码是否正确
   - Oracle: 检查 Oracle Instant Client 或 oracledb thin 模式配置
   - MySQL : 检查端口（默认 3306）、用户权限、bind-address
   - SQL Server: 检查端口（默认 1433）、TCP/IP 是否启用、ODBC Driver 17 是否安装

Q: 表或列不存在？
A: 确认目标表和列名拼写正确，注意大小写（Oracle 默认大写，MySQL/Linux 默认区分）

Q: Excel 导入失败？
A: 确保 Excel 格式正确，第一列和第二列都有数据

Q: 数据类型不匹配？
A: 确保 Excel 中的数据格式与目标列类型兼容

七、技术支持
------------
如遇问题，请查看 logs 目录下的日志文件
