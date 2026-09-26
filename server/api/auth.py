"""认证接口：注册与登录。"""
import random
import string

import pymysql
from flask import Blueprint
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute, query_one
from utils.params import clean, get_body, is_valid_email, require
from utils.response import (
    CODE_DB_ERROR,
    CODE_EMAIL_EXISTS,
    CODE_PARAM_ERROR,
    CODE_PASSWORD_ERROR,
    CODE_SUCCESS,
    CODE_USER_DISABLED,
    CODE_USER_NOT_FOUND,
    CODE_USERNAME_EXISTS,
    make_response,
)
from utils.token import generate_token

bp = Blueprint("auth", __name__, url_prefix="/api")

# 未指定用户名时的随机账号规则
RANDOM_USERNAME_PREFIX = "yunmo_"
RANDOM_USERNAME_SUFFIX_LENGTH = 6
RANDOM_USERNAME_MAX_RETRY = 10

# 密码长度限制
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 20


@bp.post("/register")
def register():
    """用户注册接口。"""
    body = get_body()
    username = clean(body.get("username"))
    password = clean(body.get("password"))
    email = clean(body.get("email"))
    nickname = clean(body.get("nickname"))

    missing = require(body, "password", "email")
    if missing:
        return make_response(CODE_PARAM_ERROR, f"缺少必填参数：{'、'.join(missing)}")

    if not PASSWORD_MIN_LENGTH <= len(password) <= PASSWORD_MAX_LENGTH:
        return make_response(
            CODE_PARAM_ERROR,
            f"密码长度需为 {PASSWORD_MIN_LENGTH}-{PASSWORD_MAX_LENGTH} 位",
        )

    if not is_valid_email(email):
        return make_response(CODE_PARAM_ERROR, "邮箱格式不正确")

    # 传了用户名就校验唯一性，没传才随机生成
    if username:
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
        "SELECT id, username, password, email, nickname, avatar, followers_count, "
        "likes_count, following_count, role, status "
        "FROM users WHERE username=%s",
        (username,),
    )
    if user is None:
        return make_response(CODE_USER_NOT_FOUND, "用户不存在")

    if not check_password_hash(user["password"], password):
        return make_response(CODE_PASSWORD_ERROR, "密码错误")

    if user["status"] == 0:
        return make_response(CODE_USER_DISABLED, "账号已被禁用")

    # 登录成功，签发 token 供后续接口携带
    return make_response(CODE_SUCCESS, "登录成功", {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "nickname": user["nickname"],
        "avatar": user["avatar"],
        "followers_count": user["followers_count"],
        "likes_count": user["likes_count"],
        "following_count": user["following_count"],
        "role": user["role"],
        "token": generate_token(user["id"]),
    })


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