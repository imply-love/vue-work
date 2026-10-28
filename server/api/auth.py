"""认证接口：注册与登录。"""
import random
import string

import pymysql
from flask import Blueprint, request
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute, query_one
from utils.device import extract_client_ip, parse_user_agent
from utils.params import clean, get_body, is_valid_email, require
from utils.response import (
    CODE_CODE_INVALID,
    CODE_DB_ERROR,
    CODE_EMAIL_EXISTS,
    CODE_PARAM_ERROR,
    CODE_PASSWORD_ERROR,
    CODE_SUCCESS,
    CODE_USER_DISABLED,
    CODE_USER_NOT_FOUND,
    CODE_USERNAME_EXISTS,
    format_datetime,
    make_response,
)
from utils.token import generate_token
from utils.verify_code import SCENE_REGISTER, check_code

bp = Blueprint("auth", __name__, url_prefix="/api")

# 未指定用户名时的随机账号规则
RANDOM_USERNAME_PREFIX = "yunmo_"
RANDOM_USERNAME_SUFFIX_LENGTH = 6
RANDOM_USERNAME_MAX_RETRY = 10

# 密码长度限制
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 20

# 与 users 表字段长度保持一致，超长直接返回 1001，避免落库时报数据库错误
USERNAME_MAX_LENGTH = 50
EMAIL_MAX_LENGTH = 100
NICKNAME_MAX_LENGTH = 50


@bp.post("/register")
def register():
    """用户注册接口。

    邮箱是强制绑定项：必须先通过 /api/email/code 拿到验证码，注册时才允许创建账号。
    """
    body = get_body()
    username = clean(body.get("username"))
    password = clean(body.get("password"))
    email = clean(body.get("email"))
    nickname = clean(body.get("nickname"))
    code = clean(body.get("code"))

    missing = require(body, "password", "email", "code")
    if missing:
        return make_response(CODE_PARAM_ERROR, f"缺少必填参数：{'、'.join(missing)}")

    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        return make_response(
            CODE_PARAM_ERROR,
            f"密码长度需为 {PASSWORD_MIN_LENGTH}-{PASSWORD_MAX_LENGTH} 位",
        )

    if not is_valid_email(email):
        return make_response(CODE_PARAM_ERROR, "邮箱格式不正确")

    if len(email) > EMAIL_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"邮箱长度不能超过 {EMAIL_MAX_LENGTH} 位")

    # 传了用户名就校验唯一性，没传才随机生成
    if username:
        if len(username) > USERNAME_MAX_LENGTH:
            return make_response(
                CODE_PARAM_ERROR, f"用户名长度不能超过 {USERNAME_MAX_LENGTH} 位"
            )
        if query_one("SELECT id FROM users WHERE username=%s", (username,)):
            return make_response(CODE_USERNAME_EXISTS, "该用户名已被注册")
    else:
        username = _generate_username()
        if username is None:
            return make_response(CODE_DB_ERROR, "用户名生成失败，请重试")

    if query_one("SELECT id FROM users WHERE email=%s", (email,)):
        return make_response(CODE_EMAIL_EXISTS, "该邮箱已被注册")

    if not nickname:
        nickname = username

    if len(nickname) > NICKNAME_MAX_LENGTH:
        return make_response(CODE_PARAM_ERROR, f"昵称长度不能超过 {NICKNAME_MAX_LENGTH} 位")

    # 放在所有字段校验之后：验证码是一次性的，前面任何一步失败都不该消耗它
    if not check_code(email, SCENE_REGISTER, code):
        return make_response(CODE_CODE_INVALID, "邮箱验证码错误或已过期，请重新获取")

    try:
        user_id = execute(
            "INSERT INTO users (username, password, email, nickname) VALUES (%s, %s, %s, %s)",
            (username, generate_password_hash(password), email, nickname),
        )
    except pymysql.MySQLError:
        return make_response(CODE_DB_ERROR, "数据库操作失败")

    # 返回用户信息，不返回密码
    return make_response(CODE_SUCCESS, "注册成功", {
        "id": user_id,
        "username": username,
        "nickname": nickname,
        "email": email,
    })


@bp.post("/login")
def login():
    """用户登录接口。"""
    body = get_body()
    username = clean(body.get("username"))
    password = clean(body.get("password"))

    missing = require(body, "username", "password")
    if missing:
        return make_response(CODE_PARAM_ERROR, f"缺少必填参数：{'、'.join(missing)}")

    user = query_one(
        "SELECT id, username, password, email, nickname, avatar, phone, followers_count, "
        "likes_count, following_count, role, status, ban_reason, ban_time "
        "FROM users WHERE username=%s",
        (username,),
    )
    if user is None:
        return make_response(CODE_USER_NOT_FOUND, "用户不存在")

    if not check_password_hash(user["password"], password):
        return make_response(CODE_PASSWORD_ERROR, "密码错误")

    # status=0 为禁用（不可登录）；status=2 为封禁，允许登录但限制发言并引导申诉
    if user["status"] == 0:
        return make_response(CODE_USER_DISABLED, "账号已被禁用")

    # 登录成功，写入登录记录（IP、设备摘要、UA），供个人中心「登录记录」展示
    _record_login(user["id"])

    # 登录成功，签发 token 供后续接口携带
    return make_response(CODE_SUCCESS, "登录成功", {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "nickname": user["nickname"],
        "avatar": user["avatar"],
        "phone": user["phone"] or "",
        "followers_count": user["followers_count"],
        "likes_count": user["likes_count"],
        "following_count": user["following_count"],
        "role": user["role"],
        "status": user["status"],
        "is_banned": user["status"] == 2,
        "ban_reason": user["ban_reason"] or "",
        "ban_time": format_datetime(user["ban_time"]),
        "token": generate_token(user["id"]),
    })


def _record_login(user_id):
    """写入一条登录记录（login_logs），失败不影响登录主流程。"""
    try:
        execute(
            "INSERT INTO login_logs (user_id, ip, device, user_agent) VALUES (%s, %s, %s, %s)",
            (
                user_id,
                extract_client_ip(request),
                parse_user_agent(request.headers.get("User-Agent", ""))[:100],
                (request.headers.get("User-Agent", "") or "")[:255],
            ),
        )
    except Exception:
        # 登录记录失败不应阻断登录本身，仅记录日志
        from flask import current_app

        current_app.logger.warning("写入登录记录失败", exc_info=True)


def _generate_username():
    """随机生成一个未被占用的用户名，失败返回 None。"""
    alphabet = string.ascii_lowercase + string.digits
    for _ in range(RANDOM_USERNAME_MAX_RETRY):
        candidate = RANDOM_USERNAME_PREFIX + "".join(
            random.choices(alphabet, k=RANDOM_USERNAME_SUFFIX_LENGTH)
        )
        if query_one("SELECT id FROM users WHERE username=%s", (candidate,)) is None:
            return candidate
    return None