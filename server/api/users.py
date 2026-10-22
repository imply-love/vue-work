"""用户接口（需登录接口范例）。

本文件演示「需要携带 token 的接口」写法：只要加上 @login_required，
就能在函数里通过 g.current_user["id"] 拿到当前登录用户。
"""
from flask import Blueprint, g
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute, paginate, query_one
from utils.auth import login_required
from utils.params import clean, get_body, is_valid_email, is_valid_phone, parse_page_args, require
from utils.response import (
    CODE_CODE_INVALID,
    CODE_EMAIL_EXISTS,
    CODE_PARAM_ERROR,
    CODE_PASSWORD_ERROR,
    CODE_PHONE_EXISTS,
    CODE_SUCCESS,
    CODE_USER_NOT_FOUND,
    format_datetime,
    make_page_response,
    make_response,
)
from utils.verify_code import SCENE_BIND_EMAIL, check_code

bp = Blueprint("users", __name__, url_prefix="/api")

PROFILE_SQL = (
    "SELECT id, username, email, nickname, avatar, phone, followers_count, "
    "likes_count, following_count, role, status, create_time "
    "FROM users WHERE id=%s"
)

# 与 users 表字段长度保持一致，超长直接返回 1001，避免落库时报数据库错误
NICKNAME_MAX_LENGTH = 50
EMAIL_MAX_LENGTH = 100
PHONE_MAX_LENGTH = 20

# 密码长度限制，与注册接口保持一致
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 20


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
    """更新当前登录用户资料：PUT /api/user/profile，body {nickname, email, code}

    邮箱变更是强制验证的：只要 email 与当前值不同，就必须带上发到新邮箱的验证码。
    """
    user_id = g.current_user["id"]
    body = get_body()
    nickname = clean(body.get("nickname"))
    email = clean(body.get("email"))
    code = clean(body.get("code"))

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

    current = query_one("SELECT email FROM users WHERE id=%s", (user_id,))
    if current is None:
        return make_response(CODE_USER_NOT_FOUND, "用户不存在")

    # 换绑邮箱必须验码，否则「邮箱已验证」这个状态可以被随意绕过
    if email != current["email"] and not check_code(email, SCENE_BIND_EMAIL, code):
        return make_response(CODE_CODE_INVALID, "邮箱验证码错误或已过期，请重新获取")

    execute(
        "UPDATE users SET nickname=%s, email=%s WHERE id=%s",
        (nickname, email, user_id),
    )

    # 返回更新后的完整资料，前端可直接覆盖本地缓存
    return make_response(CODE_SUCCESS, "保存成功", _load_profile(user_id))


@bp.put("/user/phone")
@login_required
def update_phone():
    """绑定 / 换绑 / 解绑手机号：PUT /api/user/phone，body {phone}

    手机号是非强制绑定项，不需要验证码；phone 传空串表示解绑。
    """
    user_id = g.current_user["id"]
    body = get_body()

    # 不能用 require：解绑时 phone 就是空串，只能判断字段是否存在
    if "phone" not in body:
        return make_response(CODE_PARAM_ERROR, "缺少必填参数：phone")

    phone = clean(body.get("phone"))

    if phone:
        if len(phone) > PHONE_MAX_LENGTH:
            return make_response(CODE_PARAM_ERROR, f"手机号长度不能超过 {PHONE_MAX_LENGTH} 位")
        if not is_valid_phone(phone):
            return make_response(CODE_PARAM_ERROR, "手机号格式不正确（需为 11 位中国大陆手机号）")
        if query_one("SELECT id FROM users WHERE phone=%s AND id<>%s", (phone, user_id)):
            return make_response(CODE_PHONE_EXISTS, "该手机号已被其他账号绑定")
        # 未绑定在库里存 NULL，这样唯一索引才允许多个「未绑定」共存
        phone_value = phone
        message = "手机号绑定成功"
    else:
        phone_value = None
        message = "已解绑手机号"

    execute("UPDATE users SET phone=%s WHERE id=%s", (phone_value, user_id))

    return make_response(CODE_SUCCESS, message, _load_profile(user_id))


def _load_profile(user_id):
    """按 id 查用户资料（不含密码），无此用户返回 None。"""
    user = query_one(PROFILE_SQL, (user_id,))
    if user is not None:
        user["create_time"] = format_datetime(user["create_time"])
        # 未绑定手机号在库里是 NULL，统一转成空串，前端只需判断真假
        user["phone"] = user["phone"] or ""
    return user


@bp.put("/user/password")
@login_required
def change_password():
    """修改密码：PUT /api/user/password，body {old_password, new_password}

    需要校验原密码，新密码长度 6-20 位；成功后旧 token 仍有效，
    由前端提示重新登录（安全起见建议修改后重新登录）。
    """
    user_id = g.current_user["id"]
    body = get_body()
    old_password = clean(body.get("old_password"))
    new_password = clean(body.get("new_password"))

    missing = require(body, "old_password", "new_password")
    if missing:
        return make_response(CODE_PARAM_ERROR, f"缺少必填参数：{'、'.join(missing)}")

    if not PASSWORD_MIN_LENGTH <= len(new_password) <= PASSWORD_MAX_LENGTH:
        return make_response(
            CODE_PARAM_ERROR,
            f"新密码长度需为 {PASSWORD_MIN_LENGTH}-{PASSWORD_MAX_LENGTH} 位",
        )

    user = query_one("SELECT password FROM users WHERE id=%s", (user_id,))
    if user is None:
        return make_response(CODE_USER_NOT_FOUND, "用户不存在")
    if not check_password_hash(user["password"], old_password):
        return make_response(CODE_PASSWORD_ERROR, "原密码错误")

    execute(
        "UPDATE users SET password=%s WHERE id=%s",
        (generate_password_hash(new_password), user_id),
    )
    return make_response(CODE_SUCCESS, "密码修改成功，请重新登录")


@bp.get("/user/login-logs")
@login_required
def list_login_logs():
    """登录记录：GET /api/user/login-logs?page=1&page_size=10（最近登录在前）"""
    user_id = g.current_user["id"]
    page, page_size = parse_page_args()

    count_sql = "SELECT COUNT(*) AS total FROM login_logs WHERE user_id=%s"
    list_sql = (
        "SELECT id, ip, device, user_agent, create_time "
        "FROM login_logs WHERE user_id=%s "
        "ORDER BY create_time DESC, id DESC"
    )
    items, total = paginate(count_sql, list_sql, (user_id,), page=page, page_size=page_size)
    for item in items:
        item["create_time"] = format_datetime(item["create_time"])
    return make_page_response(items, total, page, page_size)


@bp.delete("/user/account")
@login_required
def delete_account():
    """注销账号：DELETE /api/user/account，body {password}

    必须输入当前密码确认；成功后删除账号（关联的帖子、收藏等按外键级联删除），
    前端应立即清除本地登录态并返回首页。
    """
    user_id = g.current_user["id"]
    body = get_body()
    password = clean(body.get("password"))

    missing = require(body, "password")
    if missing:
        return make_response(CODE_PARAM_ERROR, f"缺少必填参数：{'、'.join(missing)}")

    user = query_one("SELECT password FROM users WHERE id=%s", (user_id,))
    if user is None:
        return make_response(CODE_USER_NOT_FOUND, "用户不存在")
    if not check_password_hash(user["password"], password):
        return make_response(CODE_PASSWORD_ERROR, "密码错误，无法注销账号")

    execute("DELETE FROM users WHERE id=%s", (user_id,))
    return make_response(CODE_SUCCESS, "账号已注销")


@bp.post("/users/<int:target_id>/follow")
@login_required
def toggle_follow(target_id):
    """关注 / 取消关注切换：POST /api/users/<id>/follow（需登录）

    幂等切换：未关注则关注（对方 followers_count +1、自己 following_count +1），
    已关注则取消（同步 -1）。不能关注自己，目标用户必须存在。
    """
    follower_id = g.current_user["id"]

    if follower_id == target_id:
        return make_response(CODE_PARAM_ERROR, "不能关注自己")

    target = query_one("SELECT id, nickname FROM users WHERE id=%s", (target_id,))
    if target is None:
        return make_response(CODE_USER_NOT_FOUND, "用户不存在")

    existed = query_one(
        "SELECT id FROM follows WHERE follower_id=%s AND followee_id=%s",
        (follower_id, target_id),
    )

    if existed:
        execute(
            "DELETE FROM follows WHERE follower_id=%s AND followee_id=%s",
            (follower_id, target_id),
        )
        execute(
            "UPDATE users SET following_count=GREATEST(following_count-1, 0) WHERE id=%s",
            (follower_id,),
        )
        execute(
            "UPDATE users SET followers_count=GREATEST(followers_count-1, 0) WHERE id=%s",
            (target_id,),
        )
        following = False
        message = "已取消关注"
    else:
        execute(
            "INSERT INTO follows (follower_id, followee_id) VALUES (%s, %s)",
            (follower_id, target_id),
        )
        execute(
            "UPDATE users SET following_count=following_count+1 WHERE id=%s",
            (follower_id,),
        )
        execute(
            "UPDATE users SET followers_count=followers_count+1 WHERE id=%s",
            (target_id,),
        )
        following = True
        message = f"已关注 {target['nickname']}"

    row = query_one(
        "SELECT followers_count FROM users WHERE id=%s",
        (target_id,),
    )
    return make_response(CODE_SUCCESS, message, {
        "target_id": target_id,
        "following": following,
        "followers_count": row["followers_count"],
    })