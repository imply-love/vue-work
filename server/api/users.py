"""用户接口（预留范例：需登录接口）。

本文件演示「需要携带 token 的接口」写法：只要加上 @login_required，
就能在函数里通过 g.current_user["id"] 拿到当前登录用户。
"""
from flask import Blueprint, g

from db import query_one
from utils.auth import login_required
from utils.response import (
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


@bp.get("/user/profile")
@login_required
def profile():
    """当前登录用户信息：GET /api/user/profile（需 header Authorization: Bearer <token>）"""
    user = query_one(PROFILE_SQL, (g.current_user["id"],))
    if user is None:
        return make_response(CODE_USER_NOT_FOUND, "用户不存在")

    user["create_time"] = format_datetime(user["create_time"])
    return make_response(CODE_SUCCESS, "获取成功", user)