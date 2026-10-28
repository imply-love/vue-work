"""帖子接口：公开分页 + 登录发帖/草稿/内容管理。

可见性（visibility）：0-公开 1-私密 2-仅好友
审查状态（review_status）：0-正常 1-推荐 2-打回 3-封禁

- GET    /api/posts              公开列表（公开 + 好友可见的帖子）
- GET    /api/posts/drafts       我的草稿列表（需登录）
- GET    /api/posts/mine         我的帖子（含草稿/被打回/被封禁，需登录）
- POST   /api/posts              发布新帖 / 保存草稿（需登录，封禁账号禁止）
- GET    /api/posts/<id>         帖子详情（按可见性鉴权）
- POST   /api/posts/<id>/like    点赞 / 取消点赞切换（需登录）
- PUT    /api/posts/<id>         更新自己的帖子/草稿（仅作者）
- PUT    /api/posts/<id>/visibility  快速设置可见性（仅作者）
- DELETE /api/posts/<id>         删除自己的帖子/草稿（仅作者）
"""
import re

from flask import Blueprint, g, request

from db import execute, paginate, query_one
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

bp = Blueprint("posts", __name__, url_prefix="/api")

VISIBILITY_PUBLIC = 0
VISIBILITY_PRIVATE = 1
VISIBILITY_FRIENDS = 2
VISIBILITY_VALUES = (VISIBILITY_PUBLIC, VISIBILITY_PRIVATE, VISIBILITY_FRIENDS)

REVIEW_NORMAL = 0
REVIEW_RECOMMEND = 1
REVIEW_RETURNED = 2
REVIEW_BANNED = 3
# 待审核：帖子已提交但未过审，作者始终可见，对外不公开；管理员通过后才进入公开列表
REVIEW_PENDING = 4

# 与 posts 表字段长度保持一致，超长直接返回 1001，避免落库时报数据库错误
TITLE_MAX_LENGTH = 200
CONTENT_MAX_LENGTH = 20000
COVER_MAX_LENGTH = 255
TAGS_MAX_LENGTH = 255
SUMMARY_MAX_LENGTH = 255
CATEGORY_MAX_LENGTH = 30

# 卡片摘要最大长度（前端卡片最多显示两行）
EXCERPT_MAX_LENGTH = 120

# 列表排序白名单：sort 参数只接受这些值，非法值回退 latest
SORT_WHITELIST = {
    "latest": "p.publish_time DESC, p.id DESC",
    # 参考 twitter/the-algorithm 的加权思路：互动行为按权重相加后排序
    "hot": "(p.like_count * 3 + p.reply_count * 2 + p.view_count) DESC, p.publish_time DESC, p.id DESC",
    "replies": "p.reply_count DESC, p.publish_time DESC, p.id DESC",
    # 管理员推荐的帖子优先展示
    "recommended": "(p.review_status = 1) DESC, p.publish_time DESC, p.id DESC",
}

# 列表与详情共用的字段：列表只取正文前 400 字符作摘要，详情取全文
LIST_SELECT = (
    "SELECT p.id, p.user_id, p.title, p.cover, p.tags, p.summary, p.category, "
    "p.status, p.visibility, p.review_status, p.edit_count, p.publish_time, "
    "LEFT(p.content, 400) AS content_raw, "
    "p.view_count, p.like_count, p.reply_count, p.create_time, "
    "u.nickname AS author_nickname, u.avatar AS author_avatar "
    "FROM posts p JOIN users u ON u.id = p.user_id"
)
DETAIL_SELECT = (
    "SELECT p.id, p.user_id, p.title, p.content, p.cover, p.tags, p.summary, "
    "p.category, p.status, p.visibility, p.review_status, p.review_note, "
    "p.edit_count, p.publish_time, p.view_count, p.like_count, p.reply_count, p.create_time, "
    "u.nickname AS author_nickname, u.avatar AS author_avatar "
    "FROM posts p JOIN users u ON u.id = p.user_id"
)


def _make_excerpt(html, max_length=EXCERPT_MAX_LENGTH):
    """把正文 HTML 转成卡片用的纯文本摘要。"""
    if not html:
        return ""

    text = re.sub(r"<[^>]*>?", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_length] + "…" if len(text) > max_length else text


def _parse_draft_flag(raw):
    """把 draft 参数归一化为 0/1：1-保存草稿 0-直接发布（默认）。"""
    return 1 if str(raw) in ("1", "true", "True") else 0


def _parse_visibility(raw):
    """解析可见性，非法值返回 None。"""
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value in VISIBILITY_VALUES else None


_CN_DIGITS = "零一二三四五六七八九"


def _cn_number(value):
    """把 1-99 转成中文数字，用于「二编」「三编」这类标签。"""
    if value < 10:
        return _CN_DIGITS[value]
    if value == 10:
        return "十"
    if value < 20:
        return "十" + _CN_DIGITS[value - 10]
    tens, ones = divmod(value, 10)
    return _CN_DIGITS[tens] + "十" + (_CN_DIGITS[ones] if ones else "")


def _edit_label(edit_count):
    """编辑标签：0 次不显示，第 1 次修改显示「二编」，依次递增。"""
    if not edit_count or edit_count <= 0:
        return ""
    return f"{_cn_number(edit_count + 1)}编"


def _validate_post_fields(title, content, cover, tags, summary, category):
    """发帖/更新共用字段长度校验，返回错误响应或 None。"""
    if len(title) > TITLE_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"标题长度不能超过 {TITLE_MAX_LENGTH} 位")
    if len(content) > CONTENT_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"正文长度不能超过 {CONTENT_MAX_LENGTH} 字")
    if len(cover) > COVER_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"封面地址长度不能超过 {COVER_MAX_LENGTH} 位")
    if len(tags) > TAGS_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"标签长度不能超过 {TAGS_MAX_LENGTH} 位")
    if len(summary) > SUMMARY_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"摘要长度不能超过 {SUMMARY_MAX_LENGTH} 位")
    if len(category) > CATEGORY_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"分类长度不能超过 {CATEGORY_MAX_LENGTH} 位")
    return None


def _format_list_item(item):
    """列表项统一格式化：时间字符串 + 正文转摘要 + 编辑标签。"""
    item["create_time"] = format_datetime(item["create_time"])
    item["publish_time"] = format_datetime(item["publish_time"])
    item["edit_label"] = _edit_label(item.get("edit_count", 0))
    item["excerpt"] = _make_excerpt(item.pop("content_raw"))
    return item


def _is_friend(user_id, other_id):
    """判断两人是否为好友（friends 表双向写入，查一行即可）。"""
    if not user_id or not other_id:
        return False
    row = query_one(
        "SELECT id FROM friends WHERE user_id=%s AND friend_id=%s",
        (user_id, other_id),
    )
    return row is not None


def can_view_post(post, user):
    """按可见性与审查状态判断当前用户能否查看帖子。"""
    is_author = bool(user) and user["id"] == post["user_id"]
    if is_author:
        return True
    # 草稿只有作者本人可见
    if post["status"] != 1:
        return False
    # 待审核 / 被打回 / 被封禁的帖子对外不可见
    if post["review_status"] in (REVIEW_PENDING, REVIEW_RETURNED, REVIEW_BANNED):
        return False
    if post["visibility"] == VISIBILITY_PUBLIC:
        return True
    if post["visibility"] == VISIBILITY_PRIVATE:
        return False
    if post["visibility"] == VISIBILITY_FRIENDS:
        return bool(user) and _is_friend(user["id"], post["user_id"])
    return False


@bp.get("/posts")
def list_posts():
    """帖子分页列表：GET /api/posts?page=1&page_size=10&sort=latest&q=关键词&category=分类

    只返回已发布且已通过审核的帖子（正常/推荐）；待审核、打回、封禁的帖子仅作者可见。
    """
    page, page_size = parse_page_args()
    sort = request.args.get("sort", "latest")
    if sort not in SORT_WHITELIST:
        sort = "latest"
    q = clean(request.args.get("q"))
    category = clean(request.args.get("category"))
    user = try_get_current_user()
    viewer_id = user["id"] if user else None

    where = ["p.status=1", "p.review_status NOT IN (2, 3, 4)"]
    args = []
    if viewer_id:
        # 公开帖子 + 自己的「仅好友可见」帖子 + 好友的「仅好友可见」帖子
        where.append(
            "(p.visibility=0 OR (p.visibility=2 AND (p.user_id=%s OR EXISTS ("
            "SELECT 1 FROM friends fr WHERE fr.user_id=%s AND fr.friend_id=p.user_id))))"
        )
        args += [viewer_id, viewer_id]
    else:
        where.append("p.visibility=0")

    if q:
        where.append("(p.title LIKE %s OR p.content LIKE %s)")
        like = f"%{q}%"
        args += [like, like]
    if category:
        where.append("p.category=%s")
        args.append(category)
    where_sql = " WHERE " + " AND ".join(where)

    count_sql = "SELECT COUNT(*) AS total FROM posts p" + where_sql
    list_sql = LIST_SELECT + where_sql + " ORDER BY " + SORT_WHITELIST[sort]
    items, total = paginate(count_sql, list_sql, args, page=page, page_size=page_size)

    items = [_format_list_item(item) for item in items]
    return make_page_response(items, total, page, page_size)


@bp.get("/posts/drafts")
@login_required
def list_my_drafts():
    """我的草稿列表：GET /api/posts/drafts?page=1&page_size=10（仅返回自己的草稿）"""
    user_id = g.current_user["id"]
    page, page_size = parse_page_args()

    count_sql = "SELECT COUNT(*) AS total FROM posts p WHERE p.user_id=%s AND p.status=0"
    list_sql = (
        LIST_SELECT
        + " WHERE p.user_id=%s AND p.status=0 ORDER BY p.update_time DESC, p.id DESC"
    )
    items, total = paginate(count_sql, list_sql, (user_id,), page=page, page_size=page_size)

    items = [_format_list_item(item) for item in items]
    return make_page_response(items, total, page, page_size)


@bp.get("/posts/mine")
@login_required
def list_my_posts():
    """内容管理-帖子列表：GET /api/posts/mine?status=all|published|draft&page=1

    与公开列表不同：这里包含自己的全部帖子（含草稿、被打回、被封禁），
    并用 review_status / review_note 告诉作者当前状态。
    """
    user_id = g.current_user["id"]
    page, page_size = parse_page_args()
    status = request.args.get("status", "all")

    where = ["p.user_id=%s"]
    args = [user_id]
    if status == "published":
        where.append("p.status=1")
    elif status == "draft":
        where.append("p.status=0")
    where_sql = " WHERE " + " AND ".join(where)

    count_sql = "SELECT COUNT(*) AS total FROM posts p" + where_sql
    list_sql = LIST_SELECT + where_sql + " ORDER BY p.update_time DESC, p.id DESC"
    items, total = paginate(count_sql, list_sql, args, page=page, page_size=page_size)
    items = [_format_list_item(item) for item in items]
    return make_page_response(items, total, page, page_size)


@bp.get("/posts/<int:post_id>")
def get_post(post_id):
    """帖子详情：GET /api/posts/1（按可见性鉴权；已发布帖子每次查看浏览数 +1）"""
    item = query_one(DETAIL_SELECT + " WHERE p.id=%s", (post_id,))
    if item is None:
        return make_response(CODE_NOT_FOUND, "帖子不存在")

    user = try_get_current_user()
    if not can_view_post(item, user):
        return make_response(CODE_NOT_FOUND, "帖子不存在")

    # 草稿不计浏览数；已发布帖子计一次浏览
    if item["status"] == 1:
        execute("UPDATE posts SET view_count=view_count+1 WHERE id=%s", (post_id,))
        item["view_count"] += 1

    item["is_favorited"] = False
    item["is_liked"] = False
    item["is_following"] = False
    item["is_self"] = False
    item["is_friend"] = False
    if user is not None:
        item["is_self"] = user["id"] == item["user_id"]
        item["is_friend"] = _is_friend(user["id"], item["user_id"])
        item["is_favorited"] = query_one(
            "SELECT id FROM favorites WHERE user_id=%s AND post_id=%s",
            (user["id"], post_id),
        ) is not None
        item["is_liked"] = query_one(
            "SELECT id FROM post_likes WHERE user_id=%s AND post_id=%s",
            (user["id"], post_id),
        ) is not None
        item["is_following"] = query_one(
            "SELECT id FROM follows WHERE follower_id=%s AND followee_id=%s",
            (user["id"], item["user_id"]),
        ) is not None

    item["create_time"] = format_datetime(item["create_time"])
    item["publish_time"] = format_datetime(item["publish_time"])
    item["review_note"] = item["review_note"] or ""
    item["edit_label"] = _edit_label(item.get("edit_count", 0))
    item["can_edit"] = item["is_self"]
    return make_response(CODE_SUCCESS, "获取成功", item)


@bp.post("/posts/<int:post_id>/like")
@login_required
def toggle_like(post_id):
    """点赞 / 取消点赞切换：POST /api/posts/1/like（需登录）"""
    user_id = g.current_user["id"]
    post = query_one(
        "SELECT id, user_id, status, visibility, review_status, like_count FROM posts WHERE id=%s",
        (post_id,),
    )
    if post is None or post["status"] != 1:
        return make_response(CODE_NOT_FOUND, "帖子不存在或未发布")
    if post["review_status"] in (REVIEW_PENDING, REVIEW_RETURNED, REVIEW_BANNED):
        return make_response(CODE_NOT_FOUND, "帖子不存在或未发布")

    existed = query_one(
        "SELECT id FROM post_likes WHERE user_id=%s AND post_id=%s",
        (user_id, post_id),
    )

    if existed:
        execute(
            "DELETE FROM post_likes WHERE user_id=%s AND post_id=%s",
            (user_id, post_id),
        )
        execute(
            "UPDATE posts SET like_count=GREATEST(like_count-1, 0) WHERE id=%s",
            (post_id,),
        )
        execute(
            "UPDATE users SET likes_count=GREATEST(likes_count-1, 0) WHERE id=%s",
            (post["user_id"],),
        )
        liked = False
        message = "已取消点赞"
    else:
        execute(
            "INSERT INTO post_likes (user_id, post_id) VALUES (%s, %s)",
            (user_id, post_id),
        )
        execute(
            "UPDATE posts SET like_count=like_count+1 WHERE id=%s",
            (post_id,),
        )
        execute(
            "UPDATE users SET likes_count=likes_count+1 WHERE id=%s",
            (post["user_id"],),
        )
        liked = True
        message = "点赞成功"

    row = query_one("SELECT like_count FROM posts WHERE id=%s", (post_id,))
    return make_response(CODE_SUCCESS, message, {
        "post_id": post_id,
        "liked": liked,
        "like_count": row["like_count"],
    })


@bp.post("/posts")
@login_required
def create_post():
    """发布新帖 / 保存草稿：POST /api/posts

    body: {title, content?, cover?, tags?, summary?, category?, visibility?, draft?}
    """
    banned = ensure_not_banned()
    if banned:
        return banned

    user_id = g.current_user["id"]
    body = get_body()
    title = clean(body.get("title"))
    content = clean(body.get("content"))
    cover = clean(body.get("cover"))
    tags = clean(body.get("tags"))
    summary = clean(body.get("summary"))
    category = clean(body.get("category"))
    draft = _parse_draft_flag(body.get("draft"))
    visibility = _parse_visibility(body.get("visibility", VISIBILITY_PUBLIC))

    if visibility is None:
        return make_response(CODE_PARAM_ERROR, "visibility 只能是 0（公开）、1（私密）或 2（仅好友）")

    if not draft and require(body, "title"):
        return make_response(CODE_PARAM_ERROR, "缺少必填参数：title")
    if draft and not (title or content or summary):
        return make_response(CODE_PARAM_ERROR, "草稿至少需要填写标题、摘要或正文之一")

    error = _validate_post_fields(title, content, cover, tags, summary, category)
    if error:
        return error

    status = 0 if draft else 1
    # 新发布的帖子默认进入「待审核」，审核通过后才对公众可见；
    # 作者本人始终能在内容管理中看到自己的内容（can_view_post 已放行作者）
    review_status = REVIEW_PENDING if status == 1 else REVIEW_NORMAL
    post_id = execute(
        "INSERT INTO posts (user_id, title, content, cover, tags, summary, category, "
        "visibility, status, review_status, publish_time) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
        "CASE WHEN %s=1 THEN NOW() ELSE NULL END)",
        (user_id, title, content, cover, tags, summary, category,
         visibility, status, review_status, status),
    )
    message = "已保存到草稿箱" if draft else "发帖成功，审核通过后将公开显示"
    return make_response(CODE_SUCCESS, message, {"id": post_id})


@bp.put("/posts/<int:post_id>")
@login_required
def update_post(post_id):
    """更新自己的帖子/草稿：PUT /api/posts/1（仅作者本人）

    - 已发布帖子再次修改：edit_count +1、publish_time 更新为修改时间
    - 被打回的帖子修改后自动恢复为正常状态
    """
    banned = ensure_not_banned()
    if banned:
        return banned

    user_id = g.current_user["id"]
    item = query_one(
        "SELECT id, user_id, status, visibility, review_status, edit_count FROM posts WHERE id=%s",
        (post_id,),
    )
    if item is None:
        return make_response(CODE_NOT_FOUND, "帖子不存在")
    if item["user_id"] != user_id:
        return make_response(CODE_NO_PERMISSION, "只能操作自己的帖子")

    body = get_body()
    title = clean(body.get("title"))
    content = clean(body.get("content"))
    cover = clean(body.get("cover"))
    tags = clean(body.get("tags"))
    summary = clean(body.get("summary"))
    category = clean(body.get("category"))
    draft = _parse_draft_flag(body.get("draft"))
    raw_visibility = body.get("visibility", item["visibility"])
    visibility = _parse_visibility(raw_visibility)

    if visibility is None:
        return make_response(CODE_PARAM_ERROR, "visibility 只能是 0（公开）、1（私密）或 2（仅好友）")

    if not draft and not title:
        return make_response(CODE_PARAM_ERROR, "缺少必填参数：title")
    if draft and not (title or content or summary):
        return make_response(CODE_PARAM_ERROR, "草稿至少需要填写标题、摘要或正文之一")

    error = _validate_post_fields(title, content, cover, tags, summary, category)
    if error:
        return error

    status = 0 if draft else 1
    # 只有「已发布 -> 再次发布」才算一次修改；草稿首次发布不计入
    edited = item["status"] == 1 and status == 1
    edit_count = item["edit_count"] + 1 if edited else item["edit_count"]

    # 被打回的帖子经作者修改后重新进入「待审核」，等待管理员再次审核通过后才公开
    review_status = item["review_status"]
    if review_status == REVIEW_RETURNED and status == 1:
        review_status = REVIEW_PENDING

    execute(
        "UPDATE posts SET title=%s, content=%s, cover=%s, tags=%s, summary=%s, "
        "category=%s, visibility=%s, status=%s, review_status=%s, edit_count=%s, "
        "publish_time=CASE WHEN %s=1 AND publish_time IS NULL THEN NOW() "
        "WHEN %s=1 THEN NOW() ELSE publish_time END WHERE id=%s",
        (title, content, cover, tags, summary, category, visibility, status,
         review_status, edit_count, status, status, post_id),
    )
    message = "已保存到草稿箱" if draft else "更新成功"
    return make_response(CODE_SUCCESS, message, {
        "id": post_id,
        "edit_count": edit_count,
        "edit_label": _edit_label(edit_count),
    })


@bp.put("/posts/<int:post_id>/visibility")
@login_required
def update_visibility(post_id):
    """快速设置帖子可见性：PUT /api/posts/1/visibility，body {visibility}"""
    user_id = g.current_user["id"]
    item = query_one("SELECT id, user_id FROM posts WHERE id=%s", (post_id,))
    if item is None:
        return make_response(CODE_NOT_FOUND, "帖子不存在")
    if item["user_id"] != user_id:
        return make_response(CODE_NO_PERMISSION, "只能操作自己的帖子")

    body = get_body()
    if "visibility" not in body:
        return make_response(CODE_PARAM_ERROR, "缺少必填参数：visibility")
    visibility = _parse_visibility(body.get("visibility"))
    if visibility is None:
        return make_response(CODE_PARAM_ERROR, "visibility 只能是 0（公开）、1（私密）或 2（仅好友）")

    execute("UPDATE posts SET visibility=%s WHERE id=%s", (visibility, post_id))
    labels = {VISIBILITY_PUBLIC: "公开", VISIBILITY_PRIVATE: "私密", VISIBILITY_FRIENDS: "仅好友可见"}
    return make_response(CODE_SUCCESS, f"已设为{labels[visibility]}", {
        "id": post_id,
        "visibility": visibility,
    })


@bp.delete("/posts/<int:post_id>")
@login_required
def delete_post(post_id):
    """删除自己的帖子/草稿：DELETE /api/posts/1（仅作者本人）"""
    user_id = g.current_user["id"]
    item = query_one("SELECT id, user_id FROM posts WHERE id=%s", (post_id,))
    if item is None:
        return make_response(CODE_NOT_FOUND, "帖子不存在")
    if item["user_id"] != user_id:
        return make_response(CODE_NO_PERMISSION, "只能操作自己的帖子")

    execute("DELETE FROM posts WHERE id=%s", (post_id,))
    return make_response(CODE_SUCCESS, "删除成功", {"id": post_id})
