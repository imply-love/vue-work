"""登录态 token：用 Flask 自带的 itsdangerous 签名，无需引入 JWT 依赖。

前端登录成功后保存 token，后续请求在请求头带上：
    Authorization: Bearer <token>
"""
from itsdangerous import BadSignature, URLSafeTimedSerializer

from config import Config

_SALT = "yunmo-api"
_TOKEN_KEY = "user_id"


def _serializer():
    return URLSafeTimedSerializer(Config.SECRET_KEY, salt=_SALT)


def generate_token(user_id):
    """为用户签发 token（默认 7 天有效，由 Config.TOKEN_EXPIRE_SECONDS 控制）。"""
    return _serializer().dumps({_TOKEN_KEY: int(user_id)})


def parse_token(token):
    """校验签名与有效期，合法则返回 user_id，否则返回 None。"""
    if not token:
        return None
    try:
        data = _serializer().loads(token, max_age=Config.TOKEN_EXPIRE_SECONDS)
    except BadSignature:
        return None
    user_id = data.get(_TOKEN_KEY)
    return user_id if isinstance(user_id, int) else None