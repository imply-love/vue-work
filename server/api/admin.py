"""管理后台接口：帖子/评论审查、用户管理、申诉处理、看板与公告（仅管理员）。

- GET  /api/admin/dashboard              看板数据（趋势/状态分布/待办清单）
- GET  /api/admin/posts                  全部帖子（支持状态/审查状态/关键词筛选）
- PUT  /api/admin/posts/<id>/review      审查帖子：approve-通过 recommend-推荐 reject-打回 ban-封禁 restore-恢复
- GET  /api/admin/comments               全部评论（支持审查状态/关键词筛选）
- PUT  /api/admin/comments/<id>/review   审查评论：approve-通过 reject-打回 ban-封禁 restore-恢复
- GET  /api/admin/users                  用户列表
- PUT  /api/admin/users/<id>/disable     禁用账号（禁用后无法登录，可启用）
- PUT  /api/admin/users/<id>/enable      启用账号
- PUT  /api/admin/users/<id>/ban         封禁账号（必填理由，已发布帖子转私密）
- PUT  /api/admin/users/<id>/unban       解除封禁
- GET  /api/admin/appeals                申诉列表
- PUT  /api/admin/appeals/<id>           处理申诉：accept-通过（解封） reject-驳回
- GET  /api/admin/stats                  后台概览统计
"""
from flask import Blueprint, g, request

from api.identity import IDENTITY_META, identity_codes
from db import execute, paginate, query_all, query_one
from utils.auth import (
    STATUS_BANNED,
    STATUS_DISABLED,
    STATUS_NORMAL,
    admin_required,
)
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

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# 帖子审查动作 -> review_status（0-正常 1-推荐 2-打回 3-封禁 4-待审核）
REVIEW_ACTIONS = {
    "approve": 0,
    "recommend": 1,
    "reject": 2,
    "ban": 3,
    "restore": 0,
}
# 打回 / 封禁必须填写理由
REVIEW_REASON_REQUIRED = ("ban", "reject")

# 评论审查动作：无需推荐层级，通过即正常
COMMENT_REVIEW_ACTIONS = {"approve": 0, "reject": 2, "ban": 3, "restore": 0}

# 资源/求番/番剧推荐沿用原动作，不含 approve
LEGACY_REVIEW_ACTIONS = ("recommend", "reject", "ban", "restore")

APPEAL_ACTIONS = ("accept", "reject")

BAN_REASON_MAX_LENGTH = 255
REVIEW_REASON_MAX_LENGTH = 255

POST_SELECT = (
    "SELECT p.id, p.user_id, p.title, p.category, p.tags, p.status, p.visibility, "
    "p.review_status, p.review_note, p.edit_count, p.publish_time, p.create_time, "
    "p.view_count, p.like_count, p.reply_count, "
    "u.username AS author_username, u.nickname AS author_nickname, u.avatar AS author_avatar "
    "FROM posts p JOIN users u ON u.id = p.user_id"
)


def _format_post(item):
    item["create_time"] = format_datetime(item["create_time"])
    item["publish_time"] = format_datetime(item["publish_time"])
    item["review_note"] = item["review_note"] or ""
    return item


@bp.get("/posts")
@admin_required
def list_posts():
    """全部帖子：GET /api/admin/posts?status=all|published|draft&reviewed=0|1&review_status=0&q=关键词

    reviewed=0 表示待审核（review_status=4），reviewed=1 表示已处理（review_status<>4）。
    """
    page, page_size = parse_page_args()
    status = request.args.get("status", "all")
    reviewed = clean(request.args.get("reviewed"))
    review_status = clean(request.args.get("review_status"))
    q = clean(request.args.get("q"))

    where = []
    args = []
    if status == "published":
        where.append("p.status=1")
    elif status == "draft":
        where.append("p.status=0")
    # 待审核 = review_status=4；已处理 = 已出评审结果（正常/推荐/打回/封禁）
    if reviewed == "1":
        where.append("p.review_status<>4")
    elif reviewed == "0":
        where.append("p.review_status=4")
    if review_status.isdigit():
        where.append("p.review_status=%s")
        args.append(int(review_status))
    if q:
        where.append("(p.title LIKE %s OR u.nickname LIKE %s)")
        like = f"%{q}%"
        args += [like, like]
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    count_sql = (
        "SELECT COUNT(*) AS total FROM posts p JOIN users u ON u.id = p.user_id" + where_sql
    )
    list_sql = POST_SELECT + where_sql + " ORDER BY p.create_time DESC, p.id DESC"
    items, total = paginate(count_sql, list_sql, args, page=page, page_size=page_size)
    return make_page_response([_format_post(item) for item in items], total, page, page_size)


@bp.put("/posts/<int:post_id>/review")
@admin_required
def review_post(post_id):
    """审查帖子：PUT /api/admin/posts/1/review，body {action, reason?}

    action: approve-通过 recommend-推荐 reject-打回 ban-封禁 restore-恢复
    """
    body = get_body()
    action = clean(body.get("action"))
    reason = clean(body.get("reason"))

    if action not in REVIEW_ACTIONS:
        return make_response(
            CODE_PARAM_ERROR, "action 只能是 approve、recommend、reject、ban 或 restore"
        )
    if action in REVIEW_REASON_REQUIRED and not reason:
        return make_response(CODE_PARAM_ERROR, "封禁或打回帖子时必须填写理由")
    if len(reason) > REVIEW_REASON_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"理由不能超过 {REVIEW_REASON_MAX_LENGTH} 字")

    item = query_one("SELECT id, user_id FROM posts WHERE id=%s", (post_id,))
    if item is None:
        return make_response(CODE_NOT_FOUND, "帖子不存在")

    review_status = REVIEW_ACTIONS[action]
    execute(
        "UPDATE posts SET review_status=%s, review_note=%s WHERE id=%s",
        (review_status, reason, post_id),
    )
    execute(
        "INSERT INTO post_review_logs (post_id, admin_id, action, reason) VALUES (%s, %s, %s, %s)",
        (post_id, g.current_user["id"], action, reason),
    )

    labels = {"approve": "已通过审核，帖子已公开", "ban": "已封禁该帖子",
              "reject": "已打回该帖子", "recommend": "已推荐该帖子",
              "restore": "已恢复该帖子"}
    return make_response(CODE_SUCCESS, labels[action], {
        "id": post_id,
        "review_status": review_status,
        "review_note": reason,
    })


# ===== 评论审查 =====

COMMENT_SELECT = (
    "SELECT r.id, r.user_id, r.post_id, r.parent_id, r.content, r.status, "
    "r.review_status, r.review_note, r.like_count, r.create_time, "
    "u.username AS author_username, u.nickname AS author_nickname, u.avatar AS author_avatar, "
    "p.title AS post_title "
    "FROM replies r JOIN users u ON u.id=r.user_id JOIN posts p ON p.id=r.post_id"
)


@bp.get("/comments")
@admin_required
def list_comments():
    """评论审查列表：GET /api/admin/comments?reviewed=0|1&review_status=0&q=关键词

    reviewed=0 表示待审核（review_status=4），reviewed=1 表示已处理（review_status<>4）。
    """
    page, page_size = parse_page_args()
    reviewed = clean(request.args.get("reviewed"))
    review_status = clean(request.args.get("review_status"))
    q = clean(request.args.get("q"))

    where = ["r.status=1"]
    args = []
    if reviewed == "1":
        where.append("r.review_status<>4")
    elif reviewed == "0":
        where.append("r.review_status=4")
    if review_status.isdigit():
        where.append("r.review_status=%s")
        args.append(int(review_status))
    if q:
        where.append("(u.nickname LIKE %s OR u.username LIKE %s OR r.content LIKE %s)")
        like = f"%{q}%"
        args += [like, like, like]
    where_sql = " WHERE " + " AND ".join(where)

    count_sql = (
        "SELECT COUNT(*) AS total FROM replies r JOIN users u ON u.id=r.user_id"
        + where_sql
    )
    list_sql = COMMENT_SELECT + where_sql + " ORDER BY r.create_time DESC, r.id DESC"
    items, total = paginate(count_sql, list_sql, args, page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["review_note"] = item["review_note"] or ""
    return make_page_response(items, total, page, page_size)


def _refresh_reply_count(post_id):
    """重算帖子回复数：仅统计「未删除且已通过审核（正常/推荐）」的评论。"""
    execute(
        "UPDATE posts SET reply_count=(SELECT COUNT(*) FROM replies "
        "WHERE post_id=%s AND status=1 AND review_status IN (0, 1)) WHERE id=%s",
        (post_id, post_id),
    )


@bp.put("/comments/<int:comment_id>/review")
@admin_required
def review_comment(comment_id):
    """审查评论：PUT /api/admin/comments/1/review，body {action, reason?}

    action: approve-通过 reject-打回 ban-封禁 restore-恢复；打回/封禁必填理由。
    审查后按「已通过且未删除」的评论数重算帖子回复数。
    """
    body = get_body()
    action = clean(body.get("action"))
    reason = clean(body.get("reason"))

    if action not in COMMENT_REVIEW_ACTIONS:
        return make_response(
            CODE_PARAM_ERROR, "action 只能是 approve、reject、ban 或 restore"
        )
    if action in REVIEW_REASON_REQUIRED and not reason:
        return make_response(CODE_PARAM_ERROR, "打回或封禁评论时必须填写理由")
    if len(reason) > REVIEW_REASON_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"理由不能超过 {REVIEW_REASON_MAX_LENGTH} 字")

    item = query_one(
        "SELECT id, post_id, review_status FROM replies WHERE id=%s AND status=1",
        (comment_id,),
    )
    if item is None:
        return make_response(CODE_NOT_FOUND, "评论不存在")

    review_status = COMMENT_REVIEW_ACTIONS[action]
    execute(
        "UPDATE replies SET review_status=%s, review_note=%s WHERE id=%s",
        (review_status, reason, comment_id),
    )
    _refresh_reply_count(item["post_id"])

    labels = {"approve": "已通过审核，评论已公开", "reject": "已打回该评论",
              "ban": "已封禁该评论", "restore": "已恢复该评论"}
    return make_response(CODE_SUCCESS, labels[action], {
        "id": comment_id,
        "review_status": review_status,
        "review_note": reason,
    })


@bp.get("/users")
@admin_required
def list_users():
    """用户列表：GET /api/admin/users?status=0|1|2&q=关键词"""
    page, page_size = parse_page_args()
    status = clean(request.args.get("status"))
    q = clean(request.args.get("q"))

    where = []
    args = []
    if status.isdigit():
        where.append("u.status=%s")
        args.append(int(status))
    if q:
        where.append("(u.username LIKE %s OR u.nickname LIKE %s OR u.email LIKE %s)")
        like = f"%{q}%"
        args += [like, like, like]
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    count_sql = "SELECT COUNT(*) AS total FROM users u" + where_sql
    list_sql = (
        "SELECT u.id, u.username, u.nickname, u.email, u.avatar, u.role, u.status, "
        "u.ban_reason, u.ban_time, u.followers_count, u.create_time, "
        "(SELECT COUNT(*) FROM posts p WHERE p.user_id=u.id AND p.status=1) AS posts_count "
        "FROM users u" + where_sql + " ORDER BY u.id DESC"
    )
    items, total = paginate(count_sql, list_sql, args, page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["ban_time"] = format_datetime(item["ban_time"])
        item["ban_reason"] = item["ban_reason"] or ""
    return make_page_response(items, total, page, page_size)


@bp.put("/users/<int:user_id>/ban")
@admin_required
def ban_user(user_id):
    """封禁账号：PUT /api/admin/users/2/ban，body {reason}（必填）

    封禁后：可登录、禁止发帖评论、已发布帖子全部转为私密。
    """
    reason = clean(get_body().get("reason"))
    if not reason:
        return make_response(CODE_PARAM_ERROR, "封禁账号必须填写理由")
    if len(reason) > BAN_REASON_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"理由不能超过 {BAN_REASON_MAX_LENGTH} 字")

    user = query_one("SELECT id, role, status FROM users WHERE id=%s", (user_id,))
    if user is None:
        return make_response(CODE_NOT_FOUND, "用户不存在")
    if user["role"] == 1:
        return make_response(CODE_NO_PERMISSION, "不能封禁管理员账号")
    if user_id == g.current_user["id"]:
        return make_response(CODE_NO_PERMISSION, "不能封禁自己")
    if user["status"] == STATUS_BANNED:
        return make_response(CODE_PARAM_ERROR, "该账号已被封禁")

    execute(
        "UPDATE users SET status=%s, ban_reason=%s, ban_time=NOW(), ban_admin_id=%s WHERE id=%s",
        (STATUS_BANNED, reason, g.current_user["id"], user_id),
    )
    # 已发布的帖子被动转为私密
    execute(
        "UPDATE posts SET visibility=1 WHERE user_id=%s AND status=1",
        (user_id,),
    )
    return make_response(CODE_SUCCESS, "已封禁该账号", {"id": user_id, "status": STATUS_BANNED})


@bp.put("/users/<int:user_id>/unban")
@admin_required
def unban_user(user_id):
    """解除封禁：PUT /api/admin/users/2/unban"""
    user = query_one("SELECT id, status FROM users WHERE id=%s", (user_id,))
    if user is None:
        return make_response(CODE_NOT_FOUND, "用户不存在")
    if user["status"] != STATUS_BANNED:
        return make_response(CODE_PARAM_ERROR, "该账号当前未被封禁")

    execute(
        "UPDATE users SET status=%s, ban_reason='', ban_time=NULL, ban_admin_id=NULL WHERE id=%s",
        (STATUS_NORMAL, user_id),
    )
    return make_response(CODE_SUCCESS, "已解除封禁", {"id": user_id, "status": STATUS_NORMAL})


@bp.put("/users/<int:user_id>/disable")
@admin_required
def disable_user(user_id):
    """禁用账号：PUT /api/admin/users/2/disable

    禁用后该账号无法登录（登录返回 1006），可随时启用；不涉及已发布内容。
    """
    user = query_one("SELECT id, role, status FROM users WHERE id=%s", (user_id,))
    if user is None:
        return make_response(CODE_NOT_FOUND, "用户不存在")
    if user["role"] == 1:
        return make_response(CODE_NO_PERMISSION, "不能禁用管理员账号")
    if user_id == g.current_user["id"]:
        return make_response(CODE_NO_PERMISSION, "不能禁用自己")
    if user["status"] == STATUS_DISABLED:
        return make_response(CODE_PARAM_ERROR, "该账号已被禁用")

    execute("UPDATE users SET status=%s WHERE id=%s", (STATUS_DISABLED, user_id))
    return make_response(CODE_SUCCESS, "已禁用该账号，用户将无法登录", {
        "id": user_id, "status": STATUS_DISABLED,
    })


@bp.put("/users/<int:user_id>/enable")
@admin_required
def enable_user(user_id):
    """启用账号：PUT /api/admin/users/2/enable（解除禁用，恢复登录）"""
    user = query_one("SELECT id, status FROM users WHERE id=%s", (user_id,))
    if user is None:
        return make_response(CODE_NOT_FOUND, "用户不存在")
    if user["status"] != STATUS_DISABLED:
        return make_response(CODE_PARAM_ERROR, "该账号当前未被禁用")

    execute("UPDATE users SET status=%s WHERE id=%s", (STATUS_NORMAL, user_id))
    return make_response(CODE_SUCCESS, "已启用该账号", {"id": user_id, "status": STATUS_NORMAL})


@bp.get("/appeals")
@admin_required
def list_appeals():
    """申诉列表：GET /api/admin/appeals?status=0|1|2&q=关键词"""
    page, page_size = parse_page_args()
    status = clean(request.args.get("status"))
    q = clean(request.args.get("q"))

    where = []
    args = []
    if status.isdigit():
        where.append("a.status=%s")
        args.append(int(status))
    if q:
        like = f"%{q}%"
        where.append("(u.username LIKE %s OR u.nickname LIKE %s OR a.reason LIKE %s)")
        args += [like, like, like]
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    count_sql = (
        "SELECT COUNT(*) AS total FROM appeals a JOIN users u ON u.id = a.user_id" + where_sql
    )
    list_sql = (
        "SELECT a.id, a.user_id, a.reason, a.status, a.admin_note, "
        "a.create_time, a.handle_time, u.username, u.nickname, u.avatar, u.ban_reason "
        "FROM appeals a JOIN users u ON u.id = a.user_id" + where_sql
        + " ORDER BY a.status ASC, a.create_time DESC, a.id DESC"
    )
    items, total = paginate(count_sql, list_sql, args, page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["handle_time"] = format_datetime(item["handle_time"])
        item["admin_note"] = item["admin_note"] or ""
        item["ban_reason"] = item["ban_reason"] or ""
    return make_page_response(items, total, page, page_size)


@bp.put("/appeals/<int:appeal_id>")
@admin_required
def handle_appeal(appeal_id):
    """处理申诉：PUT /api/admin/appeals/1，body {action: accept|reject, note?}"""
    body = get_body()
    action = clean(body.get("action"))
    note = clean(body.get("note"))

    if action not in APPEAL_ACTIONS:
        return make_response(CODE_PARAM_ERROR, "action 只能是 accept 或 reject")
    if len(note) > REVIEW_REASON_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"处理备注不能超过 {REVIEW_REASON_MAX_LENGTH} 字")

    item = query_one(
        "SELECT id, user_id, status FROM appeals WHERE id=%s",
        (appeal_id,),
    )
    if item is None:
        return make_response(CODE_NOT_FOUND, "申诉不存在")
    if item["status"] != 0:
        return make_response(CODE_PARAM_ERROR, "该申诉已处理")

    if action == "accept":
        execute(
            "UPDATE appeals SET status=1, admin_note=%s, handle_time=NOW() WHERE id=%s",
            (note, appeal_id),
        )
        execute(
            "UPDATE users SET status=%s, ban_reason='', ban_time=NULL, ban_admin_id=NULL WHERE id=%s",
            (STATUS_NORMAL, item["user_id"]),
        )
        return make_response(CODE_SUCCESS, "申诉已通过，账号已解封")

    execute(
        "UPDATE appeals SET status=2, admin_note=%s, handle_time=NOW() WHERE id=%s",
        (note, appeal_id),
    )
    return make_response(CODE_SUCCESS, "申诉已驳回")


@bp.get("/stats")
@admin_required
def stats():
    """后台概览：GET /api/admin/stats"""
    return make_response(CODE_SUCCESS, "获取成功", _overview_stats())


def _overview_stats():
    """后台概览统计（stats 与 dashboard 共用）。"""
    users_total = query_one("SELECT COUNT(*) AS total FROM users")["total"]
    posts_total = query_one("SELECT COUNT(*) AS total FROM posts WHERE status=1")["total"]
    pending_posts = query_one(
        "SELECT COUNT(*) AS total FROM posts WHERE status=1 AND review_status=4"
    )["total"]
    pending_comments = query_one(
        "SELECT COUNT(*) AS total FROM replies WHERE status=1 AND review_status=4"
    )["total"]
    banned_users = query_one(
        "SELECT COUNT(*) AS total FROM users WHERE status=%s", (STATUS_BANNED,)
    )["total"]
    disabled_users = query_one(
        "SELECT COUNT(*) AS total FROM users WHERE status=%s", (STATUS_DISABLED,)
    )["total"]
    pending_appeals = query_one(
        "SELECT COUNT(*) AS total FROM appeals WHERE status=0"
    )["total"]
    unreviewed_resources = query_one(
        "SELECT COUNT(*) AS total FROM resources WHERE review_status=0"
    )["total"]
    unreviewed_requests = query_one(
        "SELECT COUNT(*) AS total FROM anime_requests WHERE review_status=0"
    )["total"]
    pending_identity = query_one(
        "SELECT COUNT(*) AS total FROM identity_applications WHERE status=0"
    )["total"]
    return {
        "users_total": int(users_total),
        "posts_total": int(posts_total),
        "pending_posts": int(pending_posts),
        "pending_comments": int(pending_comments),
        "banned_users": int(banned_users),
        "disabled_users": int(disabled_users),
        "pending_appeals": int(pending_appeals),
        "unreviewed_resources": int(unreviewed_resources),
        "unreviewed_requests": int(unreviewed_requests),
        "pending_identity": int(pending_identity),
    }


@bp.get("/dashboard")
@admin_required
def dashboard():
    """看板数据：GET /api/admin/dashboard

    - stats:         概览统计（同 /api/admin/stats）
    - trends:        近 14 天新增用户/帖子/评论趋势（缺失日期补 0）
    - post_status:   已发布帖子审查状态分布 {0正常 1推荐 2打回 3封禁 4待审核}
    - comment_status:评论审查状态分布
    - category_top:  帖子分类排行（Top 8）
    - todos:         待办清单（数量 + 跳转目标）
    """
    from datetime import datetime, timedelta

    stats_data = _overview_stats()

    today = datetime.now()
    start = today - timedelta(days=13)
    days = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(14)]
    since = start.strftime("%Y-%m-%d 00:00:00")

    def _daily_trend(table, column):
        rows = query_all(
            f"SELECT DATE({column}) AS day, COUNT(*) AS cnt "
            f"FROM {table} WHERE {column} >= %s AND {column} < "
            f"DATE_ADD(CURDATE(), INTERVAL 1 DAY) GROUP BY day",
            (since,),
        )
        counts = {}
        for row in rows:
            day = row["day"]
            key = day.strftime("%Y-%m-%d") if hasattr(day, "strftime") else str(day)
            counts[key] = int(row["cnt"])
        return [counts.get(day, 0) for day in days]

    def _status_dist(table, extra=""):
        rows = query_all(
            f"SELECT review_status AS k, COUNT(*) AS cnt FROM {table} "
            f"{extra} GROUP BY review_status"
        )
        return {int(row["k"]): int(row["cnt"]) for row in rows}

    post_status = _status_dist("posts", "WHERE status=1")
    comment_status = _status_dist("replies", "WHERE status=1")

    category_rows = query_all(
        "SELECT category AS name, COUNT(*) AS cnt FROM posts "
        "WHERE status=1 AND category<>'' GROUP BY category "
        "ORDER BY cnt DESC, category ASC LIMIT 8"
    )

    todos = [
        {"type": "posts", "label": "待审核帖子", "count": int(post_status.get(4, 0)),
         "target": "posts", "source": "posts"},
        {"type": "comments", "label": "待审核评论", "count": int(comment_status.get(4, 0)),
         "target": "posts", "source": "comments"},
        {"type": "resources", "label": "待审资源", "count": stats_data["unreviewed_resources"],
         "target": "posts", "source": "resources"},
        {"type": "requests", "label": "待审求番", "count": stats_data["unreviewed_requests"],
         "target": "posts", "source": "requests"},
        {"type": "identity", "label": "待审身份申请", "count": stats_data["pending_identity"],
         "target": "identity"},
        {"type": "appeals", "label": "待处理申诉", "count": stats_data["pending_appeals"],
         "target": "appeals"},
    ]

    return make_response(CODE_SUCCESS, "获取成功", {
        "stats": stats_data,
        "trends": {
            "days": days,
            "users": _daily_trend("users", "create_time"),
            "posts": _daily_trend("posts", "create_time"),
            "replies": _daily_trend("replies", "create_time"),
        },
        "post_status": post_status,
        "comment_status": comment_status,
        "category_top": [{"name": row["name"], "count": int(row["cnt"])} for row in category_rows],
        "todos": todos,
    })


# ===== 资源分享审查 =====

RESOURCE_SELECT = (
    "SELECT r.id, r.user_id, r.title, r.description, r.link, r.visibility, "
    "r.review_status, r.review_note, r.create_time, "
    "u.username AS author_username, u.nickname AS author_nickname "
    "FROM resources r JOIN users u ON u.id = r.user_id"
)


def _parse_review_body():
    """解析审查动作，返回 (action, reason, 错误响应)。

    资源/求番/番剧推荐沿用原动作（不含 approve，它们的 review_status=0 表示未评审）。
    """
    body = get_body()
    action = clean(body.get("action"))
    reason = clean(body.get("reason"))
    if action not in LEGACY_REVIEW_ACTIONS:
        return None, None, make_response(
            CODE_PARAM_ERROR, "action 只能是 recommend、reject、ban 或 restore"
        )
    if action in REVIEW_REASON_REQUIRED and not reason:
        return None, None, make_response(CODE_PARAM_ERROR, "封禁或打回时必须填写理由")
    if len(reason) > REVIEW_REASON_MAX_LENGTH:
        return None, None, make_response(
            CODE_PARAM_ERROR, f"理由不能超过 {REVIEW_REASON_MAX_LENGTH} 字"
        )
    return action, reason, None


def _moderation_filters(prefix, alias="u"):
    """构造「评审状态 + 评审结果 + 关键词」的公共筛选条件。"""
    reviewed = clean(request.args.get("reviewed"))
    review_status = clean(request.args.get("review_status"))
    q = clean(request.args.get("q"))

    where = []
    args = []
    if reviewed == "1":
        where.append(f"{prefix}.review_status<>0")
    elif reviewed == "0":
        where.append(f"{prefix}.review_status=0")
    if review_status.isdigit():
        where.append(f"{prefix}.review_status=%s")
        args.append(int(review_status))
    if q:
        like = f"%{q}%"
        where.append(f"(u.nickname LIKE %s OR u.username LIKE %s)")

        args += [like, like]
    return where, args


@bp.get("/resources")
@admin_required
def list_resources():
    """资源审查列表：GET /api/admin/resources?reviewed=0|1&review_status=0&q=关键词"""
    page, page_size = parse_page_args()
    where, args = _moderation_filters("r")
    q = clean(request.args.get("q"))
    if q:
        # 关键词还支持资源标题
        where[-1] = f"(r.title LIKE %s OR u.nickname LIKE %s OR u.username LIKE %s)"
        args.append(args[-1])
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    count_sql = "SELECT COUNT(*) AS total FROM resources r JOIN users u ON u.id=r.user_id" + where_sql
    list_sql = RESOURCE_SELECT + where_sql + " ORDER BY r.create_time DESC, r.id DESC"
    items, total = paginate(count_sql, list_sql, args, page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["description"] = item["description"] or ""
        item["review_note"] = item["review_note"] or ""
    return make_page_response(items, total, page, page_size)


@bp.put("/resources/<int:resource_id>/review")
@admin_required
def review_resource(resource_id):
    """审查资源：PUT /api/admin/resources/1/review，body {action, reason?}"""
    action, reason, error = _parse_review_body()
    if error:
        return error

    if query_one("SELECT id FROM resources WHERE id=%s", (resource_id,)) is None:
        return make_response(CODE_NOT_FOUND, "资源不存在")

    review_status = REVIEW_ACTIONS[action]
    execute(
        "UPDATE resources SET review_status=%s, review_note=%s WHERE id=%s",
        (review_status, reason, resource_id),
    )
    labels = {"ban": "已封禁该资源", "reject": "已打回该资源",
              "recommend": "已推荐该资源", "restore": "已恢复该资源"}
    return make_response(CODE_SUCCESS, labels[action], {
        "id": resource_id, "review_status": review_status, "review_note": reason,
    })


# ===== 求番审查 =====

REQUEST_SELECT = (
    "SELECT r.id, r.user_id, r.anime_name, r.reason, r.status, r.review_status, "
    "r.review_note, r.create_time, u.username AS author_username, "
    "u.nickname AS author_nickname FROM anime_requests r JOIN users u ON u.id = r.user_id"
)


@bp.get("/anime-requests")
@admin_required
def list_anime_requests():
    """求番审查列表：GET /api/admin/anime-requests?reviewed=0|1&review_status=0&q=关键词"""
    page, page_size = parse_page_args()
    where, args = _moderation_filters("r")
    q = clean(request.args.get("q"))
    if q:
        where[-1] = "(r.anime_name LIKE %s OR u.nickname LIKE %s OR u.username LIKE %s)"
        args.append(args[-1])
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    count_sql = (
        "SELECT COUNT(*) AS total FROM anime_requests r JOIN users u ON u.id=r.user_id" + where_sql
    )
    list_sql = REQUEST_SELECT + where_sql + " ORDER BY r.create_time DESC, r.id DESC"
    items, total = paginate(count_sql, list_sql, args, page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["reason"] = item["reason"] or ""
        item["review_note"] = item["review_note"] or ""
    return make_page_response(items, total, page, page_size)


@bp.put("/anime-requests/<int:request_id>/review")
@admin_required
def review_anime_request(request_id):
    """审查求番：PUT /api/admin/anime-requests/1/review，body {action, reason?}

    推荐即视为已收录（status=1），恢复会回到待收录。
    """
    action, reason, error = _parse_review_body()
    if error:
        return error

    item = query_one("SELECT id FROM anime_requests WHERE id=%s", (request_id,))
    if item is None:
        return make_response(CODE_NOT_FOUND, "求番不存在")

    review_status = REVIEW_ACTIONS[action]
    collected = 1 if action == "recommend" else (0 if action == "restore" else None)
    if collected is None:
        execute(
            "UPDATE anime_requests SET review_status=%s, review_note=%s WHERE id=%s",
            (review_status, reason, request_id),
        )
    else:
        execute(
            "UPDATE anime_requests SET review_status=%s, review_note=%s, status=%s WHERE id=%s",
            (review_status, reason, collected, request_id),
        )
    labels = {"ban": "已封禁该求番", "reject": "已打回该求番",
              "recommend": "已收录该番剧", "restore": "已恢复为待收录"}
    return make_response(CODE_SUCCESS, labels[action], {
        "id": request_id, "review_status": review_status, "review_note": reason,
    })


# ===== 番剧推荐审查 =====

RECOMMENDATION_SELECT = (
    "SELECT r.id, r.user_id, r.anime_name, r.link, r.reason, r.review_status, "
    "r.review_note, r.create_time, u.username AS author_username, "
    "u.nickname AS author_nickname FROM anime_recommendations r "
    "JOIN users u ON u.id = r.user_id"
)


@bp.get("/anime-recommendations")
@admin_required
def list_anime_recommendations():
    """番剧推荐审查列表：GET /api/admin/anime-recommendations?reviewed=0|1&review_status=0&q=关键词"""
    page, page_size = parse_page_args()
    where, args = _moderation_filters("r")
    q = clean(request.args.get("q"))
    if q:
        where[-1] = "(r.anime_name LIKE %s OR u.nickname LIKE %s OR u.username LIKE %s)"
        args.append(args[-1])
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    count_sql = (
        "SELECT COUNT(*) AS total FROM anime_recommendations r "
        "JOIN users u ON u.id=r.user_id" + where_sql
    )
    list_sql = RECOMMENDATION_SELECT + where_sql + " ORDER BY r.create_time DESC, r.id DESC"
    items, total = paginate(count_sql, list_sql, args, page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["reason"] = item["reason"] or ""
        item["review_note"] = item["review_note"] or ""
    return make_page_response(items, total, page, page_size)


@bp.put("/anime-recommendations/<int:recommendation_id>/review")
@admin_required
def review_anime_recommendation(recommendation_id):
    """审查番剧推荐：PUT /api/admin/anime-recommendations/1/review，body {action, reason?}"""
    action, reason, error = _parse_review_body()
    if error:
        return error

    if query_one(
        "SELECT id FROM anime_recommendations WHERE id=%s", (recommendation_id,)
    ) is None:
        return make_response(CODE_NOT_FOUND, "推荐不存在")

    review_status = REVIEW_ACTIONS[action]
    execute(
        "UPDATE anime_recommendations SET review_status=%s, review_note=%s WHERE id=%s",
        (review_status, reason, recommendation_id),
    )
    labels = {"ban": "已封禁该推荐", "reject": "已打回该推荐",
              "recommend": "已推荐该番剧", "restore": "已恢复该推荐"}
    return make_response(CODE_SUCCESS, labels[action], {
        "id": recommendation_id, "review_status": review_status, "review_note": reason,
    })


# ===== 身份申请审批 =====

IDENTITY_THRESHOLD = 20


@bp.get("/identity-applications")
@admin_required
def list_identity_applications():
    """身份申请列表：GET /api/admin/identity-applications?status=0&q=关键词"""
    page, page_size = parse_page_args()
    status = clean(request.args.get("status"))
    q = clean(request.args.get("q"))

    where = []
    args = []
    if status.isdigit():
        where.append("a.status=%s")
        args.append(int(status))
    if q:
        like = f"%{q}%"
        where.append("(u.username LIKE %s OR u.nickname LIKE %s)")
        args += [like, like]
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    count_sql = (
        "SELECT COUNT(*) AS total FROM identity_applications a "
        "JOIN users u ON u.id = a.user_id" + where_sql
    )
    list_sql = (
        "SELECT a.id, a.user_id, a.identity_type, a.reason, a.status, a.admin_note, "
        "a.create_time, a.handle_time, u.username, u.nickname, u.avatar, u.identity, "
        "(SELECT COUNT(*) FROM anime_recommendations ar "
        " WHERE ar.user_id=a.user_id AND ar.review_status=1) AS anime_valid, "
        "(SELECT COUNT(*) FROM resources rs "
        " WHERE rs.user_id=a.user_id AND rs.review_status=1) AS resource_valid "
        "FROM identity_applications a JOIN users u ON u.id = a.user_id" + where_sql
        + " ORDER BY a.status ASC, a.create_time DESC, a.id DESC"
    )
    items, total = paginate(count_sql, list_sql, args, page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["handle_time"] = format_datetime(item["handle_time"])
        item["identity_label"] = IDENTITY_META.get(item["identity_type"], {}).get("label", "")
        item["reason"] = item["reason"] or ""
        item["admin_note"] = item["admin_note"] or ""
        item["identity"] = item["identity"] or ""
    return make_page_response(items, total, page, page_size)


@bp.put("/identity-applications/<int:application_id>")
@admin_required
def handle_identity_application(application_id):
    """审批身份申请：PUT /api/admin/identity-applications/1，body {action, note?}

    action=accept 通过（授予称号），action=reject 驳回。
    """
    body = get_body()
    action = clean(body.get("action"))
    note = clean(body.get("note"))
    if action not in ("accept", "reject"):
        return make_response(CODE_PARAM_ERROR, "action 只能是 accept 或 reject")
    if len(note) > REVIEW_REASON_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"审批备注不能超过 {REVIEW_REASON_MAX_LENGTH} 字")

    item = query_one(
        "SELECT id, user_id, identity_type, status FROM identity_applications WHERE id=%s",
        (application_id,),
    )
    if item is None:
        return make_response(CODE_NOT_FOUND, "身份申请不存在")
    if item["status"] != 0:
        return make_response(CODE_PARAM_ERROR, "该申请已处理")

    label = IDENTITY_META.get(item["identity_type"], {}).get("label", "特殊身份")
    user_id = item["user_id"]

    if action == "accept":
        table = IDENTITY_META[item["identity_type"]]["table"]
        valid = query_one(
            f"SELECT COUNT(*) AS total FROM {table} WHERE user_id=%s AND review_status=1",
            (user_id,),
        )["total"]
        if int(valid) < IDENTITY_THRESHOLD:
            return make_response(
                CODE_PARAM_ERROR,
                f"该用户当前有效记录仅 {int(valid)} 条，未达到 {IDENTITY_THRESHOLD} 条",
            )

        user = query_one("SELECT identity FROM users WHERE id=%s", (user_id,))
        codes = identity_codes(user["identity"] if user else "")
        if item["identity_type"] not in codes:
            codes.append(item["identity_type"])
        execute(
            "UPDATE users SET identity=%s WHERE id=%s", (",".join(codes), user_id)
        )
        execute(
            "UPDATE identity_applications SET status=1, admin_note=%s, handle_admin_id=%s, "
            "handle_time=NOW() WHERE id=%s",
            (note, g.current_user["id"], application_id),
        )
        execute(
            "INSERT INTO notifications (user_id, type, title, content, link) "
            "VALUES (%s, 'identity', %s, %s, '/profile/identity')",
            (user_id, "身份申请已通过", f"恭喜获得「{label}」称号，未公开奖励将由管理员发放"),
        )
        return make_response(CODE_SUCCESS, f"已通过，授予「{label}」称号")

    execute(
        "UPDATE identity_applications SET status=2, admin_note=%s, handle_admin_id=%s, "
        "handle_time=NOW() WHERE id=%s",
        (note, g.current_user["id"], application_id),
    )
    execute(
        "INSERT INTO notifications (user_id, type, title, content, link) "
        "VALUES (%s, 'identity', %s, %s, '/profile/identity')",
        (user_id, "身份申请未通过", f"「{label}」申请被驳回" + (f"：{note}" if note else "")),
    )
    return make_response(CODE_SUCCESS, "已驳回该申请")
