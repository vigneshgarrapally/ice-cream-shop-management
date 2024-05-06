import random
from datetime import datetime, timedelta
from app import db, app
from app.models import Order, OrderItem, Product, User


# Randomly generate orders within the past year
def generate_dates(num_days, num_orders):
    base = datetime.today()
    date_list = [base - timedelta(days=x) for x in range(num_days)]
    return random.choices(date_list, k=num_orders)


def generate_sample_orders(num_orders=100):
    with app.app_context():
        users = User.query.all()
        products = Product.query.all()

        if not users or not products:
            print("Make sure there are users and products in the database.")
            return

        for _ in range(num_orders):
            user = random.choice(users)
            date = random.choice(
                generate_dates(6, 1)
            )  # Generate random dates within the last year
            total_price = 0
            items = []

            order = Order(
                user_id=user.id,
                order_time=date,
                total_amount=0,  # to be calculated
                gst_amount=0,
                final_amount=0,
                status="Completed",
            )

            # Add 1 to 5 items per order
            for _ in range(random.randint(1, 5)):
                product = random.choice(products)
                quantity = random.randint(1, 10)
                item_price = product.price * quantity
                total_price += item_price

                order_item = OrderItem(
                    product_id=product.id,
                    quantity=quantity,
                    item_price=item_price,
                )
                items.append(order_item)

            gst = total_price * 0.18  # 18% GST
            final_amount = total_price + gst

            order.total_amount = total_price
            order.gst_amount = gst
            order.final_amount = final_amount

            db.session.add(order)
            for item in items:
                item.order = order
                db.session.add(item)

        db.session.commit()
        print(f"{num_orders} sample orders have been created.")


if __name__ == "__main__":
    generate_sample_orders(20)  # Generate 500 sample orders
