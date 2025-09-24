from database import db

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    plan = db.Column(db.String(50))
    status = db.Column(db.Enum('active','inactive'), default='active')

    consumptions = db.relationship('Consumption', backref='customer', cascade="all, delete-orphan")
    billings = db.relationship('Billing', backref='customer', cascade="all, delete-orphan")
    services = db.relationship('CustomerService', backref='customer', cascade="all, delete-orphan")


class Consumption(db.Model):
    __tablename__ = 'consumption'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.String(20), db.ForeignKey('customers.id'))
    type = db.Column(db.Enum('data','minutes','sms'), nullable=False)
    used = db.Column(db.Numeric(10,2), nullable=False)
    total = db.Column(db.Numeric(10,2), nullable=False)
    unit = db.Column(db.String(10), nullable=False)
    percentage = db.Column(db.Numeric(5,2))
    reset_date = db.Column(db.Date)


class Billing(db.Model):
    __tablename__ = 'billing'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.String(20), db.ForeignKey('customers.id'))
    current_balance = db.Column(db.Numeric(10,2))
    currency = db.Column(db.String(10))
    next_bill_date = db.Column(db.Date)
    monthly_fee = db.Column(db.Numeric(10,2))

    payments = db.relationship('BillingPayment', backref='billing', cascade="all, delete-orphan")


class BillingPayment(db.Model):
    __tablename__ = 'billing_payments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    billing_id = db.Column(db.Integer, db.ForeignKey('billing.id'))
    amount = db.Column(db.Numeric(10,2))
    payment_date = db.Column(db.Date)
    method = db.Column(db.String(50))


class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    status = db.Column(db.Enum('active','inactive'), default='active')

    customers = db.relationship('CustomerService', backref='service', cascade="all, delete-orphan")


class CustomerService(db.Model):
    __tablename__ = 'customer_services'
    customer_id = db.Column(db.String(20), db.ForeignKey('customers.id'), primary_key=True)
    service_id = db.Column(db.String(20), db.ForeignKey('services.id'), primary_key=True)
