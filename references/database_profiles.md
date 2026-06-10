# 数据库 Profile 配置说明

本文件用于说明如何配置 MySQL profile。请不要在这里写入真实密码。

## 配置步骤

1. 将 `references/mysql_profiles.example.json` 复制为 `references/mysql_profiles.json`。
2. 按照自己的环境填写 profile 信息。
3. 确保账号具备只读权限。
4. 查询前通过环境变量传入密码。

## 字段说明

| 字段 | 说明 |
| --- | --- |
| `label` | 给人看的名称，例如“本地演示库” |
| `host` | 数据库主机，例如 `127.0.0.1` |
| `port` | 数据库端口，MySQL 默认 `3306` |
| `database` | 默认连接的数据库名 |
| `user` | 数据库用户名，推荐只读账号 |

## 示例

```json
{
  "demo": {
    "label": "演示数据库",
    "host": "127.0.0.1",
    "port": 3306,
    "database": "demo_db",
    "user": "readonly_user"
  },
  "analytics-snapshot": {
    "label": "分析快照库",
    "host": "localhost",
    "port": 3306,
    "database": "analytics_snapshot",
    "user": "analytics_readonly"
  }
}
```

## 使用建议

- profile 名使用小写字母、数字和连字符，例如 `demo`、`local-analytics`。
- 不同环境使用不同 profile，避免误连。
- 生产环境或共享数据库建议在 `label` 中明确标注，并在查询前让用户确认。
- 如每个 profile 使用不同密码，可在运行脚本时传入不同的 `--password-env`。
