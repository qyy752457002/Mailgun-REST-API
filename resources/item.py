from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import ItemModel
from schemas import ItemSchema, ItemUpdateSchema

''' 
    "Items": 这是蓝图的名字，用于标识蓝图。这个名字在整个应用中需要是唯一的。
             在注册到 Flask 应用时，它将用于区分不同的蓝图。

     __name__: 这通常用于指定蓝图所在的模块或包。
               这有助于 Flask 找到相对于该蓝图的资源位置，如模板文件夹或静态文件夹。
               传递 __name__ 是常见的做法，它告诉 Flask 去查找和当前模块同名的模块或包。

    description="Operations on items": 这是对蓝图的描述。

                                       在使用 flask_smorest 扩展时，
                                       这个描述可以用于自动生成的 API 文档中，
                                       作为该蓝图功能的简介。
'''

blp = Blueprint("Items", __name__, description="Operations on items")

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
