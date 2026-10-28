"""账号申诉接口：被封禁用户提交申诉、查看自己的申诉记录。

- POST /api/user/appeal    提交申诉（仅 status=2 的封禁用户）
- GET  /api/user/appeals   我的申诉记录
"""
from flask import Blueprint, g

from db import execute, paginate, query_one
from utils.auth import STATUS_BANNED, login_required
from utils.params import clean, get_body, parse_page_args
from utils.response import (
    CODE_APPEAL_EXISTS,
    CODE_NOT_BANNED,
    CODE_PARAM_ERROR,
    CODE_SUCCESS,
    format_datetime,
    make_page_response,
    make_response,
)

bp = Blueprint("appeals", __name__, url_prefix="/api")

APPEAL_REASON_MAX_LENGTH = 1000


@bp.post("/user/appeal")
@login_required
def submit_appeal():
    """提交申诉：POST /api/user/appeal，body {reason}"""
    user_id = g.current_user["id"]

    if g.current_user.get("status") != STATUS_BANNED:
        return make_response(CODE_NOT_BANNED, "账号未被封禁，无需申诉")

    reason = clean(get_body().get("reason"))
    if not reason:
        return make_response(CODE_PARAM_ERROR, "缺少必填参数：reason")
    if len(reason) > APPEAL_REASON_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"申诉理由不能超过 {APPEAL_REASON_MAX_LENGTH} 字")

    pending = query_one(
        "SELECT id FROM appeals WHERE user_id=%s AND status=0",
        (user_id,),
    )
    if pending:
        return make_response(CODE_APPEAL_EXISTS, "已有待处理的申诉，请耐心等待")

    appeal_id = execute(
        "INSERT INTO appeals (user_id, reason) VALUES (%s, %s)",
        (user_id, reason),
    )
    return make_response(CODE_SUCCESS, "申诉已提交，等待管理员处理", {"id": appeal_id})


@bp.get("/user/appeals")
@login_required
def list_my_appeals():
    """我的申诉记录：GET /api/user/appeals?page=1&page_size=10"""
    user_id = g.current_user["id"]
    page, page_size = parse_page_args()

    count_sql = "SELECT COUNT(*) AS total FROM appeals WHERE user_id=%s"
    list_sql = (
        "SELECT id, reason, status, admin_note, create_time, handle_time "
        "FROM appeals WHERE user_id=%s ORDER BY create_time DESC, id DESC"
    )
    items, total = paginate(count_sql, list_sql, (user_id,), page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["handle_time"] = format_datetime(item["handle_time"])
    return make_page_response(items, total, page, page_size)
