"""帖子接口：公开分页只读 + 登录发帖/草稿/管理。

- GET    /api/posts           公开列表：支持排序 sort（latest/hot/replies）、
                              搜索 q、分类 category 筛选
- GET    /api/posts/drafts    我的草稿列表（需登录）
- POST   /api/posts           发布新帖 / 保存草稿（需登录）
- GET    /api/posts/<id>      帖子详情（草稿仅作者可见）
- POST   /api/posts/<id>/like 点赞 / 取消点赞切换（需登录）
- PUT    /api/posts/<id>      更新自己的帖子/草稿（需登录，仅作者）
- DELETE /api/posts/<id>      删除自己的帖子/草稿（需登录，仅作者）
"""
import re

from flask import Blueprint, g, request

from db import execute, paginate, query_one
from utils.auth import login_required, try_get_current_user
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

# 与 posts 表字段长度保持一致，超长直接返回 1001，避免落库时报数据库错误
TITLE_MAX_LENGTH = 200
CONTENT_MAX_LENGTH = 20000
COVER_MAX_LENGTH = 255
TAGS_MAX_LENGTH = 255
SUMMARY_MAX_LENGTH = 255
CATEGORY_MAX_LENGTH = 30

# 卡片摘要最大长度（前端卡片最多显示两行）
EXCERPT_MAX_LENGTH = 120

# 列表排序白名单：sort 参数只接受这三个值，非法值回退 latest
SORT_WHITELIST = {
    "latest": "p.create_time DESC, p.id DESC",
    "hot": "(p.like_count + p.view_count) DESC, p.create_time DESC, p.id DESC",
    "replies": "p.reply_count DESC, p.create_time DESC, p.id DESC",
}

# 列表与详情共用的字段：列表只取正文前 400 字符作摘要，详情取全文
LIST_SELECT = (
    "SELECT p.id, p.user_id, p.title, p.cover, p.tags, p.summary, p.category, "
    "p.status, LEFT(p.content, 400) AS content_raw, "
    "p.view_count, p.like_count, p.reply_count, p.create_time, "
    "u.nickname AS author_nickname, u.avatar AS author_avatar "
    "FROM posts p JOIN users u ON u.id = p.user_id"
)
DETAIL_SELECT = (
    "SELECT p.id, p.user_id, p.title, p.content, p.cover, p.tags, p.summary, "
    "p.category, p.status, p.view_count, p.like_count, p.reply_count, p.create_time, "
    "u.nickname AS author_nickname, u.avatar AS author_avatar "
    "FROM posts p JOIN users u ON u.id = p.user_id"
)


def _make_excerpt(html, max_length=EXCERPT_MAX_LENGTH):
    """把正文 HTML 转成卡片用的纯文本摘要。

    因为正文是按字符截取后再处理的，末尾可能残留半截标签，
    所以标签正则里的 ">" 是可选的，连同不完整标签一起清掉。
    """
    if not html:
        return ""

    text = re.sub(r"<[^>]*>?", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_length] + "…" if len(text) > max_length else text


def _parse_draft_flag(raw):
    """把 draft 参数归一化为 0/1：1-保存草稿 0-直接发布（默认）。"""
    return 1 if str(raw) in ("1", "true", "True") else 0


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
    """列表项统一格式化：时间字符串 + 正文转摘要。"""
    item["create_time"] = format_datetime(item["create_time"])
    item["excerpt"] = _make_excerpt(item.pop("content_raw"))
    return item


@bp.get("/posts")
def list_posts():
    """帖子分页列表：GET /api/posts?page=1&page_size=10&sort=latest&q=关键词&category=分类"""
    page, page_size = parse_page_args()
    sort = request.args.get("sort", "latest")
    if sort not in SORT_WHITELIST:
        sort = "latest"
    q = clean(request.args.get("q"))
    category = clean(request.args.get("category"))

    # 动态拼接查询条件：只展示已发布（status=1）的帖子
    where = ["p.status=1"]
    args = []
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


@bp.get("/posts/<int:post_id>")
def get_post(post_id):
    """帖子详情：GET /api/posts/1（不存在返回 1009；草稿仅作者可见）

    已发布帖子每次查看浏览数 +1；登录用户同时返回收藏 / 点赞 / 关注作者状态。
    """
    item = query_one(DETAIL_SELECT + " WHERE p.id=%s", (post_id,))
    if item is None:
        return make_response(CODE_NOT_FOUND, "帖子不存在")

    # 草稿属于未发布内容，仅作者本人可查看，也不计浏览数
    if item["status"] == 0:
        user = try_get_current_user()
        if user is None or user["id"] != item["user_id"]:
            return make_response(CODE_NOT_FOUND, "帖子不存在")
    else:
        execute("UPDATE posts SET view_count=view_count+1 WHERE id=%s", (post_id,))
        item["view_count"] += 1

    # 登录用户返回收藏 / 点赞 / 关注作者状态，供详情页展示对应按钮
    user = try_get_current_user()
    item["is_favorited"] = False
    item["is_liked"] = False
    item["is_following"] = False
    item["is_self"] = False
    if user is not None:
        item["is_self"] = user["id"] == item["user_id"]
        fav = query_one(
            "SELECT id FROM favorites WHERE user_id=%s AND post_id=%s",
            (user["id"], post_id),
        )
        item["is_favorited"] = fav is not None
        like = query_one(
            "SELECT id FROM post_likes WHERE user_id=%s AND post_id=%s",
            (user["id"], post_id),
        )
        item["is_liked"] = like is not None
        follow = query_one(
            "SELECT id FROM follows WHERE follower_id=%s AND followee_id=%s",
            (user["id"], item["user_id"]),
        )
        item["is_following"] = follow is not None

    item["create_time"] = format_datetime(item["create_time"])
    return make_response(CODE_SUCCESS, "获取成功", item)


@bp.post("/posts/<int:post_id>/like")
@login_required
def toggle_like(post_id):
    """点赞 / 取消点赞切换：POST /api/posts/1/like（需登录，管理员与普通用户均可）

    幂等切换：已点赞则取消，未点赞则点赞；同步维护 posts.like_count 与
    帖子作者的 users.likes_count（作者获赞数）。草稿不可点赞。
    """
    user_id = g.current_user["id"]
    post = query_one(
        "SELECT id, user_id, status, like_count FROM posts WHERE id=%s",
        (post_id,),
    )
    if post is None:
        return make_response(CODE_NOT_FOUND, "帖子不存在")
    if post["status"] != 1:
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

    body: {title, content?, cover?, tags?, summary?, category?, draft?}
    - draft 缺省为 0（直接发布）；draft=1 保存到草稿箱
    - 直接发布时 title 必填；草稿至少需要标题、摘要或正文之一
    """
    user_id = g.current_user["id"]
    body = get_body()
    title = clean(body.get("title"))
    content = clean(body.get("content"))
    cover = clean(body.get("cover"))
    tags = clean(body.get("tags"))
    summary = clean(body.get("summary"))
    category = clean(body.get("category"))
    draft = _parse_draft_flag(body.get("draft"))

    if not draft and require(body, "title"):
        return make_response(CODE_PARAM_ERROR, "缺少必填参数：title")
    if draft and not (title or content or summary):
        return make_response(CODE_PARAM_ERROR, "草稿至少需要填写标题、摘要或正文之一")

    error = _validate_post_fields(title, content, cover, tags, summary, category)
    if error:
        return error

    status = 0 if draft else 1
    post_id = execute(
        "INSERT INTO posts (user_id, title, content, cover, tags, summary, category, status) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (user_id, title, content, cover, tags, summary, category, status),
    )
    message = "已保存到草稿箱" if draft else "发帖成功"
    return make_response(CODE_SUCCESS, message, {"id": post_id})


@bp.put("/posts/<int:post_id>")
@login_required
def update_post(post_id):
    """更新自己的帖子/草稿：PUT /api/posts/1（仅作者本人，草稿续写或直接发布）"""
    user_id = g.current_user["id"]
    item = query_one("SELECT id, user_id FROM posts WHERE id=%s", (post_id,))
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

    if not draft and not title:
        return make_response(CODE_PARAM_ERROR, "缺少必填参数：title")
    if draft and not (title or content or summary):
        return make_response(CODE_PARAM_ERROR, "草稿至少需要填写标题、摘要或正文之一")

    error = _validate_post_fields(title, content, cover, tags, summary, category)
    if error:
        return error

    status = 0 if draft else 1
    execute(
        "UPDATE posts SET title=%s, content=%s, cover=%s, tags=%s, summary=%s, "
        "category=%s, status=%s WHERE id=%s",
        (title, content, cover, tags, summary, category, status, post_id),
    )
    message = "已保存到草稿箱" if draft else "更新成功"
    return make_response(CODE_SUCCESS, message, {"id": post_id})


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
