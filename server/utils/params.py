"""请求参数处理工具：后续新增接口直接复用，避免重复写校验与取值逻辑。"""
import re

from flask import request

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50


def get_body():
    """安全地取出 JSON 请求体。

    request.get_json(silent=True) 在请求体缺失或不是合法 JSON 时返回 None，
    直接 .get() 会抛 AttributeError，这里统一兜底为空字典。
    """
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else {}


def clean(value):
    """转成字符串并去掉首尾空白，None 归一化为空串。"""
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return value.strip()


def require(body, *fields):
    """返回缺失（或为空）的字段名列表，供接口拼 1001 的提示信息。"""
    return [field for field in fields if not clean(body.get(field))]


def is_valid_email(email):
    """常规邮箱格式校验。"""
    return bool(EMAIL_PATTERN.match(email or ""))


def parse_page_args():
    """解析分页参数，非法值回退默认值，page_size 限制上限。"""
    page = _to_positive_int(request.args.get("page"), DEFAULT_PAGE)
    page_size = _to_positive_int(request.args.get("page_size"), DEFAULT_PAGE_SIZE)
    return page, min(page_size, MAX_PAGE_SIZE)


def _to_positive_int(raw, default):
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default