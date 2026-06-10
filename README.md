# 本地数据库查询助手 Skill

这是一个通用的 Codex Skill，用于安全检查、查询和分析本地数据库或用户自行配置的只读 MySQL 数据库。它适合用于本地数据分析、应用导出库排查、SQLite 文件检查、MySQL 只读查询和结果总结。

本项目不包含任何公司内部资料、真实数据库地址、账号密码或业务字段。使用者需要按自己的环境进行配置。

## 功能特点

- 支持 SQLite 数据库文件的只读 schema 检查和 SQL 查询。
- 支持通过 profile 配置 MySQL 只读连接。
- 默认拦截常见写操作，降低误删、误改、误迁移风险。
- 查询结果以 JSON 输出，便于 AI 助手进一步总结。
- 提供敏感数据、生产环境和大批量导出场景的安全处理建议。

## 目录结构

```text
local-db-query-assistant/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── database_profiles.md
│   ├── mysql_profiles.example.json
│   └── query_safety.md
└── scripts/
    ├── mysql_readonly.py
    └── sqlite_readonly.py
```

## 安装方式

将本目录复制到 Codex 可发现的 skills 目录中，例如：

```text
~/.codex/skills/local-db-query-assistant
```

之后即可在 Codex 中通过 `$local-db-query-assistant` 调用。

## SQLite 使用

SQLite 无需额外配置，只需要提供本地数据库文件路径。

查看 schema：

```bash
python scripts/sqlite_readonly.py --db path/to/database.db --schema
```

查看 schema 并采样少量数据：

```bash
python scripts/sqlite_readonly.py --db path/to/database.db --schema --sample-rows 3
```

执行只读查询：

```bash
python scripts/sqlite_readonly.py --db path/to/database.db --query "SELECT status, COUNT(*) AS n FROM orders GROUP BY status LIMIT 20"
```

## MySQL 配置

MySQL 使用 profile 管理连接信息。先复制示例文件：

```bash
cp references/mysql_profiles.example.json references/mysql_profiles.json
```

然后把 `references/mysql_profiles.json` 改成自己的数据库配置：

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

不要把密码写入配置文件。运行查询前通过环境变量传入密码：

Windows PowerShell：

```powershell
$env:DB_QUERY_ASSISTANT_PASSWORD = "your_password"
```

macOS/Linux：

```bash
export DB_QUERY_ASSISTANT_PASSWORD="your_password"
```

查看已配置 profile：

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

执行只读查询：

```bash
python scripts/mysql_readonly.py --profile demo --query "SELECT status, COUNT(*) AS n FROM orders GROUP BY status"
```

如果不同数据库使用不同密码环境变量，可以指定 `--password-env`：

```bash
python scripts/mysql_readonly.py --profile demo --password-env DEMO_DB_PASSWORD --schema
```

## 安全约束

- 默认只读，不主动执行写入、删除、建表、改表、迁移等操作。
- 推荐使用只读数据库账号。
- 不在回答中输出密码、token、完整连接串或 `.env` 文件内容。
- 连接生产、远程、共享或客户数据环境前，应先确认。
- 探索大表时先查 schema、小样本和聚合结果，避免无意义全表扫描。
- 涉及用户、客户、订单、支付、健康、员工等敏感数据时，优先返回聚合统计。

## 适用场景

- 分析本地 SQLite 数据库文件。
- 检查应用导出的数据库快照。
- 对 MySQL 只读库进行 schema 探查。
- 根据数据查询结果生成中文分析摘要。
- 为 AI 助手提供可复用、可审计的数据库查询流程。

## 注意事项

本项目是通用 Skill 模板，不内置任何真实数据库连接。使用前必须根据自己的环境配置 profile，并确保遵守所在组织的数据安全要求。
