from app import db, app, bcrypt
import datetime
from flask_login import UserMixin


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    orders = db.relationship("Order", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)

    order_items = db.relationship("OrderItem", backref="product", lazy=True)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    total_amount = db.Column(db.Float)
    gst_amount = db.Column(db.Float)
    final_amount = db.Column(db.Float)
    order_time = db.Column(
        db.DateTime, default=datetime.datetime.now(datetime.UTC)
    )
    status = db.Column(db.String(20), default="Pending")

    items = db.relationship("OrderItem", backref="order", lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey("order.id"), nullable=False
    )
    product_id = db.Column(
        db.Integer, db.ForeignKey("product.id"), nullable=False
    )
    quantity = db.Column(db.Integer, nullable=False)
    item_price = db.Column(db.Float, nullable=False)


with app.app_context():
    db.create_all()
