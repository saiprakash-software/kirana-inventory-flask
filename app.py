from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField
from wtforms.validators import InputRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kirana.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database models
class Shop(db.Model):
    __tablename__ = 'shop'  # Ensure it matches table used in queries
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'))
    shop = db.relationship('Shop', backref='products')

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    quantity = db.Column(db.Integer)
    status = db.Column(db.String(20), default='Placed')
    product = db.relationship('Product')
    customer = db.relationship('Customer')

# Forms
class ShopForm(FlaskForm):
    name = StringField('Shop Name', validators=[InputRequired()])
    location = StringField('Location')
    submit = SubmitField('Submit')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[InputRequired()])
    quantity = IntegerField('Quantity', validators=[InputRequired()])
    shop_id = SelectField('Shop', coerce=int)
    submit = SubmitField('Submit')

class CustomerForm(FlaskForm):
    name = StringField('Customer Name', validators=[InputRequired()])
    submit = SubmitField('Submit')

class OrderForm(FlaskForm):
    product_id = SelectField('Product', coerce=int)
    customer_id = SelectField('Customer', coerce=int)
    quantity = IntegerField('Quantity', validators=[InputRequired()])
    submit = SubmitField('Place Order')

# Routes
@app.route('/')
def index():
    shops = Shop.query.all()
    return render_template('index.html', shops=shops)

@app.route('/dashboard')
def dashboard():
    low_stock = Product.query.filter(Product.quantity < 5).all()
    recent_orders = Order.query.order_by(Order.id.desc()).limit(5).all()
    return render_template('dashboard.html', low_stock=low_stock, orders=recent_orders)

@app.route('/add-shop', methods=['GET', 'POST'])
def add_shop():
    form = ShopForm()
    if form.validate_on_submit():
        shop = Shop(name=form.name.data, location=form.location.data)
        db.session.add(shop)
        db.session.commit()
        flash('✅ Shop added successfully!')
        return redirect(url_for('dashboard'))
    return render_template('form.html', form=form, title='Add Shop')

@app.route('/add-product', methods=['GET', 'POST'])
def add_product():
    form = ProductForm()
    form.shop_id.choices = [(s.id, s.name) for s in Shop.query.all()]
    if form.validate_on_submit():
        product = Product(name=form.name.data, quantity=form.quantity.data, shop_id=form.shop_id.data)
        db.session.add(product)
        db.session.commit()
        flash('✅ Product added successfully!')
        return redirect(url_for('dashboard'))
    return render_template('form.html', form=form, title='Add Product')

@app.route('/add-customer', methods=['GET', 'POST'])
def add_customer():
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(name=form.name.data)
        db.session.add(customer)
        db.session.commit()
        flash('✅ Customer added successfully!')
        return redirect(url_for('dashboard'))
    return render_template('form.html', form=form, title='Add Customer')

@app.route('/place-order', methods=['GET', 'POST'])
def place_order():
    form = OrderForm()
    form.product_id.choices = [(p.id, f"{p.name} (Stock: {p.quantity})") for p in Product.query.all()]
    form.customer_id.choices = [(c.id, c.name) for c in Customer.query.all()]
    if form.validate_on_submit():
        product = Product.query.get(form.product_id.data)
        if product.quantity >= form.quantity.data:
            product.quantity -= form.quantity.data
            order = Order(product_id=form.product_id.data,
                          customer_id=form.customer_id.data,
                          quantity=form.quantity.data)
            db.session.add(order)
            db.session.commit()
            flash('✅ Order placed successfully!')
        else:
            flash('❌ Not enough stock!')
        return redirect(url_for('dashboard'))
    return render_template('form.html', form=form, title='Place Order')

# Run server
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


