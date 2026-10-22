"""帖子接口（预留范例：公开分页只读接口）。

本文件演示「无需登录的只读接口」写法：列表分页 + 单篇详情，
后续发帖、回帖列表等接口都可以照这个结构补在自己新建的模块里。
"""
import re

from flask import Blueprint

from db import paginate, query_one
from utils.params import parse_page_args
from utils.response import (
    CODE_NOT_FOUND,
    CODE_SUCCESS,
    format_datetime,
    make_page_response,
    make_response,
)

bp = Blueprint("posts", __name__, url_prefix="/api")

# 列表里的正文只取前 400 个字符：够生成卡片摘要即可，不把整篇正文塞进列表响应
LIST_SQL = (
    "SELECT p.id, p.user_id, p.title, p.cover, "
    "LEFT(p.content, 400) AS content_raw, "
    "p.view_count, p.like_count, p.reply_count, p.create_time, "
    "u.nickname AS author_nickname, u.avatar AS author_avatar "
    "FROM posts p JOIN users u ON u.id = p.user_id "
    "WHERE p.status=1 ORDER BY p.create_time DESC, p.id DESC"
)
COUNT_SQL = "SELECT COUNT(*) AS total FROM posts p WHERE p.status=1"

# 卡片摘要最大长度（前端卡片最多显示两行）
EXCERPT_MAX_LENGTH = 120

# 详情比列表多取 content（正文），列表里不带正文，避免列表响应过大
DETAIL_SQL = (
    "SELECT p.id, p.user_id, p.title, p.content, p.cover, "
    "p.view_count, p.like_count, p.reply_count, p.create_time, "
    "u.nickname AS author_nickname, u.avatar AS author_avatar "
    "FROM posts p JOIN users u ON u.id = p.user_id "
    "WHERE p.id=%s AND p.status=1"
)


def _make_excerpt(html, max_length=EXCERPT_MAX_LENGTH):
    """把正文 HTML 转成卡片用的纯文本摘要。

    因为正文是按字符截取后再处理的，末尾可能残留半截标签，
    所以标签正则里的 ">" 是可选的，连同不完整标签一起清掉。
    """
    if not html:
        return ""

    text = re.sub(r"<[^>]*>?", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_length] + "…" if len(text) > max_length else text


@bp.get("/posts")
def list_posts():
    """帖子分页列表：GET /api/posts?page=1&page_size=10"""
    page, page_size = parse_page_args()
    items, total = paginate(COUNT_SQL, LIST_SQL, page=page, page_size=page_size)

    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["excerpt"] = _make_excerpt(item.pop("content_raw"))

    return make_page_response(items, total, page, page_size)


@bp.get("/posts/<int:post_id>")
def get_post(post_id):
    """帖子详情：GET /api/posts/1（不存在或未发布返回 1009）"""
    item = query_one(DETAIL_SQL, (post_id,))
    if item is None:
        return make_response(CODE_NOT_FOUND, "帖子不存在")

    item["create_time"] = format_datetime(item["create_time"])
    return make_response(CODE_SUCCESS, "获取成功", item)