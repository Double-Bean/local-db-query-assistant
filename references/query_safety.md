# 查询安全参考

## 安全检查清单

- 默认把本地数据库、导出数据和业务快照视为私有数据。
- 优先使用只读连接模式、只读账号或只读事务。
- 涉及写入、迁移、批量导出、生产环境、共享环境或客户数据时，先向用户确认。
- 不在回答中暴露密码、token、完整 DSN、完整 `.env` 内容或内部密钥。
- 涉及用户、客户、订单、支付、健康、员工等敏感数据时，优先返回聚合结果。
- 探索表结构时加 `LIMIT`；只有聚合查询或用户明确需要完整结果时才考虑去掉限制。

## Schema 探查模式

SQLite:

```sql
SELECT name, type
FROM sqlite_master
WHERE type IN ('table', 'view')
ORDER BY type, name;
```

```sql
PRAGMA table_info(table_name);
```

MySQL:

```sql
SELECT table_name, table_type, table_rows
FROM information_schema.tables
WHERE table_schema = DATABASE()
ORDER BY table_name;
```

```sql
SELECT column_name, data_type, is_nullable, column_key, column_default
FROM information_schema.columns
WHERE table_schema = DATABASE()
  AND table_name = 'table_name'
ORDER BY ordinal_position;
```

PostgreSQL:

```sql
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_schema, table_name;
```

## SQL 习惯

- 使用明确字段列表，避免无目的的 `SELECT *`。
- 给聚合字段和计算字段起清晰别名。
- 时间范围优先写成清晰的闭开区间，例如 `created_at >= '2026-01-01' AND created_at < '2026-02-01'`。
- Top-N 查询必须有稳定排序。
- 大表 join 前先确认 join key、基数和是否会造成重复行。
- 统计人数、订单数、设备数等指标时，确认是否需要 `COUNT(DISTINCT ...)`。

## 需要暂停确认的情况

- 用户要求修改数据或表结构。
- 数据库名、路径、host、profile 名中出现 `prod`、`production`、`live`、`online`、客户名或其他生产环境信号。
- 用户要求导出或打印大量原始个人数据。
- 当前 schema 无法支撑用户问题，需要额外业务口径或字段解释。
- 查询可能长时间运行、锁表或影响共享环境性能。
