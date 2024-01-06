import requests
import os

from flask import current_app
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    get_jwt,
    jwt_required,
)

from sqlalchemy import or_
from db import db
from models import UserModel
from schemas import UserSchema, UserRegisterSchema
from blocklist import BLOCKLIST
from tasks import send_user_registration_email


'''
在您的代码中，`blp = Blueprint("Items", "items", description="Operations on items")` 创建了一个 Flask-Smorest 蓝图。
这是 Flask-Smorest（一个 Flask 扩展）用于构建 REST API 的特性。以下是这行代码各部分的解释：

1. **创建蓝图实例**:
   - `blp` 是创建的蓝图实例的变量名。
      这个实例将用于注册相关的视图函数或类。

2. **Blueprint 类**:
   - `Blueprint` 是 Flask-Smorest 中用于创建蓝图的类。
      蓝图在 Flask 应用中用于组织和分组功能，类似于 Flask 原生的 `Blueprint`。

3. **参数**:
   - `"Users"` 是蓝图的名字。这个名字通常用于在 Flask 应用中引用或注册蓝图。
   - `"users"` 是蓝图的端点前缀。这通常会作为 URL 前缀用于此蓝图下的所有路由。
               例如，如果您在此蓝图下注册了一个 `/users` 路由，那么完整的 URL 将是 `/users/list`。

   - `description="Operations on items"` 设置了蓝图的描述，这在自动生成 API 文档时特别有用，因为它提供了关于蓝图功能的上下文信息。
'''

blp = Blueprint("Users", "users", description="Operations on users")

@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserRegisterSchema)
    def post(self, user_data):

        # 通过 UserSchema 将 user_data从 JSON 转换 为 Python 字典
        if UserModel.query.filter(
            or_(
                UserModel.username == user_data["username"],
                UserModel.email == user_data["email"]
                )
            ).first():
            abort(409, message = "A user with that username or email already exists.")
        
        user = UserModel(
            username = user_data["username"],
            email = user_data["email"],
            password = pbkdf2_sha256.hash(user_data["password"])
        )

        db.session.add(user)
        db.session.commit()

        # 将 send_user_registration_email 任务 加入 当前app 的 队列
        current_app.queue.enqueue(send_user_registration_email, user.email, user.username)

        return {"message": "User created successfully."}, 201
    
@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(UserModel.username == user_data["username"]).first()

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token( identity = user.id, fresh = True )
            refresh_token = create_refresh_token(identity = user.id)
            return {"access_token": access_token, "refresh_token": refresh_token}

        abort(401, message = "Invalid crendentials")

@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh = True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity = current_user, fresh = False)
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"access_token": new_token}

@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        # get_jwt() 返还一个 字典
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out"}, 200

@blp.route("/user/<int:user_id>")
class User(MethodView):
    """
    This resource can be useful when testing our Flask app.
    We may not want to expose it to public users, but for the
    sake of demonstration in this course, it can be useful
    when we are manipulating data regarding the users.
    """ 
    # 从路由获取user_id
    @blp.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user

    # 从路由获取user_id
    def delete(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted."}, 200