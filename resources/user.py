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
    "Users": 这是蓝图的名字，用于标识蓝图。这个名字在整个应用中需要是唯一的。
             在注册到 Flask 应用时，它将用于区分不同的蓝图。

     __name__: 这通常用于指定蓝图所在的模块或包。
               这有助于 Flask 找到相对于该蓝图的资源位置，如模板文件夹或静态文件夹。
               传递 __name__ 是常见的做法，它告诉 Flask 去查找和当前模块同名的模块或包。

    description="Operations on users": 这是对蓝图的描述。

                                       在使用 flask_smorest 扩展时，
                                       这个描述可以用于自动生成的 API 文档中，
                                       作为该蓝图功能的简介。
'''

blp = Blueprint("Users", __name__, description="Operations on users")

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
        # get_jwt() 返还一个 字典
        # 获取当前请求的 JWT
        # "jti" 是 JWT 的一个标准字段，代表 "JWT ID"。这是一个唯一标识符，用于标识该令牌的实例
        # 这行代码的作用是从当前请求的 JWT 中提取 jti 值，并将其存储在变量 jti 中
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"access_token": new_token}

@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        # get_jwt() 返还一个 字典
        # 获取当前请求的 JWT
        # "jti" 是 JWT 的一个标准字段，代表 "JWT ID"。这是一个唯一标识符，用于标识该令牌的实例
        # 这行代码的作用是从当前请求的 JWT 中提取 jti 值，并将其存储在变量 jti 中
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