"""邮箱验证码：生成、落库、校验。

注册与换绑邮箱共用同一张 email_codes 表，用 scene 区分场景，
避免注册用的验证码被拿去换绑邮箱（反之亦然）。
"""
import random
import string

from db import execute, query_one

# 验证码规则
CODE_LENGTH = 6
CODE_EXPIRE_SECONDS = 5 * 60  # 有效期 5 分钟
CODE_RESEND_INTERVAL = 60  # 同一邮箱同一场景 60 秒内只能发一次

# 场景
SCENE_REGISTER = "register"
SCENE_BIND_EMAIL = "bind_email"


def generate_code():
    """生成 6 位纯数字验证码。"""
    return "".join(random.choices(string.digits, k=CODE_LENGTH))


def send_interval_left(email, scene):
    """距离下次可发送还剩多少秒，0 表示现在可以发。"""
    row = query_one(
        "SELECT TIMESTAMPDIFF(SECOND, create_time, NOW()) AS elapsed "
        "FROM email_codes WHERE email=%s AND scene=%s ORDER BY id DESC LIMIT 1",
        (email, scene),
    )
    if row is None or row["elapsed"] is None:
        return 0
    remain = CODE_RESEND_INTERVAL - int(row["elapsed"])
    return remain if remain > 0 else 0


def create_code(email, scene):
    """写入一条新验证码，返回 (记录ID, 验证码明文)。"""
    code = generate_code()
    code_id = execute(
        "INSERT INTO email_codes (email, code, scene, expire_time) "
        "VALUES (%s, %s, %s, DATE_ADD(NOW(), INTERVAL %s SECOND))",
        (email, code, scene, CODE_EXPIRE_SECONDS),
    )
    return code_id, code


def discard_code(code_id):
    """作废一条验证码（发信失败时调用，让用户可以立刻重试）。"""
    execute("DELETE FROM email_codes WHERE id=%s", (code_id,))


def check_code(email, scene, code):
    """校验验证码：取最新一条未使用且未过期的记录比对，通过后立即置为已使用。"""
    if not code:
        return False

    row = query_one(
        "SELECT id, code FROM email_codes "
        "WHERE email=%s AND scene=%s AND used=0 AND expire_time > NOW() "
        "ORDER BY id DESC LIMIT 1",
        (email, scene),
    )
    if row is None or row["code"] != code:
        return False

    # 一次性使用：校验通过就作废，避免同一个码被反复提交
    execute("UPDATE email_codes SET used=1 WHERE id=%s", (row["id"],))
    return True