#!/usr/bin/env python3
"""使用 mysql 命令行客户端，对已配置 profile 执行只读查询。"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


BLOCKED_WORDS = (
    "alter",
    "call",
    "create",
    "delete",
    "drop",
    "grant",
    "insert",
    "load",
    "lock",
    "replace",
    "revoke",
    "set",
    "truncate",
    "unlock",
    "update",
)


def skill_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def profiles_path() -> Path:
    return skill_dir() / "references" / "mysql_profiles.json"


def load_profiles() -> dict[str, dict[str, Any]]:
    path = profiles_path()
    if not path.exists():
        example = skill_dir() / "references" / "mysql_profiles.example.json"
        raise SystemExit(
            "未找到 references/mysql_profiles.json。"
            f"请复制 {example} 为 {path}，并填写自己的只读数据库连接信息。"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_sql(sql: str) -> str:
    return " ".join(sql.strip().split()).lower()


def ensure_readonly(sql: str) -> None:
    normalized = normalize_sql(sql).lstrip(" (")
    if not normalized:
        raise SystemExit("查询不能为空。")
    if ";" in normalized.rstrip(";"):
        raise SystemExit("不允许一次执行多条 SQL。")
    tokens = normalized.replace("(", " ").replace(")", " ").replace(",", " ").split()
    if any(word in tokens for word in BLOCKED_WORDS):
        raise SystemExit("已拦截非只读 SQL。")
    allowed = normalized.startswith(("select", "with", "show", "describe", "desc", "explain"))
    if not allowed:
        raise SystemExit("只允许 SELECT、WITH、SHOW、DESCRIBE、DESC 和 EXPLAIN。")


def mysql_command(profile: dict[str, Any]) -> list[str]:
    mysql = shutil.which("mysql")
    if not mysql:
        raise SystemExit("未找到 mysql 命令行客户端。请先安装 MySQL Client，或改用项目已有数据库工具。")
    return [
        mysql,
        "--batch",
        "--raw",
        "--default-character-set=utf8mb4",
        "--connect-timeout=10",
        "-h",
        profile["host"],
        "-P",
        str(profile["port"]),
        "-u",
        profile["user"],
        profile["database"],
    ]


def run_mysql(profile: dict[str, Any], sql: str, password_env: str) -> list[dict[str, str]]:
    password = os.environ.get(password_env)
    if not password:
        raise SystemExit(f"请先设置环境变量 {password_env}，不要把密码写入配置文件。")

    env = os.environ.copy()
    env["MYSQL_PWD"] = password
    proc = subprocess.run(
        mysql_command(profile),
        input=sql,
        text=True,
        capture_output=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or "mysql 查询失败。")
    return parse_tsv(proc.stdout)


def parse_tsv(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    if not lines:
        return []
    reader = csv.DictReader(lines, delimiter="\t")
    return [dict(row) for row in reader]


def schema_sql(database: str) -> str:
    escaped = database.replace("'", "''")
    return f"""
SELECT table_name, table_type, table_rows
FROM information_schema.tables
WHERE table_schema = '{escaped}'
ORDER BY table_name
"""


def columns_sql(database: str, table: str) -> str:
    escaped_database = database.replace("'", "''")
    escaped_table = table.replace("'", "''")
    return f"""
SELECT column_name, data_type, is_nullable, column_key, column_default
FROM information_schema.columns
WHERE table_schema = '{escaped_database}'
  AND table_name = '{escaped_table}'
ORDER BY ordinal_position
"""


def public_profile(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "label": profile.get("label"),
        "host": profile.get("host"),
        "port": profile.get("port"),
        "database": profile.get("database"),
        "user": profile.get("user"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="只读 MySQL profile 查询。")
    parser.add_argument("--profile", help="references/mysql_profiles.json 中的 profile 名。")
    parser.add_argument("--list-profiles", action="store_true", help="列出已配置 profile。")
    parser.add_argument("--schema", action="store_true", help="列出所选 profile 的表。")
    parser.add_argument("--columns", help="列出指定表的字段。")
    parser.add_argument("--query", help="要执行的只读 SQL。")
    parser.add_argument("--password-env", default="DB_QUERY_ASSISTANT_PASSWORD", help="保存 MySQL 密码的环境变量名。")
    args = parser.parse_args()

    profiles = load_profiles()

    if args.list_profiles:
        output = {"profiles": {name: public_profile(profile) for name, profile in profiles.items()}}
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    if not args.profile:
        raise SystemExit("请传入 --profile，或使用 --list-profiles 查看可用配置。")
    if args.profile not in profiles:
        available = ", ".join(sorted(profiles))
        raise SystemExit(f"未知 profile: {args.profile}。可用 profile: {available}")

    if not args.schema and not args.columns and not args.query:
        raise SystemExit("请传入 --schema、--columns、--query，或组合使用。")

    profile = profiles[args.profile]
    output: dict[str, Any] = {"profile": args.profile, **public_profile(profile)}

    if args.schema:
        output["schema"] = run_mysql(profile, schema_sql(profile["database"]), args.password_env)

    if args.columns:
        output["columns_table"] = args.columns
        output["columns"] = run_mysql(profile, columns_sql(profile["database"], args.columns), args.password_env)

    if args.query:
        ensure_readonly(args.query)
        output["query"] = args.query
        output["rows"] = run_mysql(profile, args.query, args.password_env)

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
