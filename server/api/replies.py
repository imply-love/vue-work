"""评论（回帖）接口：支持多级树形评论。

审查规则：新发表的评论默认「待审核」（review_status=4），
作者本人可在内容管理看到自己的评论，审核通过（0/1）后才对外展示。

- GET    /api/posts/<post_id>/replies       平铺评论列表（分页，兼容旧接口）
- GET    /api/posts/<post_id>/replies/tree  树形评论（多级多分支，一次性返回）
- POST   /api/posts/<post_id>/replies       发表评论/回复（需登录，parent_id 指定父评论）
- DELETE /api/replies/<id>                  删除自己的评论（作者或管理员）
- GET    /api/user/replies                  我的评论（内容管理）
"""
from flask import Blueprint, g

from api.posts import (
    REVIEW_BANNED,
    REVIEW_NORMAL,
    REVIEW_PENDING,
    REVIEW_RETURNED,
    can_view_post,
)
from db import execute, paginate, query_all, query_one
from utils.auth import ensure_not_banned, login_required, try_get_current_user
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

bp = Blueprint("replies", __name__, url_prefix="/api")

# 评论正文上限（与回帖表 TEXT 列匹配，超长直接 1001）
CONTENT_MAX_LENGTH = 500

# 对外可见的评论审查状态：正常 / 推荐
VISIBLE_REVIEW = (REVIEW_NORMAL, 1)

# 树形评论一次最多返回的节点数，避免超大帖子拖慢接口
TREE_MAX_NODES = 2000

LIST_SELECT = (
    "SELECT r.id, r.user_id, r.post_id, r.parent_id, r.content, r.like_count, "
    "r.review_status, r.review_note, r.create_time, "
    "u.nickname AS author_nickname, u.avatar AS author_avatar "
    "FROM replies r JOIN users u ON u.id = r.user_id"
)


def _refresh_reply_count(post_id):
    """重算帖子回复数：仅统计「未删除且已通过审核（正常/推荐）」的评论。

    评论审核通过/打回/封禁、删除评论后调用，保证对外展示的数字与实际可见评论一致。
    """
    execute(
        "UPDATE posts SET reply_count=(SELECT COUNT(*) FROM replies "
        "WHERE post_id=%s AND status=1 AND review_status IN (0, 1)) WHERE id=%s",
        (post_id, post_id),
    )


def _check_viewable_post(post_id):
    """帖子存在且当前用户可见才允许查看/发表评论，返回 (post, 错误响应)。"""
    post = query_one(
        "SELECT id, user_id, status, visibility, review_status FROM posts WHERE id=%s",
        (post_id,),
    )
    if post is None or post["status"] != 1:
        return None, make_response(CODE_NOT_FOUND, "帖子不存在或未发布")
    if post["review_status"] in (REVIEW_PENDING, REVIEW_RETURNED, REVIEW_BANNED):
        return None, make_response(CODE_NOT_FOUND, "帖子不存在或未发布")
    user = try_get_current_user()
    if not can_view_post(post, user):
        return None, make_response(CODE_NOT_FOUND, "帖子不存在")
    return post, None


def _build_tree(rows):
    """把平铺评论按 parent_id 组装成多级树。

    父评论已被删除（status=0 被过滤）时，子评论提升为顶层，避免整条分支消失。
    """
    nodes = {}
    for row in rows:
        row["create_time"] = format_datetime(row["create_time"])
        row["children"] = []
        nodes[row["id"]] = row

    roots = []
    for row in rows:
        parent_id = row["parent_id"]
        parent = nodes.get(parent_id)
        if parent is not None and parent_id != row["id"]:
            parent["children"].append(row)
        else:
            roots.append(row)
    return roots


@bp.get("/posts/<int:post_id>/replies")
def list_replies(post_id):
    """平铺评论列表：GET /api/posts/1/replies?page=1&page_size=20（按时间正序）"""
    _, err = _check_viewable_post(post_id)
    if err is not None:
        return err

    page, page_size = parse_page_args()
    visible_sql = "r.post_id=%s AND r.status=1 AND r.review_status IN (0, 1)"
    list_sql = LIST_SELECT + " WHERE " + visible_sql + " ORDER BY r.create_time ASC, r.id ASC"
    count_sql = "SELECT COUNT(*) AS total FROM replies r WHERE " + visible_sql
    items, total = paginate(count_sql, list_sql, (post_id,), page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["review_note"] = item["review_note"] or ""
    return make_page_response(items, total, page, page_size)


@bp.get("/posts/<int:post_id>/replies/tree")
def list_reply_tree(post_id):
    """树形评论：GET /api/posts/1/replies/tree（多级多分支，按时间正序）"""
    _, err = _check_viewable_post(post_id)
    if err is not None:
        return err

    rows = query_all(
        LIST_SELECT + " WHERE r.post_id=%s AND r.status=1 AND r.review_status IN (0, 1) "
        "ORDER BY r.create_time ASC, r.id ASC LIMIT %s",
        (post_id, TREE_MAX_NODES),
    )
    roots = _build_tree(rows)
    return make_response(CODE_SUCCESS, "获取成功", {
        "list": roots,
        "total": len(rows),
    })


@bp.post("/posts/<int:post_id>/replies")
@login_required
def create_reply(post_id):
    """发表评论/回复：POST /api/posts/1/replies，body {content, parent_id?}

    parent_id 缺省为 0（直接评论）；回复某条评论时传该评论 ID。
    """
    banned = ensure_not_banned()
    if banned:
        return banned

    _, err = _check_viewable_post(post_id)
    if err is not None:
        return err

    body = get_body()
    content = clean(body.get("content"))
    raw_parent = clean(body.get("parent_id")) or "0"

    missing = require(body, "content")
    if missing:
        return make_response(CODE_PARAM_ERROR, f"缺少必填参数：{'、'.join(missing)}")
    if len(content) > CONTENT_MAX_LENGTH:
        return make_response(
            CODE_PARAM_ERROR, f"评论长度不能超过 {CONTENT_MAX_LENGTH} 字"
        )
    if not raw_parent.isdigit():
        return make_response(CODE_PARAM_ERROR, "parent_id 需为数字")
    parent_id = int(raw_parent)
    if parent_id:
        # 只能回复「已通过审核且未删除」的评论（待审核评论尚未公开）
        parent = query_one(
            "SELECT id FROM replies WHERE id=%s AND post_id=%s AND status=1 "
            "AND review_status IN (0, 1)",
            (parent_id, post_id),
        )
        if parent is None:
            return make_response(CODE_NOT_FOUND, "回复的评论不存在")

    user_id = g.current_user["id"]
    reply_id = execute(
        "INSERT INTO replies (post_id, user_id, parent_id, content, review_status) "
        "VALUES (%s, %s, %s, %s, %s)",
        (post_id, user_id, parent_id, content, REVIEW_PENDING),
    )
    # 待审核评论暂不计入 reply_count，审核通过后在管理端重算

    row = query_one(
        "SELECT r.id, r.user_id, r.post_id, r.parent_id, r.content, r.like_count, "
        "r.review_status, r.review_note, r.create_time, "
        "u.nickname AS author_nickname, u.avatar AS author_avatar "
        "FROM replies r JOIN users u ON u.id=r.user_id WHERE r.id=%s",
        (reply_id,),
    )
    row["create_time"] = format_datetime(row["create_time"])
    row["review_note"] = row["review_note"] or ""
    row["children"] = []
    return make_response(CODE_SUCCESS, "评论已提交，审核通过后将公开展示", row)


@bp.delete("/replies/<int:reply_id>")
@login_required
def delete_reply(reply_id):
    """删除评论：DELETE /api/replies/1（评论作者或管理员）

    采用软删除（status=0），并把直接子评论上提到被删评论的父级，
    保证楼中楼分支不会因为删除中间节点而消失。
    """
    user_id = g.current_user["id"]
    reply = query_one(
        "SELECT id, post_id, user_id, parent_id FROM replies WHERE id=%s AND status=1",
        (reply_id,),
    )
    if reply is None:
        return make_response(CODE_NOT_FOUND, "评论不存在")
    if reply["user_id"] != user_id and g.current_user.get("role") != 1:
        return make_response(CODE_NO_PERMISSION, "只能删除自己的评论")

    execute("UPDATE replies SET status=0 WHERE id=%s", (reply_id,))
    execute(
        "UPDATE replies SET parent_id=%s WHERE parent_id=%s AND status=1",
        (reply["parent_id"], reply_id),
    )
    _refresh_reply_count(reply["post_id"])
    return make_response(CODE_SUCCESS, "评论已删除", {"id": reply_id})


@bp.get("/user/replies")
@login_required
def list_my_replies():
    """我的评论列表：GET /api/user/replies?page=1&page_size=10（内容管理用）

    与公开列表不同：包含自己全部未删除的评论（含待审核/被打回/被封禁），
    并用 review_status / review_note 告诉作者当前审查状态。
    """
    user_id = g.current_user["id"]
    page, page_size = parse_page_args()
    count_sql = "SELECT COUNT(*) AS total FROM replies WHERE user_id=%s AND status=1"
    list_sql = (
        "SELECT r.id, r.post_id, r.parent_id, r.content, r.review_status, "
        "r.review_note, r.create_time, p.title AS post_title "
        "FROM replies r JOIN posts p ON p.id=r.post_id "
        "WHERE r.user_id=%s AND r.status=1 "
        "ORDER BY r.create_time DESC, r.id DESC"
    )
    items, total = paginate(count_sql, list_sql, (user_id,), page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
        item["review_note"] = item["review_note"] or ""
    return make_page_response(items, total, page, page_size)
