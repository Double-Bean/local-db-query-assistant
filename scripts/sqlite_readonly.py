#!/usr/bin/env python3
"""以只读方式检查和查询 SQLite 数据库。"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


BLOCKED_PREFIXES = (
    "alter",
    "attach",
    "create",
    "delete",
    "detach",
    "drop",
    "insert",
    "pragma writable_schema",
    "reindex",
    "replace",
    "update",
    "vacuum",
)


def connect_readonly(db_path: str) -> sqlite3.Connection:
    path = Path(db_path).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"数据库不存在: {path}")
    uri = f"file:{path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_sql(sql: str) -> str:
    return " ".join(sql.strip().split()).lower()


def ensure_readonly(sql: str) -> None:
    normalized = normalize_sql(sql).lstrip(" (")
    if not normalized:
        raise SystemExit("查询不能为空。")
    if normalized.startswith(BLOCKED_PREFIXES):
        raise SystemExit("已拦截非只读 SQL。请只使用 SELECT、WITH 或安全 PRAGMA。")
    if ";" in normalized.rstrip(";"):
        raise SystemExit("不允许一次执行多条 SQL。")
    allowed = normalized.startswith(
        ("select", "with", "pragma table_info", "pragma index_list", "pragma index_info")
    )
    if not allowed:
        raise SystemExit("只允许 SELECT、WITH 和安全的 schema PRAGMA。")


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def rows_to_dicts(cursor: sqlite3.Cursor, limit: int) -> list[dict[str, Any]]:
    rows = cursor.fetchmany(limit)
    return [dict(row) for row in rows]


def inspect_schema(conn: sqlite3.Connection, sample_rows: int) -> dict[str, Any]:
    objects = conn.execute(
        """
        SELECT name, type
        FROM sqlite_master
        WHERE type IN ('table', 'view')
          AND name NOT LIKE 'sqlite_%'
        ORDER BY type, name
        """
    ).fetchall()

    result: dict[str, Any] = {"objects": []}
    for item in objects:
        name = item["name"]
        columns = [dict(row) for row in conn.execute(f"PRAGMA table_info({quote_identifier(name)})")]
        indexes = [dict(row) for row in conn.execute(f"PRAGMA index_list({quote_identifier(name)})")]
        entry: dict[str, Any] = {
            "name": name,
            "type": item["type"],
            "columns": columns,
            "indexes": indexes,
        }
        if sample_rows > 0 and item["type"] == "table":
            sample_sql = f"SELECT * FROM {quote_identifier(name)} LIMIT ?"
            entry["sample"] = [dict(row) for row in conn.execute(sample_sql, (sample_rows,))]
        result["objects"].append(entry)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="只读 SQLite schema 检查与查询。")
    parser.add_argument("--db", required=True, help="SQLite 数据库文件路径。")
    parser.add_argument("--schema", action="store_true", help="检查表、字段和索引。")
    parser.add_argument("--sample-rows", type=int, default=0, help="schema 检查时每张表采样 N 行。")
    parser.add_argument("--query", help="要执行的只读 SQL。")
    parser.add_argument("--limit", type=int, default=100, help="查询最多返回的行数。")
    args = parser.parse_args()

    if not args.schema and not args.query:
        raise SystemExit("请传入 --schema、--query 或两者同时传入。")

    conn = connect_readonly(args.db)
    output: dict[str, Any] = {"database": str(Path(args.db).expanduser().resolve())}

    try:
        if args.schema:
            output["schema"] = inspect_schema(conn, max(args.sample_rows, 0))

        if args.query:
            ensure_readonly(args.query)
            cursor = conn.execute(args.query)
            output["query"] = args.query
            output["columns"] = [description[0] for description in cursor.description or []]
            output["rows"] = rows_to_dicts(cursor, max(args.limit, 1))
            output["row_limit"] = max(args.limit, 1)
    finally:
        conn.close()

    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
