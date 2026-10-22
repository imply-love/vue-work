"""资源分享接口：支撑资源分享板块的分享资源功能。

- GET /api/resources：公开分页列表，游客也可浏览
- POST /api/resources：需登录，管理员与普通用户均可分享资源
"""
import re

from flask import Blueprint, g

from db import execute, paginate
from utils.auth import login_required
from utils.params import clean, get_body, parse_page_args, require
from utils.response import (
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

LIST_SQL = (
    "SELECT r.id, r.user_id, r.title, r.description, r.link, r.create_time, "
    "u.nickname AS author_nickname, u.avatar AS author_avatar "
    "FROM resources r JOIN users u ON u.id = r.user_id "
    "ORDER BY r.create_time DESC, r.id DESC"
)
COUNT_SQL = "SELECT COUNT(*) AS total FROM resources"


@bp.get("/resources")
def list_resources():
    """资源分页列表：GET /api/resources?page=1&page_size=10"""
    page, page_size = parse_page_args()
    items, total = paginate(COUNT_SQL, LIST_SQL, page=page, page_size=page_size)

    for item in items:
        item["create_time"] = format_datetime(item["create_time"])

    return make_page_response(items, total, page, page_size)


@bp.post("/resources")
@login_required
def create_resource():
    """分享资源：POST /api/resources，body {title, link, description?}

    需登录：管理员与普通用户均可分享，未登录返回 1007。
    """
    user_id = g.current_user["id"]
    body = get_body()
    title = clean(body.get("title"))
    link = clean(body.get("link"))
    description = clean(body.get("description"))

    missing = require(body, "title", "link")
    if missing:
        return make_response(CODE_PARAM_ERROR, f"缺少必填参数：{'、'.join(missing)}")

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
        "INSERT INTO resources (user_id, title, description, link) VALUES (%s, %s, %s, %s)",
        (user_id, title, description, link),
    )
    return make_response(CODE_SUCCESS, "分享成功", {"id": resource_id})
