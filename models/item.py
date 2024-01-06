from db import db

class ItemModel(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    price = db.Column(db.Float(precision=2), unique=False, nullable=False)
    '''
    注意!!! 如果不用migrations, 就要手动更改数据库中的 item 表，加入description 列
    '''
    description = db.Column(db.String)

    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), unique=False, nullable=False)
    store = db.relationship("StoreModel", back_populates="items")

    tags = db.relationship("TagModel", back_populates = "items", secondary = "items_tags")
