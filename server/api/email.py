"""邮箱验证码接口。

注册前发送：POST /api/email/code        body {"email": "..."}（无需登录）
换绑邮箱发送：POST /api/user/email/code  body {"email": "..."}（需登录）

两个场景分开成两个接口，是为了让「注册前」这个公开入口不需要登录态；
生成与校验逻辑都复用 utils/verify_code.py，用 scene 隔离。
"""
from flask import Blueprint, g

from db import query_one
from utils.auth import login_required
from utils.mailer import send_verify_code
from utils.params import clean, get_body, is_valid_email
from utils.response import (
    CODE_CODE_TOO_FREQUENT,
    CODE_EMAIL_EXISTS,
    CODE_MAIL_SEND_FAILED,
    CODE_PARAM_ERROR,
    CODE_SUCCESS,
    make_response,
)
from utils.verify_code import (
    SCENE_BIND_EMAIL,
    SCENE_REGISTER,
    create_code,
    discard_code,
    send_interval_left,
)

bp = Blueprint("email", __name__, url_prefix="/api")

# 与 users 表字段长度保持一致
EMAIL_MAX_LENGTH = 100


@bp.post("/email/code")
def send_register_code():
    """注册前发送邮箱验证码：该邮箱必须尚未注册。"""
    email, error = _read_email()
    if error:
        return error

    if query_one("SELECT id FROM users WHERE email=%s", (email,)):
        return make_response(CODE_EMAIL_EXISTS, "该邮箱已被注册")

    return _send(email, SCENE_REGISTER)


@bp.post("/user/email/code")
@login_required
def send_bind_email_code():
    """换绑邮箱时发送验证码：新邮箱不能被其他账号占用。"""
    email, error = _read_email()
    if error:
        return error

    user_id = g.current_user["id"]
    if query_one("SELECT id FROM users WHERE email=%s AND id<>%s", (email, user_id)):
        return make_response(CODE_EMAIL_EXISTS, "该邮箱已被其他账号绑定")

    return _send(email, SCENE_BIND_EMAIL)


def _read_email():
    """读取并校验请求体里的邮箱，返回 (邮箱, 错误响应)。"""
    body = get_body()
    email = clean(body.get("email"))
    if not email:
        return None, make_response(CODE_PARAM_ERROR, "缺少必填参数：email")
    if len(email) > EMAIL_MAX_LENGTH:
        return None, make_response(CODE_PARAM_ERROR, f"邮箱长度不能超过 {EMAIL_MAX_LENGTH} 位")
    if not is_valid_email(email):
        return None, make_response(CODE_PARAM_ERROR, "邮箱格式不正确")
    return email, None


def _send(email, scene):
    """生成验证码并发送。未配置邮件服务时提示去后端控制台查看。"""
    remain = send_interval_left(email, scene)
    if remain:
        return make_response(CODE_CODE_TOO_FREQUENT, f"验证码已发送，请 {remain} 秒后再试")

    code_id, code = create_code(email, scene)
    sent, error = send_verify_code(email, code)
    if error:
        # 发信失败就作废这条验证码，否则重发间隔会把用户卡住
        discard_code(code_id)
        return make_response(CODE_MAIL_SEND_FAILED, "验证码邮件发送失败，请稍后重试")

    if sent:
        return make_response(CODE_SUCCESS, "验证码已发送，请查收邮件")
    return make_response(CODE_SUCCESS, "验证码已生成，请到后端控制台查看（当前未配置邮件服务）")