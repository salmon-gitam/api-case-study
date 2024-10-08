from flask_restful import Resource, reqparse
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    get_jwt_identity,
)
from models import db, User, Product, CartItem, Order, OrderItem

# User Registration Parser
user_registration_parser = reqparse.RequestParser()
user_registration_parser.add_argument('username', type=str, required=True, help='Username is required.')
user_registration_parser.add_argument('password', type=str, required=True, help='Password is required.')

# User Login Parser
user_login_parser = user_registration_parser.copy()

# Product Parser
product_parser = reqparse.RequestParser()
product_parser.add_argument('name', type=str, required=True, help='Product name is required.')
product_parser.add_argument('price', type=float, required=True, help='Product price is required.')
product_parser.add_argument('description', type=str)

# Cart Parser
cart_parser = reqparse.RequestParser()
cart_parser.add_argument('product_id', type=int, required=True, help='Product ID is required.')
cart_parser.add_argument('quantity', type=int, required=True, help='Quantity is required.')

# User Registration Resource
class UserRegister(Resource):
    def post(self):
        data = user_registration_parser.parse_args()
        if User.query.filter_by(username=data['username']).first():
            return {'message': 'User already exists.'}, 400

        user = User(username=data['username'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return {'message': 'User registered successfully.'}, 201

# User Login Resource
class UserLogin(Resource):
    def post(self):
        data = user_login_parser.parse_args()
        user = User.query.filter_by(username=data['username']).first()

        if user and user.verify_password(data['password']):
            access_token = create_access_token(identity=user.id)
            return {'access_token': access_token}, 200
        return {'message': 'Invalid credentials.'}, 401

# Product List Resource
class ProductListResource(Resource):
    def get(self):
        products = Product.query.all()
        return [
            {'id': p.id, 'name': p.name, 'price': p.price, 'description': p.description}
            for p in products
        ], 200

    @jwt_required()
    def post(self):
        data = product_parser.parse_args()
        if Product.query.filter_by(name=data['name']).first():
            return {'message': 'Product already exists.'}, 400

        product = Product(
            name=data['name'],
            price=data['price'],
            description=data.get('description'),
        )
        db.session.add(product)
        db.session.commit()
        return {'message': 'Product added successfully.', 'product': {'id': product.id}}, 201

# Product Resource
class ProductResource(Resource):
    def get(self, product_id):
        product = Product.query.get_or_404(product_id)
        return {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'description': product.description,
        }, 200

    @jwt_required()
    def put(self, product_id):
        data = product_parser.parse_args()
        product = Product.query.get_or_404(product_id)

        product.name = data['name']
        product.price = data['price']
        product.description = data.get('description')
        db.session.commit()
        return {'message': 'Product updated successfully.'}, 200

    @jwt_required()
    def delete(self, product_id):
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        return {'message': 'Product deleted successfully.'}, 200

# Cart Resource
class CartResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        cart_items = CartItem.query.filter_by(user_id=user_id).all()
        return [
            {
                'id': item.id,
                'product': {
                    'id': item.product.id,
                    'name': item.product.name,
                    'price': item.product.price,
                },
                'quantity': item.quantity,
            }
            for item in cart_items
        ], 200

    @jwt_required()
    def post(self):
        data = cart_parser.parse_args()
        user_id = get_jwt_identity()
        product = Product.query.get_or_404(data['product_id'])

        cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product.id).first()
        if cart_item:
            cart_item.quantity += data['quantity']
        else:
            cart_item = CartItem(
                quantity=data['quantity'], product_id=product.id, user_id=user_id
            )
            db.session.add(cart_item)
        db.session.commit()
        return {'message': 'Item added to cart.'}, 201

    @jwt_required()
    def delete(self):
        user_id = get_jwt_identity()
        CartItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return {'message': 'Cart cleared.'}, 200

# Order Resource
class OrderResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        orders = Order.query.filter_by(user_id=user_id).all()
        order_list = []
        for order in orders:
            order_data = {
                'order_id': order.id,
                'total_price': order.total_price,
                'timestamp': order.timestamp.isoformat(),
                'items': [
                    {
                        'product_name': item.product_name,
                        'quantity': item.quantity,
                        'price_per_item': item.price_per_item,
                    }
                    for item in order.order_items
                ],
            }
            order_list.append(order_data)
        return order_list, 200

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        cart_items = CartItem.query.filter_by(user_id=user_id).all()

        if not cart_items:
            return {'message': 'Your cart is empty.'}, 400

        total_price = sum(item.product.price * item.quantity for item in cart_items)
        order = Order(total_price=total_price, user_id=user_id)
        db.session.add(order)
        db.session.commit()

        for item in cart_items:
            order_item = OrderItem(
                product_name=item.product.name,
                quantity=item.quantity,
                price_per_item=item.product.price,
                order_id=order.id,
            )
            db.session.add(order_item)
            db.session.delete(item)

        db.session.commit()
        return {'message': 'Order placed successfully.', 'order_id': order.id}, 201
