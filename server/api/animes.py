"""番剧库与番剧推荐接口。

- GET    /api/animes                    番剧库分页列表（公开，支持 q 搜索）
- POST   /api/animes                    管理员新增番剧库内容
- PUT    /api/animes/<id>               管理员修改番剧库内容
- DELETE /api/animes/<id>               管理员删除番剧库内容
- GET    /api/anime-recommendations     番剧推荐分页列表（公开，封禁的推荐不展示）
- POST   /api/anime-recommendations     发起番剧推荐（需登录，番名/链接/推荐理由必填）
"""
import re

from flask import Blueprint, g, request

from db import execute, paginate, query_one
from utils.auth import admin_required, login_required
from utils.params import clean, get_body, parse_page_args, require
from utils.response import (
    CODE_NOT_FOUND,
    CODE_PARAM_ERROR,
    CODE_SUCCESS,
    format_datetime,
    make_page_response,
    make_response,
)

bp = Blueprint("animes", __name__, url_prefix="/api")

TITLE_MAX_LENGTH = 200
CATEGORY_MAX_LENGTH = 30
COVER_MAX_LENGTH = 255
DESCRIPTION_MAX_LENGTH = 5000
LINK_MAX_LENGTH = 500
ANIME_NAME_MAX_LENGTH = 100
REASON_MAX_LENGTH = 5000

LINK_PATTERN = re.compile(r"^https?://\S+$", re.IGNORECASE)

ANIME_SELECT = (
    "SELECT a.id, a.title, a.category, a.cover, a.description, a.link, "
    "a.create_time, a.update_time FROM animes a"
)

RECOMMEND_SELECT = (
    "SELECT r.id, r.user_id, r.anime_name, r.link, r.reason, r.review_status, "
    "r.review_note, r.create_time, u.nickname AS author_nickname, u.avatar AS author_avatar "
    "FROM anime_recommendations r JOIN users u ON u.id = r.user_id"
)


def _validate_anime_body(body, partial=False):
    """校验番剧字段，返回 (payload, 错误响应)。"""
    title = clean(body.get("title"))
    category = clean(body.get("category"))
    cover = clean(body.get("cover"))
    description = clean(body.get("description"))
    link = clean(body.get("link"))

    if not partial and not title:
        return None, make_response(CODE_PARAM_ERROR, "缺少必填参数：title")
    if len(title) > TITLE_MAX_LENGTH:
        return None, make_response(CODE_PARAM_ERROR, f"番名长度不能超过 {TITLE_MAX_LENGTH} 位")
    if len(category) > CATEGORY_MAX_LENGTH:
        return None, make_response(CODE_PARAM_ERROR, f"分类长度不能超过 {CATEGORY_MAX_LENGTH} 位")
    if len(cover) > COVER_MAX_LENGTH:
        return None, make_response(CODE_PARAM_ERROR, f"封面地址不能超过 {COVER_MAX_LENGTH} 位")
    if len(description) > DESCRIPTION_MAX_LENGTH:
        return None, make_response(
            CODE_PARAM_ERROR, f"简介长度不能超过 {DESCRIPTION_MAX_LENGTH} 字"
        )
    if len(link) > LINK_MAX_LENGTH:
        return None, make_response(CODE_PARAM_ERROR, f"链接长度不能超过 {LINK_MAX_LENGTH} 位")
    if link and not LINK_PATTERN.match(link):
        return None, make_response(CODE_PARAM_ERROR, "链接需为 http:// 或 https:// 开头的有效地址")

    return {
        "title": title,
        "category": category,
        "cover": cover,
        "description": description,
        "link": link,
    }, None


@bp.get("/animes")
def list_animes():
    """番剧库列表：GET /api/animes?page=1&page_size=10&q=关键词"""
    page, page_size = parse_page_args()
    q = clean(request.args.get("q"))

    where = ""
    args = []
    if q:
        where = " WHERE a.title LIKE %s OR a.category LIKE %s"
        like = f"%{q}%"
        args += [like, like]

    count_sql = "SELECT COUNT(*) AS total FROM animes a" + where
    list_sql = ANIME_SELECT + where + " ORDER BY a.create_time DESC, a.id DESC"
    items, total = paginate(count_sql, list_sql, args, page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["update_time"] = format_datetime(item["update_time"])
        item["description"] = item["description"] or ""
    return make_page_response(items, total, page, page_size)


@bp.post("/animes")
@admin_required
def create_anime():
    """管理员新增番剧：POST /api/animes，body {title, category?, cover?, description?, link?}"""
    payload, error = _validate_anime_body(get_body())
    if error:
        return error

    anime_id = execute(
        "INSERT INTO animes (title, category, cover, description, link, admin_id) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (
            payload["title"],
            payload["category"],
            payload["cover"],
            payload["description"],
            payload["link"],
            g.current_user["id"],
        ),
    )
    return make_response(CODE_SUCCESS, "已新增番剧", {"id": anime_id})


@bp.put("/animes/<int:anime_id>")
@admin_required
def update_anime(anime_id):
    """管理员修改番剧：PUT /api/animes/1，body 同新增（title 必填）"""
    payload, error = _validate_anime_body(get_body())
    if error:
        return error

    if query_one("SELECT id FROM animes WHERE id=%s", (anime_id,)) is None:
        return make_response(CODE_NOT_FOUND, "番剧不存在")

    execute(
        "UPDATE animes SET title=%s, category=%s, cover=%s, description=%s, link=%s WHERE id=%s",
        (
            payload["title"],
            payload["category"],
            payload["cover"],
            payload["description"],
            payload["link"],
            anime_id,
        ),
    )
    return make_response(CODE_SUCCESS, "已保存番剧", {"id": anime_id})


@bp.delete("/animes/<int:anime_id>")
@admin_required
def delete_anime(anime_id):
    """管理员删除番剧：DELETE /api/animes/1"""
    if query_one("SELECT id FROM animes WHERE id=%s", (anime_id,)) is None:
        return make_response(CODE_NOT_FOUND, "番剧不存在")

    execute("DELETE FROM animes WHERE id=%s", (anime_id,))
    return make_response(CODE_SUCCESS, "已删除番剧", {"id": anime_id})


@bp.get("/anime-recommendations")
def list_recommendations():
    """番剧推荐列表：GET /api/anime-recommendations?page=1&page_size=10

    封禁（review_status=3）的推荐不对外展示。
    """
    page, page_size = parse_page_args()
    where = " WHERE r.review_status<>3"
    count_sql = (
        "SELECT COUNT(*) AS total FROM anime_recommendations r" + where
    )
    list_sql = RECOMMEND_SELECT + where + " ORDER BY r.create_time DESC, r.id DESC"
    items, total = paginate(count_sql, list_sql, page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["reason"] = item["reason"] or ""
        item["review_note"] = item["review_note"] or ""
    return make_page_response(items, total, page, page_size)


@bp.post("/anime-recommendations")
@login_required
def create_recommendation():
    """发起番剧推荐：POST /api/anime-recommendations，body {anime_name, link, reason}

    番名、链接、推荐理由均为必填，链接仅接受 http/https。
    """
    body = get_body()
    missing = require(body, "anime_name", "link", "reason")
    if missing:
        return make_response(CODE_PARAM_ERROR, f"缺少必填参数：{'、'.join(missing)}")

    anime_name = clean(body.get("anime_name"))
    link = clean(body.get("link"))
    reason = clean(body.get("reason"))

    if len(anime_name) > ANIME_NAME_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"番名长度不能超过 {ANIME_NAME_MAX_LENGTH} 位")
    if len(link) > LINK_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"链接长度不能超过 {LINK_MAX_LENGTH} 位")
    if not LINK_PATTERN.match(link):
        return make_response(CODE_PARAM_ERROR, "番剧链接需为 http:// 或 https:// 开头的有效地址")
    if len(reason) > REASON_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"推荐理由长度不能超过 {REASON_MAX_LENGTH} 字")

    recommend_id = execute(
        "INSERT INTO anime_recommendations (user_id, anime_name, link, reason) "
        "VALUES (%s, %s, %s, %s)",
        (g.current_user["id"], anime_name, link, reason),
    )
    return make_response(CODE_SUCCESS, "推荐成功，等待管理员评审", {"id": recommend_id})
