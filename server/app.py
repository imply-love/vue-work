"""云墨江湖 后端入口。

启动方式（在 server 目录下执行）：
    python app.py

接口文档见项目根目录 .trae/documents/登录后端搭建方案.md 的「接口清单」。
"""
import pymysql
from flask import Flask

from api import register_blueprints
from config import Config
from db import close_db
from utils.response import (
    CODE_DB_ERROR,
    CODE_NOT_FOUND,
    CODE_NO_PERMISSION,
    CODE_SERVER_ERROR,
    make_response,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY

# 注册所有业务蓝图（新增接口只需改 api/__init__.py）
register_blueprints(app)

# 请求结束时释放数据库连接
app.teardown_appcontext(close_db)


@app.after_request
def add_cors_headers(response):
    """统一跨域响应头，方便前端（Vite dev server 3000）直接调用。"""
    response.headers["Access-Control-Allow-Origin"] = Config.CORS_ORIGINS
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    return response


@app.errorhandler(404)
def handle_not_found(error):
    """接口不存在时也返回统一的 JSON 结构。"""
    return make_response(CODE_NOT_FOUND, "接口不存在"), 404


@app.errorhandler(405)
def handle_method_not_allowed(error):
    """请求方法不被允许时也返回统一的 JSON 结构。"""
    return make_response(CODE_NO_PERMISSION, "请求方法不被允许"), 405


@app.errorhandler(pymysql.MySQLError)
def handle_db_error(error):
    """数据库异常兜底，避免后续新增接口漏捕获而返回 HTML 错误页。"""
    return make_response(CODE_DB_ERROR, "数据库操作失败"), 500


@app.errorhandler(500)
def handle_server_error(error):
    """服务器内部错误统一结构。"""
    return make_response(CODE_SERVER_ERROR, "服务器内部错误"), 500


# 启动 Flask 应用
if __name__ == "__main__":
    # debug=Config.DEBUG 开启调试模式，代码修改后自动重启
    # host="0.0.0.0" 允许局域网内其他设备访问
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)