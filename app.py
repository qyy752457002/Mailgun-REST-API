from flask import Flask, jsonify
from dotenv import load_dotenv
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from rq import Queue
from db import db
from blocklist import BLOCKLIST

import redis
import os
import secrets
import models

from resources.item import blp as ItemBlueprint
from resources.store import blp as StoreBlueprint
from resources.tag import blp as TagBlueprint
from resources.user import blp as UserBlueprint

def create_app(db_url=None):
    app = Flask(__name__)
    load_dotenv()

    '''
    您贴出的代码片段似乎是用来建立与 Redis 服务器的连接，并用这个连接创建一个用于处理电子邮件任务的作业队列。
    下面是代码的详细解释：

    1. connection = redis.from_url(os.getenv("REDIS_URL")): 这行代码使用 redis 库根据环境变量 REDIS_URL 的值来创建一个 Redis 连接。
    这个环境变量应该包含 Redis 服务器的完整 URL，包括协议、用户名、密码、主机名、端口号和数据库编号（如果需要）。

    2. app.queue = Queue("emails", connection=connection): 这行代码使用前面创建的 Redis 连接来初始化一个名为 "emails" 的队列，
    并将这个队列作为 app 对象的 queue 属性。

    这样做的目的是为了在应用程序的其他部分能够使用 app.queue 来加入电子邮件任务。
    '''

    # 建立connection
    connection = redis.from_url(
        os.getenv("REDIS_URL")
    )

    # app 绑定 queue
    app.queue = Queue("emails", connection = connection)

    app.config["API_TITLE"] = "Stores REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["PROPAGATE_EXCEPTIONS"] = True

    db.init_app(app)
    migrate = Migrate(app, db)

    api = Api(app)

    ### 这段代码中定义了不同的回调函数来处理与JWT相关的各种情况

    # 设置用于签名和解码JWT的密钥
    app.config["JWT_SECRET_KEY"] = "jose"
    # 初始化JWTManager与Flask应用
    jwt = JWTManager(app)

    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        if identity == 1:
            return {"is_admin": True}
        return {"is_admin": False}

    # 检查令牌是否在黑名单中：
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST

    # 处理过期的令牌：
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify({"message": "The token has expired.", "error": "token_expired"}),
            401,
        )

    # 处理无效的令牌：
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {"message": "Signature verification failed.", "error": "invalid_token"}
            ),
            401,
        )

    # 处理缺失令牌的情况：
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "description": "Request does not contain an access token.",
                    "error": "authorization_required",
                }
            ),
            401,
        )

    # 处理不是新鲜令牌的情况：
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "description": "The token is not fresh.",
                    "error": "fresh_token_required",
                }
            ),
            401,
        )

    # 处理被撤销的令牌：
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {"description": "The token has been revoked.", "error": "token_revoked"}
            ),
            401,
        )

    with app.app_context():
        db.create_all()

    # 将 ItemBlueprint蓝图 注册到 Flask 应用
    api.register_blueprint(ItemBlueprint)
    # 将 StoreBlueprint蓝图 注册到 Flask 应用
    api.register_blueprint(StoreBlueprint)
    # 将 TagBlueprint蓝图 注册到 Flask 应用
    api.register_blueprint(TagBlueprint)
    # 将 UserBlueprint蓝图 注册到 Flask 应用
    api.register_blueprint(UserBlueprint)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)


