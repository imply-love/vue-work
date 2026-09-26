"""初始化数据库：创建 yunmo 库并建表。

用法（在 server 目录下）：
    python init_db.py
"""
from pathlib import Path

import pymysql

from config import Config

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_FILE = BASE_DIR / "sql" / "schema.sql"


def load_statements():
    """读取 schema.sql 并按分号切分成可逐条执行的语句。"""
    sql_text = SCHEMA_FILE.read_text(encoding="utf-8")
    lines = [
        line for line in sql_text.splitlines()
        if line.strip() and not line.strip().startswith("--")
    ]
    return [stmt.strip() for stmt in "\n".join(lines).split(";") if stmt.strip()]


def main():
    if not SCHEMA_FILE.exists():
        raise SystemExit(f"未找到建表脚本：{SCHEMA_FILE}")

    # 此时 yunmo 库可能还不存在，因此连接时不指定 database
    conn = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        charset=Config.DB_CHARSET,
        autocommit=True,
    )
    try:
        with conn.cursor() as cursor:
            for statement in load_statements():
                cursor.execute(statement)
                print(f"  已执行：{statement.splitlines()[0][:60]}...")
    finally:
        conn.close()

    print(f"数据库初始化完成：{Config.DB_NAME} @ {Config.DB_HOST}:{Config.DB_PORT}")


if __name__ == "__main__":
    main()