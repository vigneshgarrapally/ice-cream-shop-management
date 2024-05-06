from app import db, app
from app.models import Product

# Define the products to add
products = [
    {"name": "Ice Cream", "size": "Small", "price": 4.00},
    {"name": "Ice Cream", "size": "Medium", "price": 5.00},
    {"name": "Ice Cream", "size": "Large", "price": 8.00},
    {"name": "Smoothie", "size": "Small", "price": 10.00},
    {"name": "Smoothie", "size": "Large", "price": 11.00},
    {"name": "Shake", "size": "Small", "price": 10.00},
    {"name": "Shake", "size": "Large", "price": 11.00},
    {"name": "Water Bottle", "size": "Standard", "price": 3.00},
    {"name": "Soda", "size": "Standard", "price": 4.00},
]


def add_products():
    with app.app_context():
        for product in products:
            # Check if the product already exists to avoid duplicates
            existing_product = Product.query.filter_by(
                name=product["name"], size=product["size"]
            ).first()
            if not existing_product:
                new_product = Product(
                    name=product["name"],
                    size=product["size"],
                    price=product["price"],
                )
                db.session.add(new_product)

        db.session.commit()
        print("Products added successfully.")


if __name__ == "__main__":
    add_products()
