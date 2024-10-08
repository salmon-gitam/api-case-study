from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager
from models import db
from resources import (
    UserRegister,
    UserLogin,
    ProductListResource,
    ProductResource,
    CartResource,
    OrderResource,
)
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
api = Api(app)
jwt = JWTManager(app)
db.init_app(app)

with app.app_context():
    db.create_all()

# Endpoints
api.add_resource(UserRegister, '/register')
api.add_resource(UserLogin, '/login')
api.add_resource(ProductListResource, '/products')
api.add_resource(ProductResource, '/products/<int:product_id>')
api.add_resource(CartResource, '/cart')
api.add_resource(OrderResource, '/orders')

if __name__ == '__main__':
    app.run(debug=True)
