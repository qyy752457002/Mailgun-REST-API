from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import ItemModel
from schemas import ItemSchema, ItemUpdateSchema

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
   - `"Items"` 是蓝图的名字。这个名字通常用于在 Flask 应用中引用或注册蓝图。
   - `"items"` 是蓝图的端点前缀。这通常会作为 URL 前缀用于此蓝图下的所有路由。
               例如，如果您在此蓝图下注册了一个 `/list` 路由，那么完整的 URL 将是 `/items/list`。

   - `description="Operations on items"` 设置了蓝图的描述，这在自动生成 API 文档时特别有用，因为它提供了关于蓝图功能的上下文信息。
'''

blp = Blueprint("Items", "items", description="Operations on items")

@blp.route("/item/<int:item_id>")
class Item(MethodView):
    @jwt_required()
    @blp.response(200, ItemSchema)
    # item_id来自路由
    def get(self, item_id):
        item = ItemModel.query.get_or_404(item_id)

        # 由于方法被 @blp.response(200, ItemSchema) 装饰器装饰，
        # Flask-Smorest 将会自动使用 ItemSchema 对 item 实例进行序列化，
        # 并将序列化后的 JSON 数据作为 HTTP 响应的主体返回给客户端。
        return item
    
    # item_id来自路由
    @jwt_required()
    def delete(self, item_id):
        jwt = get_jwt()
        if not jwt.get("is_admin"):
            abort(401, message = "Admin privilege required.")
        item = ItemModel.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return {"message": "Item deleted."}
    
    '''
    @blp.arguments(ItemUpdateSchema):

    - 这个装饰器用于解析和验证客户端请求体中的数据。
    - ItemUpdateSchema 是一个 Marshmallow Schema，定义了期望接收的数据结构和验证规则。
    - 当客户端发起 PUT 请求并发送数据到服务器时，Flask-Smorest 会使用 ItemUpdateSchema 来解析和验证这些数据。
    - 如果数据有效，它会被转换成 Python 字典，并作为 item_data 参数传递给 put 方法。
    
    '''

    @blp.arguments(ItemUpdateSchema)
    @blp.response(200, ItemSchema)
    def put(self, item_data, item_id):
        # 获取数据库 表 中，对应该 item_id的 item实例对象
        item = ItemModel.query.get(item_id)

        # 如果找到了：

        # item_data 是一个 由 ItemUpdateSchema 转换成 的 字典 
        # 对应 ItemUpdateSchema 中的 name属性 与 price属性
        if item:
            item.price = item_data["price"]
            item.name = item_data["name"]

        # 如果没有找到:
            
        # 根据 item_data 和 item_id 创建一个新的 ItemModel 实例
        # 因为 item_data 是 字典，所以 这边用 **item_data
        else:
            item = ItemModel(id=item_id, **item_data)

        db.session.add(item)
        db.session.commit()

        ''' 
        {
            "id": 1,
            "name": "Example Item",
            "price": 19.99,
            "store": {
                // 这里是 store 对象的详细信息，根据 PlainStoreSchema 结构
            },
            "tags": [
                // 这里是与该 item 相关联的 tags 列表
            ]
        }
        
        '''
        # 由于方法被 @blp.response(200, ItemSchema) 装饰器装饰，
        # Flask-Smorest 将会自动使用 ItemSchema 对 item 实例进行序列化，
        # 并将序列化后的 JSON 数据作为 HTTP 响应的主体返回给客户端。
        return item

@blp.route("/item")
class ItemList(MethodView):
    @jwt_required()
    @blp.response(200, ItemSchema(many=True))
    def get(self):

        # 查询并返回 ItemModel 表中的所有数据记录
        # 这些记录将是包含一系列 ItemModel 的实例的 列表

        items = ItemModel.query

        # 由于方法被 @blp.response(200, ItemSchema(many=True)) 装饰器装饰，
        # Flask-Smorest 将会自动使用 ItemSchema 对 列表中 的 每一个 item 实例进行序列化，
        # 并将序列化后的 一个列表 的 JSON 数据作为 HTTP 响应的主体返回给客户端。
        return items.all()

    @jwt_required(fresh = True)
    @blp.arguments(ItemSchema)
    @blp.response(201, ItemSchema)
    def post(self, item_data):
        
        # 根据当前的item_data字典，建立ItemModel 的 实例对象
        item = ItemModel(**item_data)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting the item.")

        # 由于方法被 @blp.response(201, ItemSchema) 装饰器装饰，
        # Flask-Smorest 将会自动使用 ItemSchema 对 item 实例进行序列化，
        # 并将序列化后的 JSON 数据作为 HTTP 响应的主体返回给客户端。
        return item
