"""收藏接口：支撑个人中心的「我的收藏」功能。

- POST   /api/favorites          收藏帖子（需登录，body {post_id}）
- DELETE /api/favorites/<post_id> 取消收藏（需登录）
- GET    /api/favorites          我的收藏列表（需登录，分页）
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

bp = Blueprint("favorites", __name__, url_prefix="/api")

# 收藏列表带帖子信息：只展示已发布的帖子（草稿不会出现在收藏列表）
FAVORITE_LIST_SQL = (
    "SELECT f.id AS favorite_id, f.post_id, f.create_time AS favorite_time, "
    "p.title, p.cover, p.tags, p.summary, p.category, p.status, "
    "LEFT(p.content, 400) AS content_raw, "
    "p.view_count, p.like_count, p.reply_count, p.create_time, "
    "u.nickname AS author_nickname, u.avatar AS author_avatar "
    "FROM favorites f "
    "JOIN posts p ON p.id = f.post_id "
    "JOIN users u ON u.id = p.user_id "
    "WHERE f.user_id=%s AND p.status=1 "
    "ORDER BY f.create_time DESC, f.id DESC"
)
FAVORITE_COUNT_SQL = (
    "SELECT COUNT(*) AS total FROM favorites f JOIN posts p ON p.id=f.post_id "
    "WHERE f.user_id=%s AND p.status=1"
)

# 详情页展示收藏状态用：查单条收藏记录
FAVORITE_EXIST_SQL = (
    "SELECT id FROM favorites WHERE user_id=%s AND post_id=%s"
)


def format_favorite_item(item):
    """格式化收藏列表项：时间字符串 + 正文转摘要。"""
    item["favorite_time"] = format_datetime(item.pop("favorite_time"))
    item["create_time"] = format_datetime(item["create_time"])
    if item.get("content_raw"):
        text = item["content_raw"].replace("\n", " ")
        item["excerpt"] = text[:120] + ("…" if len(text) > 120 else "")
    else:
        item["excerpt"] = ""
    item.pop("content_raw", None)
    return item


@bp.get("/favorites")
@login_required
def list_favorites():
    """我的收藏列表：GET /api/favorites?page=1&page_size=10"""
    user_id = g.current_user["id"]
    page, page_size = parse_page_args()
    items, total = paginate(
        FAVORITE_COUNT_SQL,
        FAVORITE_LIST_SQL,
        (user_id,),
        page=page,
        page_size=page_size,
    )
    items = [format_favorite_item(item) for item in items]
    return make_page_response(items, total, page, page_size)


@bp.post("/favorites")
@login_required
def add_favorite():
    """收藏帖子：POST /api/favorites，body {post_id}

    仅可收藏已发布的帖子；重复收藏直接返回成功（幂等）。
    """
    user_id = g.current_user["id"]
    body = get_body()
    post_id = clean(body.get("post_id"))

    missing = require(body, "post_id")
    if missing:
        return make_response(CODE_PARAM_ERROR, f"缺少必填参数：{'、'.join(missing)}")
    if not post_id.isdigit():
        return make_response(CODE_PARAM_ERROR, "post_id 需为数字")

    post_id = int(post_id)
    post = query_one(
        "SELECT id FROM posts WHERE id=%s AND status=1",
        (post_id,),
    )
    if post is None:
        return make_response(CODE_NOT_FOUND, "帖子不存在或未发布")

    # 幂等：已收藏则直接返回成功，不重复插入
    existed = query_one(FAVORITE_EXIST_SQL, (user_id, post_id))
    if existed:
        return make_response(CODE_SUCCESS, "已收藏", {"post_id": post_id})

    execute(
        "INSERT INTO favorites (user_id, post_id) VALUES (%s, %s)",
        (user_id, post_id),
    )
    return make_response(CODE_SUCCESS, "收藏成功", {"post_id": post_id})


@bp.delete("/favorites/<int:post_id>")
@login_required
def remove_favorite(post_id):
    """取消收藏：DELETE /api/favorites/1（未收藏也返回成功，幂等）"""
    user_id = g.current_user["id"]
    execute(
        "DELETE FROM favorites WHERE user_id=%s AND post_id=%s",
        (user_id, post_id),
    )
    return make_response(CODE_SUCCESS, "已取消收藏", {"post_id": post_id})
