---
name: local-db-query-assistant
description: 安全检查、查询和分析本地数据库或用户自行配置的只读 MySQL 数据库。适用于 Codex 需要从 SQLite、MySQL、导出的应用数据库、数据分析快照或本地开发库中回答问题时；包含数据库配置引导、schema 探查、只读 SQL 生成、结果总结和敏感信息保护流程。
---

# 本地数据库查询助手

## 核心原则

1. 先确认数据库类型、位置、连接方式和用户要回答的问题。优先使用用户明确给出的本地文件或已配置 profile。
2. 默认只读。除非用户明确要求并确认目标，否则不要运行 `INSERT`、`UPDATE`、`DELETE`、`DROP`、`ALTER`、`CREATE`、`TRUNCATE`、`VACUUM`、迁移脚本或任何会改变数据/结构的命令。
3. 回答分析问题前先探查 schema。只在必要时查看表、字段、索引和少量样例行。
4. SQL 要聚焦：写清楚筛选条件、排序、聚合口径和时间范围；探索型查询必须加 `LIMIT`；避免在大表或敏感表上使用 `SELECT *`。
5. 用用户的语言总结结果。必要时附上 SQL 或查询逻辑，便于复核；不要输出密码、token、完整连接串或大量原始个人信息。
6. 查询失败时，先阅读错误和 schema，再修正 SQL。不要凭空猜字段名或业务逻辑。

## 使用前配置

将本 skill 文件夹放到 Codex 可发现的 skills 目录中，例如：

```text
~/.codex/skills/local-db-query-assistant
```

SQLite 本地文件无需额外配置，只需要知道 `.db`、`.sqlite` 或 `.sqlite3` 文件路径。

MySQL 需要先配置只读 profile：

1. 复制并修改 `references/mysql_profiles.example.json` 为 `references/mysql_profiles.json`。
2. 为每个 profile 填写通用连接信息：`label`、`host`、`port`、`database`、`user`。
3. 不要把密码写入文件。运行查询前通过环境变量传入密码，默认变量名是 `DB_QUERY_ASSISTANT_PASSWORD`。
4. 推荐使用只读数据库账号；如连接生产、共享或客户数据环境，先向用户确认。

示例 profile：

```json
{
  "demo": {
    "label": "演示数据库",
    "host": "127.0.0.1",
    "port": 3306,
    "database": "demo_db",
    "user": "readonly_user"
  }
}
```

Windows PowerShell 设置密码示例：

```powershell
$env:DB_QUERY_ASSISTANT_PASSWORD = "your_password"
```

macOS/Linux 设置密码示例：

```bash
export DB_QUERY_ASSISTANT_PASSWORD="your_password"
```

## SQLite 快速使用

使用 `scripts/sqlite_readonly.py` 查询 SQLite 数据库。脚本会用 SQLite 只读 URI 模式打开文件，拦截常见写操作，并以 JSON 输出结果。

查看 schema：

```bash
python scripts/sqlite_readonly.py --db path/to/database.db --schema
```

查看 schema 并采样少量行：

```bash
python scripts/sqlite_readonly.py --db path/to/database.db --schema --sample-rows 3
```

运行只读查询：

```bash
python scripts/sqlite_readonly.py --db path/to/database.db --query "SELECT status, COUNT(*) AS n FROM orders GROUP BY status LIMIT 20"
```

## MySQL 快速使用

使用 `scripts/mysql_readonly.py` 查询已配置的 MySQL profile。脚本依赖本机可用的 `mysql` 命令行客户端，密码从环境变量读取。

查看可用 profile：

```bash
python scripts/mysql_readonly.py --list-profiles
```

查看表清单：

```bash
python scripts/mysql_readonly.py --profile demo --schema
```

查看字段清单：

```bash
python scripts/mysql_readonly.py --profile demo --columns orders
```

运行只读查询：

```bash
python scripts/mysql_readonly.py --profile demo --query "SELECT status, COUNT(*) AS n FROM orders GROUP BY status"
```

如果密码环境变量不是默认名，使用 `--password-env` 指定：

```bash
python scripts/mysql_readonly.py --profile demo --password-env DEMO_DB_PASSWORD --schema
```

## 其他数据库

对于 PostgreSQL、DuckDB、SQL Server 或其他引擎，优先使用项目现有客户端、只读账号或只读事务。保持以下约束：

- 优先使用只读连接、只读角色或只读事务。
- 不打印完整连接串、密码、token 或 `.env` 文件内容。
- 连接生产、远程、共享或客户数据环境前先确认。
- 在大范围查询前，先做 schema 探查、`EXPLAIN`、小样本查询或聚合查询。
- 遇到敏感数据、陌生表或可能修改数据的请求时，先阅读 `references/query_safety.md`。

## 回答格式

返回查询结果时：

- 先给结论，再给依据。
- 说明使用的数据库、profile 或文件路径，以及涉及的表。
- 说明筛选条件、时间范围、口径、行数限制和关键假设。
- 需要用户复核时附上 SQL。
- 数据不足或 schema 不支持问题时，明确说缺什么，不要硬编答案。
