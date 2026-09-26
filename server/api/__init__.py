"""接口层：按业务模块拆分蓝图，统一在此注册。

后续新增接口的标准步骤（以回帖为例）：
    1. 新建 api/replies.py，定义
           bp = Blueprint("replies", __name__, url_prefix="/api")
    2. 需要统一响应就 from utils.response import make_response, make_page_response
       需要分页就 from utils.params import parse_page_args + from db import paginate
       需要登录态就 from utils.auth import login_required
    3. 在下方 import 一行、往 BLUEPRINTS 加一项，其余无需改动

api/posts.py 是「公开分页接口」范式，api/users.py 是「需登录接口」范式，可直接照抄。
"""
from api.auth import bp as auth_bp
from api.posts import bp as posts_bp
from api.users import bp as users_bp

BLUEPRINTS = [
    auth_bp,
    posts_bp,
    users_bp,
]


def register_blueprints(app):
    """把 BLUEPRINTS 中的蓝图全部注册到 Flask 应用。"""
    for bp in BLUEPRINTS:
        app.register_blueprint(bp)