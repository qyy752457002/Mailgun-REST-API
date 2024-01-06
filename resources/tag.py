from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError

from db import db
from models import TagModel, StoreModel, ItemModel
from schemas import TagSchema, TagAndItemSchema

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
   - `"Tags"` 是蓝图的名字。这个名字通常用于在 Flask 应用中引用或注册蓝图。
   - `"tags"` 是蓝图的端点前缀。这通常会作为 URL 前缀用于此蓝图下的所有路由。
               例如，如果您在此蓝图下注册了一个 `/tag` 路由，那么完整的 URL 将是 `/tags/list`。

   - `description="Operations on items"` 设置了蓝图的描述，这在自动生成 API 文档时特别有用，因为它提供了关于蓝图功能的上下文信息。
'''

blp = Blueprint("Tags", "tags", description="Operations on tags")

@blp.route("/store/<int:store_id>/tag")
class TagsInStore(MethodView):
    @blp.response(200, TagSchema(many=True))
    # store_id来自路由
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)

        # 一个 store 可能 包含 多个 tags

        # 由于方法被 @blp.response(200, TagSchema(many=True)) 装饰器装饰，
        # Flask-Smorest 将会自动使用 TagSchema 对 列表中的 每一个 tag 实例进行序列化，
        # 并将序列化后的 JSON 数据作为 HTTP 响应的主体返回给客户端。
        return store.tags.all()
    
    @blp.arguments(TagSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        # .first(): 从上述过滤后的记录中获取第一个匹配的记录
        if TagModel.query.filter(TagModel.store_id == store_id, TagModel.name == tag_data["name"]).first():
            abort(400, message = "A tag with that name already exists in that store.")

        tag = TagModel(**tag_data, store_id = store_id)

        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(
                500,
                message = str(e)
            )

        # 由于方法被 @blp.response(201, TagSchema) 装饰器装饰，
        # Flask-Smorest 将会自动使用 TagSchema 对 tag 实例进行序列化，
        # 并将序列化后的 JSON 数据作为 HTTP 响应的主体返回给客户端。
        return tag
    
@blp.route("/item/<int:item_id>/tag/<int:tag_id>")
class LinkTagsToItem(MethodView):
    @blp.response(201, TagSchema)
    # item_id, tag_id 来自路由
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        # item.tags 是一个 列表
        # 往列表中加入新的 tag
        item.tags.append(tag)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting the tag.")

        return tag

    @blp.response(200, TagAndItemSchema)
    # item_id, tag_id 来自路由
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        # item.tags 是一个 列表
        # 往列表中 移除 tag
        item.tags.remove(tag)

        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="An error occurred while inserting the tag.")

        return {"message": "Item removed from tag", "item": item, "tag": tag}
    
@blp.route("/tag/<int:tag_id>")
class Tag(MethodView):
    @blp.response(200, TagSchema)
    # tag_id来自路由
    def get(self, tag_id):

        tag = TagModel.query.get_or_404(tag_id)

        # 由于方法被 @blp.response(200, TagSchema) 装饰器装饰，
        # Flask-Smorest 将会自动使用 TagSchema 对 tag 实例进行序列化，
        # 并将序列化后的 JSON 数据作为 HTTP 响应的主体返回给客户端。
        return tag
    
    '''
    这段代码定义了一个用于删除标签（Tag）的方法，并且它包含了多个装饰器来处理不同的响应场景。我将逐个解释这些装饰器以及方法的逻辑。

    ### 1. `@blp.response` 装饰器:

    - `@blp.response(202, description="Deletes a tag if no item is tagged with it.", example={"message": "Tag deleted."})`:
    - 这个装饰器定义了成功删除标签时的响应类型。
    - 状态码 `202` 表示请求已被接受处理，但处理尚未完成。
    - `description` 提供了关于响应的简要信息。
    - `example` 提供了响应体的示例。

    ### 2. `@blp.alt_response` 装饰器:

    - `@blp.alt_response(404, description="Tag not found.")`:
    - 这个装饰器定义了当标签未找到时的响应类型。
    - 状态码 `404` 表示未找到指定的资源。

    - `@blp.alt_response(400, description="Returned if the tag is assigned to one or more items. In this case, the tag is not deleted.")`:
    - 定义了如果标签与一个或多个物品相关联时的响应类型。
    - 状态码 `400` 表示由于客户端错误，请求无法完成。

    ### 3. `delete` 方法逻辑:

    - 方法首先尝试通过 `tag_id` 获取 `TagModel` 实例。如果没有找到相应的标签，则 `get_or_404` 会自动中断处理并返回一个 `404 Not Found` 响应。
    - 如果找到了标签，代码会检查这个标签是否与任何物品相关联。这是通过检查 `tag.items` 来完成的，其中 `items` 是与 `TagModel` 关联的物品集合。
    - 如果 `tag.items` 为空，说明没有物品与此标签相关联，标签可以安全删除。随后代码会从数据库中删除该标签并提交更改。
    - 如果标签有相关联的物品，则调用 `abort` 函数，返回一个 `400 Bad Request` 响应，表示由于标签当前与一个或多个物品相关联，因此不能删除。

    这段代码非常适合处理依赖于其他实体存在的实体的删除操作。它确保在删除标签之前，标签不再与任何物品相关联，从而避免了潜在的数据一致性问题。   
    
    '''
    @blp.response(
        202,
        description="Deletes a tag if no item is tagged with it.",
        example={"message": "Tag deleted."},
    )
    @blp.alt_response(404, description="Tag not found.")
    @blp.alt_response(
        400,
        description="Returned if the tag is assigned to one or more items. In this case, the tag is not deleted.",
    )
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)

        if not tag.items:
            db.session.delete(tag)
            db.session.commit()
            return {"message": "Tag deleted."}
        abort(
            400,
            message="Could not delete tag. Make sure tag is not associated with any items, then try again.",  # noqa: E501
        )
