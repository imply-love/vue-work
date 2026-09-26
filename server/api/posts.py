"""帖子接口（预留范例：公开分页只读接口）。

本文件演示「无需登录的列表分页接口」写法，后续发帖、帖子详情、回帖列表等
接口都可以照这个结构补在自己新建的模块里。
"""
from flask import Blueprint

from db import paginate
from utils.params import parse_page_args
from utils.response import format_datetime, make_page_response

bp = Blueprint("posts", __name__, url_prefix="/api")

LIST_SQL = (
    "SELECT p.id, p.user_id, p.title, p.cover, "
    "p.view_count, p.like_count, p.reply_count, p.create_time, "
    "u.nickname AS author_nickname, u.avatar AS author_avatar "
    "FROM posts p JOIN users u ON u.id = p.user_id "
    "WHERE p.status=1 ORDER BY p.create_time DESC, p.id DESC"
)
COUNT_SQL = "SELECT COUNT(*) AS total FROM posts p WHERE p.status=1"


@bp.get("/posts")
def list_posts():
    """帖子分页列表：GET /api/posts?page=1&page_size=10"""
    page, page_size = parse_page_args()
    items, total = paginate(COUNT_SQL, LIST_SQL, page=page, page_size=page_size)

    for item in items:
        item["create_time"] = format_datetime(item["create_time"])

    return make_page_response(items, total, page, page_size)