"""资源分享接口：支撑资源分享板块的分享资源功能。

- GET /api/resources：分页列表（必须登录；按查看条件过滤）
- POST /api/resources：需登录，管理员与普通用户均可分享资源

查看条件 visibility：0-所有同好 1-仅管理员与特殊身份 2-仅自己。
未登录用户一律禁止查看；管理员可见全部，特殊身份可见「所有同好 + 仅管理员与特殊身份」。
"""
import re

from flask import Blueprint, g

from db import execute, paginate, query_one
from utils.auth import login_required
from utils.params import clean, get_body, parse_page_args, require
from utils.response import (
    CODE_NOT_FOUND,
    CODE_NO_PERMISSION,
    CODE_PARAM_ERROR,
    CODE_SUCCESS,
    format_datetime,
    make_page_response,
    make_response,
)

bp = Blueprint("resources", __name__, url_prefix="/api")

# 与 resources 表字段长度保持一致，超长直接返回 1001
TITLE_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 5000
LINK_MAX_LENGTH = 500

# 资源链接仅接受 http/https 地址，其他协议一律拦截
LINK_PATTERN = re.compile(r"^https?://\S+$", re.IGNORECASE)

VISIBILITY_VALUES = (0, 1, 2)

LIST_SQL = (
    "SELECT r.id, r.user_id, r.title, r.description, r.link, r.visibility, "
    "r.review_status, r.create_time, "
    "u.nickname AS author_nickname, u.avatar AS author_avatar "
    "FROM resources r JOIN users u ON u.id = r.user_id"
)


@bp.get("/resources")
@login_required
def list_resources():
    """资源分页列表：GET /api/resources?page=1&page_size=10

    未登录返回 1007；封禁（review_status=3）的资源不展示。
    """
    page, page_size = parse_page_args()
    user_id = g.current_user["id"]
    viewer = query_one("SELECT role, identity FROM users WHERE id=%s", (user_id,))

    where = ["r.review_status<>3"]
    args = []
    if viewer["role"] != 1:
        if viewer.get("identity"):
            where.append("(r.visibility IN (0, 1) OR r.user_id=%s)")
        else:
            where.append("(r.visibility=0 OR r.user_id=%s)")
        args.append(user_id)
    where_sql = " WHERE " + " AND ".join(where)

    count_sql = "SELECT COUNT(*) AS total FROM resources r" + where_sql
    list_sql = LIST_SQL + where_sql + " ORDER BY r.create_time DESC, r.id DESC"
    items, total = paginate(count_sql, list_sql, args, page=page, page_size=page_size)

    for item in items:
        item["create_time"] = format_datetime(item["create_time"])

    return make_page_response(items, total, page, page_size)


@bp.post("/resources")
@login_required
def create_resource():
    """分享资源：POST /api/resources，body {title, link, description?, visibility?}

    需登录：管理员与普通用户均可分享，未登录返回 1007。
    visibility 默认为 0（所有同好可见）。
    """
    user_id = g.current_user["id"]
    body = get_body()
    title = clean(body.get("title"))
    link = clean(body.get("link"))
    description = clean(body.get("description"))
    visibility_raw = clean(body.get("visibility", "0"))

    missing = require(body, "title", "link")
    if missing:
        return make_response(CODE_PARAM_ERROR, f"缺少必填参数：{'、'.join(missing)}")

    if not visibility_raw.isdigit() or int(visibility_raw) not in VISIBILITY_VALUES:
        return make_response(CODE_PARAM_ERROR, "查看条件只能是 0、1、2")
    visibility = int(visibility_raw)

    if len(title) > TITLE_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"资源标题长度不能超过 {TITLE_MAX_LENGTH} 位")
    if len(description) > DESCRIPTION_MAX_LENGTH:
        return make_response(
            CODE_PARAM_ERROR, f"资源描述长度不能超过 {DESCRIPTION_MAX_LENGTH} 字"
        )
    if len(link) > LINK_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"资源链接长度不能超过 {LINK_MAX_LENGTH} 位")
    if not LINK_PATTERN.match(link):
        return make_response(CODE_PARAM_ERROR, "资源链接需为 http:// 或 https:// 开头的有效地址")

    resource_id = execute(
        "INSERT INTO resources (user_id, title, description, link, visibility) "
        "VALUES (%s, %s, %s, %s, %s)",
        (user_id, title, description, link, visibility),
    )
    return make_response(CODE_SUCCESS, "分享成功", {"id": resource_id, "visibility": visibility})


@bp.delete("/resources/<int:resource_id>")
@login_required
def delete_resource(resource_id):
    """删除资源：DELETE /api/resources/1（发布者本人或管理员可删）"""
    item = query_one("SELECT id, user_id FROM resources WHERE id=%s", (resource_id,))
    if item is None:
        return make_response(CODE_NOT_FOUND, "资源不存在")
    if g.current_user["id"] != item["user_id"] and g.current_user.get("role") != 1:
        return make_response(CODE_NO_PERMISSION, "只能删除自己分享的资源")

    execute("DELETE FROM resources WHERE id=%s", (resource_id,))
    return make_response(CODE_SUCCESS, "已删除该资源", {"id": resource_id})
