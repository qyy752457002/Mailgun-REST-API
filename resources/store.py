from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from db import db
from models import StoreModel
from schemas import StoreSchema

'''
在您的代码中，`blp = Blueprint("Stores", "stores", description="Operations on stores")` 创建了一个 Flask-Smorest 蓝图。
这是 Flask-Smorest（一个 Flask 扩展）用于构建 REST API 的特性。以下是这行代码各部分的解释：

1. **创建蓝图实例**:
   - `blp` 是创建的蓝图实例的变量名。
      这个实例将用于注册相关的视图函数或类。

2. **Blueprint 类**:
   - `Blueprint` 是 Flask-Smorest 中用于创建蓝图的类。
      蓝图在 Flask 应用中用于组织和分组功能，类似于 Flask 原生的 `Blueprint`。

3. **参数**:
   - `"Stores"` 是蓝图的名字。这个名字通常用于在 Flask 应用中引用或注册蓝图。
   - `"stores"` 是蓝图的端点前缀。这通常会作为 URL 前缀用于此蓝图下的所有路由。
               例如，如果您在此蓝图下注册了一个 `/list` 路由，那么完整的 URL 将是 `/stores/list`。

   - `description="Operations on stores"` 设置了蓝图的描述，这在自动生成 API 文档时特别有用，因为它提供了关于蓝图功能的上下文信息。
'''

blp = Blueprint("Stores", "stores", description="Operations on stores")

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
