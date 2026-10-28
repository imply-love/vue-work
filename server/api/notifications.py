"""站内通知接口：个人中心「消息通知」页与导航未读角标。

- GET /api/notifications              我的通知分页列表（支持 unread=1 只看未读）
- GET /api/notifications/unread-count 我的未读通知数量
- PUT /api/notifications/<id>/read    标记单条已读
- PUT /api/notifications/read-all     全部标记已读
"""
from flask import Blueprint, g, request

from db import execute, paginate, query_one
from utils.auth import login_required
from utils.params import clean, parse_page_args
from utils.response import (
    CODE_NOT_FOUND,
    CODE_SUCCESS,
    format_datetime,
    make_page_response,
    make_response,
)

bp = Blueprint("notifications", __name__, url_prefix="/api")


@bp.get("/notifications")
@login_required
def list_notifications():
    """我的通知：GET /api/notifications?page=1&page_size=10&unread=1"""
    page, page_size = parse_page_args()
    unread = clean(request.args.get("unread"))
    user_id = g.current_user["id"]

    where = " WHERE user_id=%s"
    args = [user_id]
    if unread == "1":
        where += " AND is_read=0"

    count_sql = "SELECT COUNT(*) AS total FROM notifications" + where
    list_sql = (
        "SELECT id, type, title, content, link, is_read, create_time "
        "FROM notifications" + where + " ORDER BY is_read ASC, create_time DESC, id DESC"
    )
    items, total = paginate(count_sql, list_sql, args, page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
    return make_page_response(items, total, page, page_size)


@bp.get("/notifications/unread-count")
@login_required
def unread_count():
    """未读数量：GET /api/notifications/unread-count"""
    row = query_one(
        "SELECT COUNT(*) AS total FROM notifications WHERE user_id=%s AND is_read=0",
        (g.current_user["id"],),
    )
    return make_response(CODE_SUCCESS, "获取成功", {"count": int(row["total"])})


@bp.put("/notifications/read-all")
@login_required
def read_all():
    """全部标记已读：PUT /api/notifications/read-all"""
    execute(
        "UPDATE notifications SET is_read=1 WHERE user_id=%s AND is_read=0",
        (g.current_user["id"],),
    )
    return make_response(CODE_SUCCESS, "已全部标记为已读")


@bp.put("/notifications/<int:notification_id>/read")
@login_required
def read_one(notification_id):
    """标记单条已读：PUT /api/notifications/1/read"""
    item = query_one(
        "SELECT id FROM notifications WHERE id=%s AND user_id=%s",
        (notification_id, g.current_user["id"]),
    )
    if item is None:
        return make_response(CODE_NOT_FOUND, "通知不存在")

    execute("UPDATE notifications SET is_read=1 WHERE id=%s", (notification_id,))
    return make_response(CODE_SUCCESS, "已标记为已读")
