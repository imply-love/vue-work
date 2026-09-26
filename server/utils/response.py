"""统一响应与业务状态码。

所有接口都必须通过本模块返回 JSON，保证前端可以用同一套逻辑处理。
响应体结构沿用后端文档约定：{"code": ..., "message": ..., "data": ...}
"""
import math

from flask import jsonify

# ---- 业务状态码：0 表示成功，非 0 表示失败 ----
CODE_SUCCESS = 0  # 成功
CODE_PARAM_ERROR = 1001  # 参数缺失或格式错误
CODE_USERNAME_EXISTS = 1002  # 该用户名已被注册
CODE_EMAIL_EXISTS = 1003  # 该邮箱已被注册
CODE_USER_NOT_FOUND = 1004  # 用户不存在
CODE_PASSWORD_ERROR = 1005  # 密码错误
CODE_USER_DISABLED = 1006  # 账号已被禁用
CODE_TOKEN_INVALID = 1007  # 登录状态无效或已过期
CODE_NO_PERMISSION = 1008  # 无权访问该资源
CODE_NOT_FOUND = 1009  # 资源不存在
CODE_DB_ERROR = 2000  # 数据库操作失败
CODE_SERVER_ERROR = 3000  # 服务器内部错误


def format_datetime(value):
    """把 datetime 转成前端友好的字符串，避免默认的 RFC 822 格式。"""
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


def make_response(code=CODE_SUCCESS, message="成功", data=None):
    """统一构造 JSON 响应。

    :param code: 业务状态码，0 表示成功
    :param message: 提示信息
    :param data: 返回的数据载荷
    """
    return jsonify({
        "code": code,
        "message": message,
        "data": data,
    })


def make_page_response(items, total, page, page_size, message="获取成功"):
    """构造分页列表响应。

    data 统一为 {"list", "total", "page", "page_size", "total_pages"}，
    后续所有列表接口都复用该结构，前端只需写一套分页逻辑。
    """
    total_pages = math.ceil(total / page_size) if page_size else 0
    return make_response(CODE_SUCCESS, message, {
        "list": items or [],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    })