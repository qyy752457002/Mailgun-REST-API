from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from db import db
from models import StoreModel
from schemas import StoreSchema

''' 
    "Stores": 这是蓝图的名字，用于标识蓝图。这个名字在整个应用中需要是唯一的。
             在注册到 Flask 应用时，它将用于区分不同的蓝图。

     __name__: 这通常用于指定蓝图所在的模块或包。
               这有助于 Flask 找到相对于该蓝图的资源位置，如模板文件夹或静态文件夹。
               传递 __name__ 是常见的做法，它告诉 Flask 去查找和当前模块同名的模块或包。

    description="Operations on stores": 这是对蓝图的描述。

                                       在使用 flask_smorest 扩展时，
                                       这个描述可以用于自动生成的 API 文档中，
                                       作为该蓝图功能的简介。
'''

blp = Blueprint("Stores", __name__, description="Operations on stores")

@blp.route("/store/<int:store_id>")
class Store(MethodView):
    @blp.response(200, StoreSchema)
    # store_id来自路由
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)

        # 由于方法被 @blp.response(200, StoreSchema) 装饰器装饰，
        # Flask-Smorest 将会自动使用 StoreSchema 对 store 实例进行序列化，
        # 并将序列化后的 JSON 数据作为 HTTP 响应的主体返回给客户端。
        return store

    # store_id来自路由
    def delete(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        db.session.delete(store)
        db.session.commit()
        return {"message": "Store deleted"}, 200

@blp.route("/store")
class StoreList(MethodView):
    @blp.response(200, StoreSchema(many=True))
    def get(self):

        # 查询并返回 StoreModel 表中的所有数据记录
        # 这些记录将是包含一系列 StoreModel 的实例的 列表

        stores = StoreModel.query

        # 由于方法被 @blp.response(200, StoreSchema(many=True)) 装饰器装饰，
        # Flask-Smorest 将会自动使用 StoreSchema 对 列表中 的 每一个 store 实例进行序列化，
        # 并将序列化后的 一个列表 的 JSON 数据作为 HTTP 响应的主体返回给客户端。
        return stores.all()

    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        store = StoreModel(**store_data)
        try:
            db.session.add(store)
            db.session.commit()
        except IntegrityError:
            abort(
                400,
                message="A store with that name already exists.",
            )
        except SQLAlchemyError:
            abort(500, message="An error occurred creating the store.")

        # 由于方法被 @blp.response(200, StoreSchema) 装饰器装饰，
        # Flask-Smorest 将会自动使用 StoreSchema 对 store 实例进行序列化，
        # 并将序列化后的 JSON 数据作为 HTTP 响应的主体返回给客户端。
        return store
