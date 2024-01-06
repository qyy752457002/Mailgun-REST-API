from db import db

class StoreModel(db.Model):
    __tablename__ = "stores"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    # lazy="dynamic": 设置加载关系的方式
    # "dynamic" 使得这个关系成为一个在实际访问时才加载的查询，允许在其上执行进一步的查询操作，例如过滤和排序

    # cascade="all, delete": 指定级联行为
    # 在这种情况下，当删除 StoreModel 实例时，所有与之关联的 ItemModel 实例也将被删除。
    items = db.relationship("ItemModel", back_populates="store", lazy="dynamic", cascade="all, delete")
    tags = db.relationship("TagModel", back_populates = "store", lazy="dynamic")
