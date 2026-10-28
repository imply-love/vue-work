"""身份申请接口：番剧大佬 / 我就是资源。

- GET  /api/identity/overview        我的身份、有效推荐/分享数量与申请记录
- POST /api/identity/applications    提交身份申请（需达到 20 条有效记录）

有效口径：管理员评审结果为「推荐」（review_status=1）的番剧推荐 / 资源分享。
"""
from flask import Blueprint, g

from db import execute, query_all, query_one
from utils.auth import login_required
from utils.params import clean, get_body
from utils.response import (
    CODE_APPLICATION_EXISTS,
    CODE_PARAM_ERROR,
    CODE_SUCCESS,
    format_datetime,
    make_response,
)

bp = Blueprint("identity", __name__, url_prefix="/api")

THRESHOLD = 20

IDENTITY_META = {
    "anime_master": {
        "label": "番剧大佬",
        "source": "番剧推荐",
        "table": "anime_recommendations",
    },
    "resource_master": {
        "label": "我就是资源",
        "source": "资源分享",
        "table": "resources",
    },
}

REASON_MAX_LENGTH = 5000


def _valid_count(identity_type, user_id):
    """统计某身份对应的有效（评审为推荐）条目数。"""
    meta = IDENTITY_META[identity_type]
    row = query_one(
        f"SELECT COUNT(*) AS total FROM {meta['table']} "
        "WHERE user_id=%s AND review_status=1",
        (user_id,),
    )
    return int(row["total"])


def identity_codes(raw):
    """把逗号分隔的身份编码拆成列表（支持一人多身份）。"""
    return [item for item in (raw or "").split(",") if item]


def identity_labels(raw):
    """身份编码转中文称号，用于个人中心展示。"""
    return [IDENTITY_META[item]["label"] for item in identity_codes(raw) if item in IDENTITY_META]


def _application_row(item):
    item["create_time"] = format_datetime(item["create_time"])
    item["handle_time"] = format_datetime(item["handle_time"])
    item["identity_label"] = IDENTITY_META[item["identity_type"]]["label"]
    item["reason"] = item["reason"] or ""
    item["admin_note"] = item["admin_note"] or ""
    return item


@bp.get("/identity/overview")
@login_required
def overview():
    """我的身份概览：GET /api/identity/overview"""
    user_id = g.current_user["id"]
    user = query_one("SELECT identity FROM users WHERE id=%s", (user_id,))
    identity = user["identity"] if user else ""

    applications = []
    rows = query_all(
        "SELECT id, identity_type, reason, status, admin_note, create_time, handle_time "
        "FROM identity_applications WHERE user_id=%s ORDER BY create_time DESC, id DESC",
        (user_id,),
    )
    applications = [_application_row(item) for item in rows]

    return make_response(CODE_SUCCESS, "获取成功", {
        "identity": identity,
        "identity_label": "、".join(identity_labels(identity)),
        "threshold": THRESHOLD,
        "anime_valid": _valid_count("anime_master", user_id),
        "resource_valid": _valid_count("resource_master", user_id),
        "applications": applications,
    })


@bp.post("/identity/applications")
@login_required
def apply_identity():
    """提交身份申请：POST /api/identity/applications，body {identity_type, reason?}"""
    body = get_body()
    identity_type = clean(body.get("identity_type"))
    reason = clean(body.get("reason"))
    user_id = g.current_user["id"]

    if identity_type not in IDENTITY_META:
        return make_response(CODE_PARAM_ERROR, "identity_type 只能是 anime_master 或 resource_master")
    if len(reason) > REASON_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"申请说明不能超过 {REASON_MAX_LENGTH} 字")

    user = query_one("SELECT identity FROM users WHERE id=%s", (user_id,))
    if user and identity_type in identity_codes(user["identity"]):
        return make_response(CODE_PARAM_ERROR, "你已拥有该身份")

    pending = query_one(
        "SELECT id FROM identity_applications "
        "WHERE user_id=%s AND identity_type=%s AND status=0",
        (user_id, identity_type),
    )
    if pending is not None:
        return make_response(CODE_APPLICATION_EXISTS, "该身份的申请正在审核中，请耐心等待")

    valid = _valid_count(identity_type, user_id)
    if valid < THRESHOLD:
        return make_response(
            CODE_PARAM_ERROR,
            f"有效{IDENTITY_META[identity_type]['source']}需达到 {THRESHOLD} 条，当前 {valid} 条",
        )

    application_id = execute(
        "INSERT INTO identity_applications (user_id, identity_type, reason) VALUES (%s, %s, %s)",
        (user_id, identity_type, reason),
    )
    # 通知所有管理员有新申请待审批
    label = IDENTITY_META[identity_type]["label"]
    execute(
        "INSERT INTO notifications (user_id, type, title, content, link) "
        "SELECT id, 'identity', %s, %s, '/admin' FROM users WHERE role=1",
        ("新的身份申请", f"有用户提交「{label}」身份申请，请尽快审批"),
    )
    return make_response(CODE_SUCCESS, "申请已提交，等待管理员审批", {"id": application_id})
