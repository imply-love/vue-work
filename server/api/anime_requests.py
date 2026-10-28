"""求番接口：支撑番剧库板块的求番功能。

- GET /api/anime-requests：公开分页列表，游客也可浏览（封禁的求番不展示）
- POST /api/anime-requests：需登录，管理员与普通用户均可发起求番

每次求番都会给所有管理员写入一条站内通知，提示尽快收录。
"""
from flask import Blueprint, g

from db import execute, paginate, query_one
from utils.auth import login_required
from utils.params import clean, get_body, parse_page_args, require
from utils.response import (
    CODE_PARAM_ERROR,
    CODE_SUCCESS,
    format_datetime,
    make_page_response,
    make_response,
)

bp = Blueprint("anime_requests", __name__, url_prefix="/api")

# 与 anime_requests 表字段长度保持一致，超长直接返回 1001
ANIME_NAME_MAX_LENGTH = 100
REASON_MAX_LENGTH = 5000

LIST_SQL = (
    "SELECT r.id, r.user_id, r.anime_name, r.reason, r.status, r.review_status, "
    "r.review_note, r.create_time, "
    "u.nickname AS author_nickname, u.avatar AS author_avatar "
    "FROM anime_requests r JOIN users u ON u.id = r.user_id "
    "WHERE r.review_status<>3 "
    "ORDER BY r.create_time DESC, r.id DESC"
)
COUNT_SQL = "SELECT COUNT(*) AS total FROM anime_requests r WHERE r.review_status<>3"


@bp.get("/anime-requests")
def list_anime_requests():
    """求番分页列表：GET /api/anime-requests?page=1&page_size=10"""
    page, page_size = parse_page_args()
    items, total = paginate(COUNT_SQL, LIST_SQL, page=page, page_size=page_size)

    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["review_note"] = item["review_note"] or ""

    return make_page_response(items, total, page, page_size)


@bp.post("/anime-requests")
@login_required
def create_anime_request():
    """发起求番：POST /api/anime-requests，body {anime_name, reason?}

    需登录：管理员与普通用户均可发起，未登录返回 1007。
    提交后通知所有管理员尽快收录。
    """
    user_id = g.current_user["id"]
    body = get_body()
    anime_name = clean(body.get("anime_name"))
    reason = clean(body.get("reason"))

    missing = require(body, "anime_name")
    if missing:
        return make_response(CODE_PARAM_ERROR, f"缺少必填参数：{'、'.join(missing)}")

    if len(anime_name) > ANIME_NAME_MAX_LENGTH:
        return make_response(
            CODE_PARAM_ERROR, f"番剧名称长度不能超过 {ANIME_NAME_MAX_LENGTH} 位"
        )
    if len(reason) > REASON_MAX_LENGTH:
        return make_response(
            CODE_PARAM_ERROR, f"求番理由长度不能超过 {REASON_MAX_LENGTH} 字"
        )

    request_id = execute(
        "INSERT INTO anime_requests (user_id, anime_name, reason) VALUES (%s, %s, %s)",
        (user_id, anime_name, reason),
    )

    # 对所有管理员发出通知，请求尽快收录
    user = query_one("SELECT nickname, username FROM users WHERE id=%s", (user_id,))
    author = (user["nickname"] or user["username"]) if user else "有同好"
    execute(
        "INSERT INTO notifications (user_id, type, title, content, link) "
        "SELECT id, 'anime_request', %s, %s, '/admin' FROM users WHERE role=1",
        ("新的求番请求", f"{author} 请求收录《{anime_name}》，请尽快处理"),
    )
    return make_response(CODE_SUCCESS, "求番成功", {"id": request_id})
