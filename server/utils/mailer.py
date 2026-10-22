"""验证码邮件发送。

未配置 SMTP 账号（Config.MAIL_ENABLED 为 False）时不真的发信，
改为把验证码打印到后端控制台，保证本地开发也能跑通完整注册流程；
在 .env 里填上 MAIL_USERNAME / MAIL_PASSWORD 后自动切换为真实发信。
"""
import logging
import smtplib
from email.header import Header
from email.mime.text import MIMEText

from config import Config
from utils.verify_code import CODE_EXPIRE_SECONDS

logger = logging.getLogger(__name__)

MAIL_SUBJECT = "【番剧同好会】邮箱验证码"
SMTP_TIMEOUT_SECONDS = 10


def send_verify_code(email, code):
    """发送验证码邮件。

    :return: (是否真实发出, 失败原因)，失败原因非 None 表示发信失败
    """
    if not Config.MAIL_ENABLED:
        _print_code(email, code)
        return False, None

    message = MIMEText(_build_text(code), "plain", "utf-8")
    message["Subject"] = Header(MAIL_SUBJECT, "utf-8")
    message["From"] = "%s <%s>" % (
        Header(Config.MAIL_FROM_NAME, "utf-8").encode(),
        Config.MAIL_USERNAME,
    )
    message["To"] = email

    try:
        if Config.MAIL_USE_SSL:
            server = smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=SMTP_TIMEOUT_SECONDS)
        else:
            server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT, timeout=SMTP_TIMEOUT_SECONDS)
            server.starttls()

        with server:
            server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
            server.sendmail(Config.MAIL_USERNAME, [email], message.as_string())
    except (smtplib.SMTPException, OSError) as exc:
        logger.error("验证码邮件发送失败：%s", exc)
        return False, str(exc)

    return True, None


def _build_text(code):
    """邮件正文。"""
    return (
        "你的邮箱验证码是：%s\n\n"
        "验证码 %d 分钟内有效，请勿转发给他人。\n"
        "如果这不是你本人的操作，忽略这封邮件即可。"
    ) % (code, CODE_EXPIRE_SECONDS // 60)


def _print_code(email, code):
    """未配置邮件服务时，把验证码输出到控制台。"""
    print(
        "\n"
        "==================== 邮箱验证码（开发模式）====================\n"
        "  收件邮箱：%s\n"
        "  验证码　：%s\n"
        "  有效期　：%d 分钟\n"
        "  提示：在 server/.env 配置 MAIL_USERNAME / MAIL_PASSWORD 后改为真实发信\n"
        "=============================================================" % (
            email, code, CODE_EXPIRE_SECONDS // 60
        ),
        flush=True,
    )