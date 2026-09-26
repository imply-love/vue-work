"""登录态校验：@login_required 装饰器与 g.current_user。

后续需要「当前登录用户」的接口，直接加装饰器即可：
    @bp.get("/xxx")
    @login_required
    def xxx():
        user_id = g.current_user["id"]
"""
from functools import wraps

from flask import g, request

from db import query_one
from utils.response import (
    CODE_TOKEN_INVALID,
    CODE_USER_DISABLED,
    make_response,
)
from utils.token import parse_token

_CURRENT_USER_KEY = "current_user"
_BEARER_PREFIX = "bearer "


def get_current_user():
    """读取当前登录用户信息，未登录返回 None。"""
    return g.get(_CURRENT_USER_KEY)


def login_required(view):
    """校验请求头中的 token，通过后把当前用户写入 g.current_user。"""
    @wraps(view)
    def wrapper(*args, **kwargs):
        user_id = parse_token(_extract_token())
        if user_id is None:
            return make_response(CODE_TOKEN_INVALID, "登录状态无效或已过期")

        user = query_one(
            "SELECT id, username, role, status FROM users WHERE id=%s",
            (user_id,),
        )
        if user is None:
            return make_response(CODE_TOKEN_INVALID, "登录状态无效或已过期")
        if user["status"] == 0:
            return make_response(CODE_USER_DISABLED, "账号已被禁用")

        g.current_user = {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
        }
        return view(*args, **kwargs)

    return wrapper


def _extract_token():
    """从 Authorization 请求头取出 token。"""
    header = request.headers.get("Authorization", "")
    if header.lower().startswith(_BEARER_PREFIX):
        return header[len(_BEARER_PREFIX):].strip()
    return header.strip()