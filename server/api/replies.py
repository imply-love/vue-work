"""评论（回帖）接口：帖子详情下的评论区。

- GET  /api/posts/<post_id>/replies   评论列表（公开，按时间正序分页）
- POST /api/posts/<post_id>/replies   发表评论（需登录：管理员与普通用户均可）
"""
from flask import Blueprint, g

from db import execute, paginate, query_one
from utils.auth import login_required
from utils.params import clean, get_body, parse_page_args, require
from utils.response import (
    CODE_NOT_FOUND,
    CODE_PARAM_ERROR,
    CODE_SUCCESS,
    format_datetime,
    make_page_response,
    make_response,
)

bp = Blueprint("replies", __name__, url_prefix="/api")

# 评论正文上限（与回帖表 TEXT 列匹配，超长直接 1001）
CONTENT_MAX_LENGTH = 500

LIST_SELECT = (
    "SELECT r.id, r.user_id, r.post_id, r.content, r.like_count, r.create_time, "
    "u.nickname AS author_nickname, u.avatar AS author_avatar "
    "FROM replies r JOIN users u ON u.id = r.user_id"
)
COUNT_SQL = "SELECT COUNT(*) AS total FROM replies r WHERE r.post_id=%s"


def _check_publishable_post(post_id):
    """帖子存在且已发布才允许评论，否则返回错误响应；通过返回 None。"""
    post = query_one(
        "SELECT id, status FROM posts WHERE id=%s",
        (post_id,),
    )
    if post is None or post["status"] != 1:
        return make_response(CODE_NOT_FOUND, "帖子不存在或未发布")
    return None


@bp.get("/posts/<int:post_id>/replies")
def list_replies(post_id):
    """评论列表：GET /api/posts/1/replies?page=1&page_size=20（按时间正序）"""
    err = _check_publishable_post(post_id)
    if err is not None:
        return err

    page, page_size = parse_page_args()
    list_sql = (
        LIST_SELECT + " WHERE r.post_id=%s ORDER BY r.create_time ASC, r.id ASC"
    )
    items, total = paginate(COUNT_SQL, list_sql, (post_id,), page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
    return make_page_response(items, total, page, page_size)


@bp.post("/posts/<int:post_id>/replies")
@login_required
def create_reply(post_id):
    """发表评论：POST /api/posts/1/replies，body {content}

    评论后 posts.reply_count +1；content 必填，最长 500 字。
    """
    err = _check_publishable_post(post_id)
    if err is not None:
        return err

    body = get_body()
    content = clean(body.get("content"))

    missing = require(body, "content")
    if missing:
        return make_response(CODE_PARAM_ERROR, f"缺少必填参数：{'、'.join(missing)}")
    if len(content) > CONTENT_MAX_LENGTH:
        return make_response(
            CODE_PARAM_ERROR, f"评论长度不能超过 {CONTENT_MAX_LENGTH} 字"
        )

    user_id = g.current_user["id"]
    reply_id = execute(
        "INSERT INTO replies (post_id, user_id, content) VALUES (%s, %s, %s)",
        (post_id, user_id, content),
    )
    execute("UPDATE posts SET reply_count=reply_count+1 WHERE id=%s", (post_id,))

    row = query_one(
        "SELECT r.id, r.user_id, r.post_id, r.content, r.like_count, r.create_time, "
        "u.nickname AS author_nickname, u.avatar AS author_avatar "
        "FROM replies r JOIN users u ON u.id=r.user_id WHERE r.id=%s",
        (reply_id,),
    )
    row["create_time"] = format_datetime(row["create_time"])
    return make_response(CODE_SUCCESS, "评论发表成功", row)
