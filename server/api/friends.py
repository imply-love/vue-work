"""好友接口：好友申请、审批与好友列表。

- POST   /api/friends/requests        发起好友申请（需登录）
- GET    /api/friends/requests        收到的/发出的好友申请
- PUT    /api/friends/requests/<id>   同意/拒绝好友申请
- GET    /api/friends                 我的好友列表
- GET    /api/friends/pending-count   待处理申请数量（导航角标）
- DELETE /api/friends/<user_id>       解除好友关系
"""
from flask import Blueprint, g, request

from db import execute, paginate, query_one
from utils.auth import login_required
from utils.params import clean, get_body, parse_page_args
from utils.response import (
    CODE_NOT_FOUND,
    CODE_NO_PERMISSION,
    CODE_PARAM_ERROR,
    CODE_SUCCESS,
    format_datetime,
    make_page_response,
    make_response,
)

bp = Blueprint("friends", __name__, url_prefix="/api")

REQUEST_MESSAGE_MAX_LENGTH = 255

USER_CARD_SELECT = (
    "SELECT u.id, u.username, u.nickname, u.avatar, u.followers_count, "
    "u.likes_count, u.following_count, u.create_time "
    "FROM users u"
)


def _are_friends(user_id, other_id):
    row = query_one(
        "SELECT id FROM friends WHERE user_id=%s AND friend_id=%s",
        (user_id, other_id),
    )
    return row is not None


def _write_friendship(user_id, other_id):
    """好友关系双向写入，重复执行不会产生重复行。"""
    execute(
        "INSERT IGNORE INTO friends (user_id, friend_id) VALUES (%s, %s), (%s, %s)",
        (user_id, other_id, other_id, user_id),
    )


@bp.post("/friends/requests")
@login_required
def send_friend_request():
    """发起好友申请：POST /api/friends/requests，body {user_id, message?}"""
    user_id = g.current_user["id"]
    body = get_body()
    raw_target = clean(body.get("user_id"))
    message = clean(body.get("message"))

    if not raw_target:
        return make_response(CODE_PARAM_ERROR, "缺少必填参数：user_id")
    if not raw_target.isdigit():
        return make_response(CODE_PARAM_ERROR, "user_id 需为数字")
    target_id = int(raw_target)

    if target_id == user_id:
        return make_response(CODE_PARAM_ERROR, "不能添加自己为好友")
    if len(message) > REQUEST_MESSAGE_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"申请留言不能超过 {REQUEST_MESSAGE_MAX_LENGTH} 字")

    target = query_one("SELECT id, nickname FROM users WHERE id=%s", (target_id,))
    if target is None:
        return make_response(CODE_NOT_FOUND, "用户不存在")
    if _are_friends(user_id, target_id):
        return make_response(CODE_SUCCESS, "你们已经是好友了")

    # 对方已经向我发过申请：直接互相通过，省去一次点击
    reverse = query_one(
        "SELECT id FROM friend_requests "
        "WHERE from_user_id=%s AND to_user_id=%s AND status=0",
        (target_id, user_id),
    )
    if reverse:
        _write_friendship(user_id, target_id)
        execute(
            "UPDATE friend_requests SET status=1, handle_time=NOW() WHERE id=%s",
            (reverse["id"],),
        )
        return make_response(CODE_SUCCESS, "已互相通过好友申请")

    existed = query_one(
        "SELECT id, status FROM friend_requests WHERE from_user_id=%s AND to_user_id=%s",
        (user_id, target_id),
    )
    if existed:
        if existed["status"] == 0:
            return make_response(CODE_SUCCESS, "好友申请已发送，请等待对方处理")
        # 曾被拒绝，允许重新申请
        execute(
            "UPDATE friend_requests SET status=0, message=%s, create_time=NOW(), "
            "handle_time=NULL WHERE id=%s",
            (message, existed["id"]),
        )
        return make_response(CODE_SUCCESS, "好友申请已重新发送")

    execute(
        "INSERT INTO friend_requests (from_user_id, to_user_id, message) VALUES (%s, %s, %s)",
        (user_id, target_id, message),
    )
    return make_response(CODE_SUCCESS, f"已向 {target['nickname']} 发送好友申请")


@bp.get("/friends/requests")
@login_required
def list_friend_requests():
    """好友申请列表：GET /api/friends/requests?direction=incoming|outgoing&page=1"""
    user_id = g.current_user["id"]
    direction = request.args.get("direction", "incoming")
    page, page_size = parse_page_args()

    if direction == "outgoing":
        where = "WHERE fr.from_user_id=%s"
        join_sql = "SELECT fr.id, fr.message, fr.status, fr.create_time, fr.handle_time, " \
                   "u.id AS user_id, u.nickname, u.avatar " \
                   "FROM friend_requests fr JOIN users u ON u.id=fr.to_user_id "
        count_sql = "SELECT COUNT(*) AS total FROM friend_requests fr WHERE fr.from_user_id=%s"
    else:
        where = "WHERE fr.to_user_id=%s"
        join_sql = "SELECT fr.id, fr.message, fr.status, fr.create_time, fr.handle_time, " \
                   "u.id AS user_id, u.nickname, u.avatar " \
                   "FROM friend_requests fr JOIN users u ON u.id=fr.from_user_id "
        count_sql = "SELECT COUNT(*) AS total FROM friend_requests fr WHERE fr.to_user_id=%s"

    list_sql = join_sql + where + " ORDER BY fr.status ASC, fr.create_time DESC, fr.id DESC"
    items, total = paginate(count_sql, list_sql, (user_id,), page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["handle_time"] = format_datetime(item["handle_time"])
    return make_page_response(items, total, page, page_size)


@bp.get("/friends/pending-count")
@login_required
def pending_count():
    """待处理好友申请数量：GET /api/friends/pending-count"""
    row = query_one(
        "SELECT COUNT(*) AS total FROM friend_requests WHERE to_user_id=%s AND status=0",
        (g.current_user["id"],),
    )
    return make_response(CODE_SUCCESS, "获取成功", {"count": int(row["total"])})


@bp.put("/friends/requests/<int:request_id>")
@login_required
def handle_friend_request(request_id):
    """同意/拒绝好友申请：PUT /api/friends/requests/1，body {action: accept|reject}"""
    user_id = g.current_user["id"]
    body = get_body()
    action = clean(body.get("action"))

    if action not in ("accept", "reject"):
        return make_response(CODE_PARAM_ERROR, "action 只能是 accept 或 reject")

    item = query_one(
        "SELECT id, from_user_id, to_user_id, status FROM friend_requests WHERE id=%s",
        (request_id,),
    )
    if item is None:
        return make_response(CODE_NOT_FOUND, "好友申请不存在")
    if item["to_user_id"] != user_id:
        return make_response(CODE_NO_PERMISSION, "只能处理发给自己的好友申请")
    if item["status"] != 0:
        return make_response(CODE_PARAM_ERROR, "该申请已处理")

    if action == "accept":
        _write_friendship(user_id, item["from_user_id"])
        execute(
            "UPDATE friend_requests SET status=1, handle_time=NOW() WHERE id=%s",
            (request_id,),
        )
        return make_response(CODE_SUCCESS, "已添加为好友")

    execute(
        "UPDATE friend_requests SET status=2, handle_time=NOW() WHERE id=%s",
        (request_id,),
    )
    return make_response(CODE_SUCCESS, "已拒绝好友申请")


@bp.get("/friends")
@login_required
def list_friends():
    """我的好友列表：GET /api/friends?page=1&page_size=10"""
    user_id = g.current_user["id"]
    page, page_size = parse_page_args()
    count_sql = "SELECT COUNT(*) AS total FROM friends WHERE user_id=%s"
    list_sql = (
        USER_CARD_SELECT
        + " JOIN friends f ON f.friend_id = u.id "
        "WHERE f.user_id=%s ORDER BY f.create_time DESC, f.id DESC"
    )
    items, total = paginate(count_sql, list_sql, (user_id,), page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["is_friend"] = True
    return make_page_response(items, total, page, page_size)


@bp.delete("/friends/<int:friend_id>")
@login_required
def remove_friend(friend_id):
    """解除好友关系：DELETE /api/friends/2（双向删除）"""
    user_id = g.current_user["id"]
    if not _are_friends(user_id, friend_id):
        return make_response(CODE_NOT_FOUND, "你们还不是好友")
    execute(
        "DELETE FROM friends WHERE (user_id=%s AND friend_id=%s) "
        "OR (user_id=%s AND friend_id=%s)",
        (user_id, friend_id, friend_id, user_id),
    )
    return make_response(CODE_SUCCESS, "已解除好友关系")
