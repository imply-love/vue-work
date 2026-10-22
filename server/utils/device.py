"""从 User-Agent 解析设备/浏览器摘要，用于登录记录展示。"""

# 浏览器识别规则：按顺序匹配，命中即返回
_BROWSER_RULES = [
    ("Edg/", "Edge"),
    ("Chrome/", "Chrome"),
    ("Firefox/", "Firefox"),
    ("Safari/", "Safari"),
    ("OPR/", "Opera"),
    ("MSIE ", "IE"),
    ("Trident/", "IE"),
]

# 操作系统识别规则：按顺序匹配，命中即返回
_OS_RULES = [
    ("Windows NT 10.0", "Windows 10/11"),
    ("Windows NT 6.3", "Windows 8.1"),
    ("Windows NT 6.1", "Windows 7"),
    ("Windows", "Windows"),
    ("Mac OS X", "macOS"),
    ("iPhone", "iPhone"),
    ("iPad", "iPad"),
    ("Android", "Android"),
    ("Linux", "Linux"),
]


def parse_user_agent(user_agent):
    """把 UA 字符串解析成「系统 + 浏览器」摘要，例如「Windows 10/11 · Chrome」。

    解析失败或 UA 为空时返回空串，不抛异常。
    """
    ua = user_agent or ""
    if not ua.strip():
        return ""

    browser = next((label for token, label in _BROWSER_RULES if token in ua), "浏览器")
    os_name = next((label for token, label in _OS_RULES if token in ua), "未知系统")

    # 移动端标识：iPhone/Android/iPad 已在系统规则里体现，这里不再单独标注
    return f"{os_name} · {browser}"


def extract_client_ip(request):
    """从请求中提取客户端 IP。

    优先取 X-Forwarded-For 第一个地址（反向代理场景），否则取 remote_addr。
    """
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    return (request.remote_addr or "")[:45]
