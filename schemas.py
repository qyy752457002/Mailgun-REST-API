from marshmallow import Schema, fields

'''
在软件开发和数据处理中，schema（模式）扮演了非常重要的角色。特别是在使用像 Marshmallow 这样的库进行序列化和反序列化操作时，schema 显得尤为重要。
以下是 schema 的主要作用：

1. **数据验证（Data Validation）**:
   - Schema 定义了数据的结构，包括哪些字段是必需的、它们的数据类型（如字符串、整数、浮点数等）、以及其他验证规则（如字符串长度限制、数字范围等）。
     这确保了只有符合这些规则的数据才能被接受和处理。

2. **序列化（Serialization）**:
   - 在将数据发送给客户端（比如 API 响应）之前，schema 用于将复杂的数据类型（如 ORM 对象）转换成简单的数据类型（通常是 JSON 格式）。
     这使得数据易于在网络上传输，并能被客户端轻松解析。

3. **反序列化（Deserialization）**:
   - Schema 也用于将客户端发送的简单数据（如 JSON）转换回复杂的数据类型，以便在服务器端进行处理。这通常发生在处理客户端的请求数据时。

4. **数据格式化（Data Formatting）**:
   - Schema 可以定义数据如何被格式化或转换。例如，你可以在 schema 中定义一个日期字段应该如何从字符串转换为 Python 的 `datetime` 对象，或者反过来。

5. **文档生成（Documentation Generation）**:
   - 在一些现代的 Web 框架中，schema 可以用于自动生成 API 文档。例如，根据 schema 自动生成的文档可以告诉开发人员哪些字段是必需的、它们的类型是什么，以及该 API 的其他相关信息。

6. **简化代码和提高可维护性**:
   - 使用 schema 来定义数据结构可以使代码更加简洁、易于理解和维护。
     它提供了一个中央位置来定义和更改与特定数据类型相关的规则和逻辑，而不是在代码库中的多个位置。

总的来说，schema 使得在不同的系统、组件或服务之间交换数据变得更加安全、可靠和高效。
通过预先定义数据的结构和规则，schema 减少了出错的可能性，并确保了数据的一致性和完整性。

'''

# 序列化: Python 数据类型 转换为 JSON
# 反序列化: JSON 转换为 Python 数据类型

'''
对应 ItemModel 的 id, name, price 属性
'''
class PlainItemSchema(Schema):
    
    # 标记为 dump_only 表示它仅用于序列化数据时,
    # 即返回给客户端的响应中会包含这个字段，但不会用于接收客户端的输入。
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    price = fields.Float(required=True)

'''
对应 StoreModel 的 id, name 属性
'''
class PlainStoreSchema(Schema):

    # 标记为 dump_only 表示它仅用于序列化数据时,
    # 即返回给客户端的响应中会包含这个字段，但不会用于接收客户端的输入。
    id = fields.Int(dump_only=True)
    name = fields.Str()

'''
对应 TagModel 的 id, name 属性
'''
class PlainTagSchema(Schema):

    # 标记为 dump_only 表示它仅用于序列化数据时,
    # 即返回给客户端的响应中会包含这个字段，但不会用于接收客户端的输入。
    id = fields.Int(dump_only=True)
    name = fields.Str()

'''
对应 ItemModel 的 store_id, store, tags 属性
'''
class ItemSchema(PlainItemSchema):

    # 标记为 load_only,
    # 这意味着它仅用于加载（反序列化）数据时，比如在创建或更新物品时从请求中读取数据,
    # 但它不会包含在序列化（返回给客户端）的数据中。
    store_id = fields.Int(required=True, load_only=True)

    # store 字段是一个嵌套的对象,
    # 其结构和数据应按照 PlainStoreSchema 模式来序列化。
    store = fields.Nested(PlainStoreSchema(), dump_only=True)

    tags = fields.List(fields.Nested(PlainTagSchema()), dump_only=True)

'''
对应 ItemModel 的 name, price 属性
'''
class ItemUpdateSchema(Schema):
    name = fields.Str()
    price = fields.Float()

'''
对应 StoreModel 的 items, tags 属性
'''
class StoreSchema(PlainStoreSchema):

    # items 字段是一个列表，其中每个元素都是一个嵌套的 PlainItemSchema 对象
    # 当你从数据库中获取一个商店对象，并使用 StoreSchema 对其进行序列化时，结果将包括商店的所有信息以及一个包含该商店所有物品的列表。
    # 每个物品都按照 PlainItemSchema 的格式来展示
    items = fields.List(fields.Nested(PlainItemSchema()), dump_only=True)

    tags = fields.List(fields.Nested(PlainTagSchema()), dump_only=True)

'''
对应 StoreModel 的 store_id, store, items 属性
'''
class TagSchema(PlainTagSchema):

    # 标记为 load_only,
    # 这意味着它仅用于加载（反序列化）数据时，比如在创建或更新物品时从请求中读取数据,
    # 但它不会包含在序列化（返回给客户端）的数据中。
    store_id = fields.Int(load_only=True)

    # store 字段是一个嵌套的对象,
    # 其结构和数据应按照 PlainStoreSchema 模式来序列化。
    store = fields.Nested(PlainStoreSchema(), dump_only=True)

    items = fields.List(fields.Nested(PlainItemSchema()), dump_only=True)

class TagAndItemSchema(Schema):
    message = fields.Str()
    item = fields.Nested(ItemSchema)
    tag = fields.Nested(TagSchema)

class UserSchema(Schema):
    id = fields.Int(dump_only = True)
    username = fields.Str(required = True)
    password = fields.Str(required = True, load_only = True)

class UserRegisterSchema(UserSchema):
    email = fields.Str(required = True)