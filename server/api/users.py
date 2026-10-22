"""用户接口（需登录接口范例）。

本文件演示「需要携带 token 的接口」写法：只要加上 @login_required，
就能在函数里通过 g.current_user["id"] 拿到当前登录用户。
"""
from flask import Blueprint, g

from db import execute, query_one
from utils.auth import login_required
from utils.params import clean, get_body, is_valid_email, require
from utils.response import (
    CODE_EMAIL_EXISTS,
    CODE_PARAM_ERROR,
    CODE_SUCCESS,
    CODE_USER_NOT_FOUND,
    format_datetime,
    make_response,
)

bp = Blueprint("users", __name__, url_prefix="/api")

PROFILE_SQL = (
    "SELECT id, username, email, nickname, avatar, followers_count, "
    "likes_count, following_count, role, status, create_time "
    "FROM users WHERE id=%s"
)

# 与 users 表字段长度保持一致，超长直接返回 1001，避免落库时报数据库错误
NICKNAME_MAX_LENGTH = 50
EMAIL_MAX_LENGTH = 100


@bp.get("/user/profile")
@login_required
def profile():
    """当前登录用户信息：GET /api/user/profile（需 header Authorization: Bearer <token>）"""
    user = _load_profile(g.current_user["id"])
    if user is None:
        return make_response(CODE_USER_NOT_FOUND, "用户不存在")

    return make_response(CODE_SUCCESS, "获取成功", user)


@bp.put("/user/profile")
@login_required
def update_profile():
    """更新当前登录用户资料：PUT /api/user/profile，body {nickname, email}"""
    user_id = g.current_user["id"]
    body = get_body()
    nickname = clean(body.get("nickname"))
    email = clean(body.get("email"))

    missing = require(body, "nickname", "email")
    if missing:
        return make_response(CODE_PARAM_ERROR, f"缺少必填参数：{'、'.join(missing)}")

    if len(nickname) > NICKNAME_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"昵称长度不能超过 {NICKNAME_MAX_LENGTH} 位")

    if len(email) > EMAIL_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"邮箱长度不能超过 {EMAIL_MAX_LENGTH} 位")

    if not is_valid_email(email):
        return make_response(CODE_PARAM_ERROR, "邮箱格式不正确")

    # 邮箱要保持唯一，但要排除自己
    if query_one("SELECT id FROM users WHERE email=%s AND id<>%s", (email, user_id)):
        return make_response(CODE_EMAIL_EXISTS, "该邮箱已被注册")

    execute(
        "UPDATE users SET nickname=%s, email=%s WHERE id=%s",
        (nickname, email, user_id),
    )

    # 返回更新后的完整资料，前端可直接覆盖本地缓存
    return make_response(CODE_SUCCESS, "保存成功", _load_profile(user_id))


def _load_profile(user_id):
    """按 id 查用户资料（不含密码），无此用户返回 None。"""
    user = query_one(PROFILE_SQL, (user_id,))
    if user is not None:
        user["create_time"] = format_datetime(user["create_time"])
    return user