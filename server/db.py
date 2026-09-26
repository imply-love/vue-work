"""数据层：请求级连接复用与 SQL 执行封装。

约定：所有 SQL 一律使用 %s 占位符 + 参数化传入，禁止字符串拼接。
"""
import pymysql
from flask import g

from config import Config

_CONN_KEY = "_db_conn"


def get_conn():
    """获取当前请求的数据库连接，首次调用时建立并缓存到 flask.g。"""
    if not hasattr(g, _CONN_KEY):
        setattr(g, _CONN_KEY, pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset=Config.DB_CHARSET,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        ))
    return getattr(g, _CONN_KEY)


def close_db(exc=None):
    """请求结束时关闭连接，注册到 app.teardown_appcontext。"""
    conn = g.pop(_CONN_KEY, None)
    if conn is not None:
        conn.close()


def query_one(sql, args=None):
    """执行查询，返回单行 dict；无结果返回 None。"""
    with get_conn().cursor() as cursor:
        cursor.execute(sql, args)
        return cursor.fetchone()


def query_all(sql, args=None):
    """执行查询，返回 list[dict]。"""
    with get_conn().cursor() as cursor:
        cursor.execute(sql, args)
        return cursor.fetchall()


def execute(sql, args=None):
    """执行写操作并提交，返回自增主键（非自增写入时为影响行数）。"""
    conn = get_conn()
    with conn.cursor() as cursor:
        cursor.execute(sql, args)
        conn.commit()
        return cursor.lastrowid


def paginate(sql_count, sql_list, args=None, page=1, page_size=10):
    """通用分页查询。

    :param sql_count: 统计总数的 SQL，例如 "SELECT COUNT(*) AS total FROM posts WHERE status=1"
    :param sql_list: 查询列表的 SQL，**不要自带 LIMIT**，由本函数拼接
    :return: (items, total)
    """
    args = tuple(args or ())
    row = query_one(sql_count, args)
    total = int(row["total"]) if row else 0

    items = []
    if total > 0:
        offset = (page - 1) * page_size
        items = query_all(sql_list + " LIMIT %s OFFSET %s", args + (page_size, offset))
    return items, total