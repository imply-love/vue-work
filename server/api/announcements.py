"""公告接口：前台公开展示 + 后台管理（仅管理员）。

- GET    /api/announcements                   前台公告列表（仅发布中，最新在前）
- GET    /api/admin/announcements             后台公告列表（全部，分页，支持状态/关键词筛选）
- POST   /api/admin/announcements             新建公告（body {title, content, status?}）
- PUT    /api/admin/announcements/<id>        编辑公告（body {title, content}）
- PUT    /api/admin/announcements/<id>/status 发布 / 下架（body {status: 1|0}）
- DELETE /api/admin/announcements/<id>        删除公告
"""
from flask import Blueprint, g, request

from db import execute, paginate, query_all, query_one
from utils.auth import admin_required
from utils.params import clean, get_body, parse_page_args, require
from utils.response import (
    CODE_NOT_FOUND,
    CODE_PARAM_ERROR,
    CODE_SUCCESS,
    format_datetime,
    make_page_response,
    make_response,
)

bp = Blueprint("announcements", __name__, url_prefix="/api")

TITLE_MAX_LENGTH = 100
CONTENT_MAX_LENGTH = 2000

ANNOUNCE_SELECT = (
    "SELECT a.id, a.title, a.content, a.status, a.create_time, a.update_time, "
    "a.publish_time, u.nickname AS admin_nickname "
    "FROM announcements a JOIN users u ON u.id=a.admin_id"
)


@bp.get("/announcements")
def list_public_announcements():
    """前台公告：GET /api/announcements（仅返回发布中的公告，最多 10 条）"""
    rows = query_all(
        ANNOUNCE_SELECT + " WHERE a.status=1 "
        "ORDER BY a.publish_time DESC, a.id DESC LIMIT 10"
    )
    for item in rows:
        item["create_time"] = format_datetime(item["create_time"])
        item["publish_time"] = format_datetime(item["publish_time"])
    return make_response(CODE_SUCCESS, "获取成功", {"list": rows, "total": len(rows)})


@bp.get("/admin/announcements")
@admin_required
def list_announcements():
    """后台公告列表：GET /api/admin/announcements?status=0|1&page=1&q=标题关键词"""
    page, page_size = parse_page_args()
    status = clean(request.args.get("status"))
    q = clean(request.args.get("q"))

    where = []
    args = []
    if status.isdigit():
        where.append("a.status=%s")
        args.append(int(status))
    if q:
        where.append("a.title LIKE %s")
        args.append(f"%{q}%")
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    count_sql = "SELECT COUNT(*) AS total FROM announcements a" + where_sql
    list_sql = ANNOUNCE_SELECT + where_sql + " ORDER BY a.create_time DESC, a.id DESC"
    items, total = paginate(count_sql, list_sql, args, page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["update_time"] = format_datetime(item["update_time"])
        item["publish_time"] = format_datetime(item["publish_time"])
    return make_page_response(items, total, page, page_size)


@bp.post("/admin/announcements")
@admin_required
def create_announcement():
    """新建公告：POST /api/admin/announcements，body {title, content, status?}

    status 缺省为 1（立即发布）；传 0 表示仅创建不发布。
    """
    body = get_body()
    title = clean(body.get("title"))
    content = clean(body.get("content"))
    status = 1 if clean(body.get("status", "1")) == "1" else 0

    missing = require(body, "title", "content")
    if missing:
        return make_response(CODE_PARAM_ERROR, f"缺少必填参数：{'、'.join(missing)}")
    if len(title) > TITLE_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"标题不能超过 {TITLE_MAX_LENGTH} 字")
    if len(content) > CONTENT_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"内容不能超过 {CONTENT_MAX_LENGTH} 字")

    announcement_id = execute(
        "INSERT INTO announcements (title, content, status, admin_id, publish_time) "
        "VALUES (%s, %s, %s, %s, CASE WHEN %s=1 THEN NOW() ELSE NULL END)",
        (title, content, status, g.current_user["id"], status),
    )
    message = "公告已创建并发布" if status else "公告已创建（未发布）"
    return make_response(CODE_SUCCESS, message, {"id": announcement_id, "status": status})


@bp.put("/admin/announcements/<int:announcement_id>")
@admin_required
def update_announcement(announcement_id):
    """编辑公告：PUT /api/admin/announcements/1，body {title, content}"""
    body = get_body()
    title = clean(body.get("title"))
    content = clean(body.get("content"))

    missing = require(body, "title", "content")
    if missing:
        return make_response(CODE_PARAM_ERROR, f"缺少必填参数：{'、'.join(missing)}")
    if len(title) > TITLE_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"标题不能超过 {TITLE_MAX_LENGTH} 字")
    if len(content) > CONTENT_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"内容不能超过 {CONTENT_MAX_LENGTH} 字")

    item = query_one("SELECT id, status FROM announcements WHERE id=%s", (announcement_id,))
    if item is None:
        return make_response(CODE_NOT_FOUND, "公告不存在")

    execute(
        "UPDATE announcements SET title=%s, content=%s, "
        "publish_time=CASE WHEN %s=1 THEN NOW() ELSE publish_time END WHERE id=%s",
        (title, content, item["status"], announcement_id),
    )
    return make_response(CODE_SUCCESS, "公告已更新", {"id": announcement_id})


@bp.put("/admin/announcements/<int:announcement_id>/status")
@admin_required
def set_announcement_status(announcement_id):
    """发布 / 下架公告：PUT /api/admin/announcements/1/status，body {status: 1|0}"""
    body = get_body()
    raw = clean(body.get("status"))
    if raw not in ("0", "1"):
        return make_response(CODE_PARAM_ERROR, "status 只能是 1（发布）或 0（下架）")
    status = int(raw)

    item = query_one("SELECT id FROM announcements WHERE id=%s", (announcement_id,))
    if item is None:
        return make_response(CODE_NOT_FOUND, "公告不存在")

    execute(
        "UPDATE announcements SET status=%s, "
        "publish_time=CASE WHEN %s=1 THEN NOW() ELSE publish_time END WHERE id=%s",
        (status, status, announcement_id),
    )
    label = "已发布" if status else "已下架"
    return make_response(CODE_SUCCESS, f"公告{label}", {"id": announcement_id, "status": status})


@bp.delete("/admin/announcements/<int:announcement_id>")
@admin_required
def delete_announcement(announcement_id):
    """删除公告：DELETE /api/admin/announcements/1"""
    item = query_one("SELECT id FROM announcements WHERE id=%s", (announcement_id,))
    if item is None:
        return make_response(CODE_NOT_FOUND, "公告不存在")
    execute("DELETE FROM announcements WHERE id=%s", (announcement_id,))
    return make_response(CODE_SUCCESS, "公告已删除", {"id": announcement_id})
