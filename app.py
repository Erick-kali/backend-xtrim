from flask import Flask, request, jsonify
from flask_cors import CORS
from database import db
from models import Customer, Consumption, Billing, BillingPayment, Service, CustomerService
import random
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

# Habilitar CORS para todas las rutas
CORS(app)

# Configuración de MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/telcox'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Crear las tablas
with app.app_context():
    db.create_all()

# -----------------------
# ENDPOINTS PARA TIEMPO REAL
# -----------------------

@app.route('/api/customer/<string:customer_id>/realtime', methods=['GET'])
def get_customer_realtime_data(customer_id):
    """Endpoint consolidado para obtener todos los datos del cliente en tiempo real"""
    try:
        # Obtener datos del cliente
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({"error": "Customer not found"}), 404

        # Obtener consumos
        consumptions = Consumption.query.filter_by(customer_id=customer_id).all()
        
        # Obtener facturación
        billing = Billing.query.filter_by(customer_id=customer_id).first()
        
        # Obtener servicios del cliente
        customer_services = db.session.query(CustomerService.service_id).filter_by(customer_id=customer_id).all()
        service_ids = [cs[0] for cs in customer_services]
        services = Service.query.filter(Service.id.in_(service_ids)).all() if service_ids else []

        # Obtener último pago si existe
        last_payment = None
        if billing:
            payment = BillingPayment.query.filter_by(billing_id=billing.id).order_by(BillingPayment.payment_date.desc()).first()
            if payment:
                last_payment = {
                    "amount": float(payment.amount),
                    "date": str(payment.payment_date),
                    "method": payment.method
                }

        # Construir respuesta
        response = {
            "timestamp": datetime.now().isoformat(),
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "plan": customer.plan,
                "status": customer.status
            },
            "consumption": {
                "data": {"used": 0, "total": 0, "unit": "GB", "percentage": 0, "reset_date": ""},
                "minutes": {"used": 0, "total": 0, "unit": "min", "percentage": 0, "reset_date": ""},
                "sms": {"used": 0, "total": 0, "unit": "SMS", "percentage": 0, "reset_date": ""}
            },
            "billing": {
                "current_balance": 0,
                "currency": "EUR",
                "next_bill_date": "",
                "monthly_fee": 0,
                "last_payment": last_payment
            },
            "services": []
        }

        # Procesar consumos
        for c in consumptions:
            consumption_type = c.type.lower()
            if consumption_type in response["consumption"]:
                response["consumption"][consumption_type] = {
                    "used": float(c.used),
                    "total": float(c.total),
                    "unit": c.unit,
                    "percentage": float(c.percentage) if c.percentage else 0,
                    "reset_date": str(c.reset_date)
                }

        # Procesar facturación
        if billing:
            response["billing"] = {
                "current_balance": float(billing.current_balance) if billing.current_balance else 0,
                "currency": billing.currency or "EUR",
                "next_bill_date": str(billing.next_bill_date),
                "monthly_fee": float(billing.monthly_fee) if billing.monthly_fee else 0,
                "last_payment": last_payment
            }

        # Procesar servicios
        response["services"] = [{
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "status": s.status
        } for s in services]

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": f"Error fetching realtime data: {str(e)}"}), 500

@app.route('/api/customer/<string:customer_id>/simulate-usage', methods=['POST'])
def simulate_usage(customer_id):
    """Simular uso de datos, minutos y SMS para mostrar tiempo real"""
    try:
        # Obtener consumos actuales
        consumptions = Consumption.query.filter_by(customer_id=customer_id).all()
        
        updates = []
        for consumption in consumptions:
            if consumption.type == 'data':
                # Simular uso de datos (0.1 - 0.5 GB)
                additional_usage = round(random.uniform(0.1, 0.5), 2)
                new_used = min(consumption.used + additional_usage, consumption.total)
                consumption.used = new_used
                consumption.percentage = round((new_used / consumption.total) * 100, 1)
                updates.append(f"Data: +{additional_usage}GB")
                
            elif consumption.type == 'minutes':
                # Simular uso de minutos (5 - 15 min)
                additional_minutes = random.randint(5, 15)
                new_used = min(consumption.used + additional_minutes, consumption.total)
                consumption.used = new_used
                consumption.percentage = round((new_used / consumption.total) * 100, 1)
                updates.append(f"Minutes: +{additional_minutes}min")
                
            elif consumption.type == 'sms':
                # Simular uso de SMS (1 - 3 SMS)
                additional_sms = random.randint(1, 3)
                new_used = min(consumption.used + additional_sms, consumption.total)
                consumption.used = new_used
                consumption.percentage = round((new_used / consumption.total) * 100, 1)
                updates.append(f"SMS: +{additional_sms}")

        db.session.commit()
        
        return jsonify({
            "message": "Usage simulated successfully",
            "updates": updates,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error simulating usage: {str(e)}"}), 500

@app.route('/api/customer/<string:customer_id>/reset-consumption', methods=['POST'])
def reset_consumption(customer_id):
    """Resetear el consumo del cliente (simular nuevo ciclo)"""
    try:
        consumptions = Consumption.query.filter_by(customer_id=customer_id).all()
        
        for consumption in consumptions:
            consumption.used = 0
            consumption.percentage = 0
            # Actualizar fecha de reset al próximo mes
            consumption.reset_date = datetime.now() + timedelta(days=30)

        db.session.commit()
        
        return jsonify({
            "message": "Consumption reset successfully",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error resetting consumption: {str(e)}"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de salud para verificar conectividad"""
    return jsonify({
        "status": "healthy",
        "service": "TelcoX Flask Backend",
        "timestamp": datetime.now().isoformat(),
        "database": "connected"
    })

# -----------------------
# CRUD Customers (con CORS habilitado)
# -----------------------
@app.route('/customers', methods=['GET', 'POST'])
def customer_list():
    if request.method == 'GET':
        customers = Customer.query.all()
        return jsonify([{
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "plan": c.plan,
            "status": c.status
        } for c in customers])

    if request.method == 'POST':
        data = request.get_json()
        customer = Customer(
            id=data['id'],
            name=data['name'],
            email=data.get('email'),
            phone=data.get('phone'),
            plan=data.get('plan'),
            status=data.get('status', 'active')
        )
        db.session.add(customer)
        db.session.commit()
        return jsonify({"message": "Customer created"}), 201

@app.route('/customers/<string:customer_id>', methods=['GET', 'PUT', 'DELETE'])
def customer_detail(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    if request.method == 'GET':
        return jsonify({
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "plan": customer.plan,
            "status": customer.status
        })

    if request.method == 'PUT':
        data = request.get_json()
        customer.name = data.get('name', customer.name)
        customer.email = data.get('email', customer.email)
        customer.phone = data.get('phone', customer.phone)
        customer.plan = data.get('plan', customer.plan)
        customer.status = data.get('status', customer.status)
        db.session.commit()
        return jsonify({"message": "Customer updated"})

    if request.method == 'DELETE':
        db.session.delete(customer)
        db.session.commit()
        return jsonify({"message": "Customer deleted"})

# -----------------------
# CRUD Consumption
# -----------------------
@app.route('/consumptions', methods=['GET', 'POST'])
def consumption_list():
    if request.method == 'GET':
        consumptions = Consumption.query.all()
        return jsonify([{
            "id": c.id,
            "customer_id": c.customer_id,
            "type": c.type,
            "used": float(c.used),
            "total": float(c.total),
            "unit": c.unit,
            "percentage": float(c.percentage) if c.percentage else None,
            "reset_date": str(c.reset_date)
        } for c in consumptions])

    if request.method == 'POST':
        data = request.get_json()
        c = Consumption(**data)
        db.session.add(c)
        db.session.commit()
        return jsonify({"message": "Consumption created"}), 201

@app.route('/consumptions/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def consumption_detail(id):
    c = Consumption.query.get(id)
    if not c:
        return jsonify({"error": "Consumption not found"}), 404

    if request.method == 'GET':
        return jsonify({
            "id": c.id,
            "customer_id": c.customer_id,
            "type": c.type,
            "used": float(c.used),
            "total": float(c.total),
            "unit": c.unit,
            "percentage": float(c.percentage) if c.percentage else None,
            "reset_date": str(c.reset_date)
        })

    if request.method == 'PUT':
        data = request.get_json()
        for field in ['customer_id', 'type', 'used', 'total', 'unit', 'percentage', 'reset_date']:
            if field in data:
                setattr(c, field, data[field])
        db.session.commit()
        return jsonify({"message": "Consumption updated"})

    if request.method == 'DELETE':
        db.session.delete(c)
        db.session.commit()
        return jsonify({"message": "Consumption deleted"})

# -----------------------
# CRUD Billing
# -----------------------
@app.route('/billings', methods=['GET', 'POST'])
def billing_list():
    if request.method == 'GET':
        billings = Billing.query.all()
        return jsonify([{
            "id": b.id,
            "customer_id": b.customer_id,
            "current_balance": float(b.current_balance) if b.current_balance else None,
            "currency": b.currency,
            "next_bill_date": str(b.next_bill_date),
            "monthly_fee": float(b.monthly_fee) if b.monthly_fee else None
        } for b in billings])

    if request.method == 'POST':
        data = request.get_json()
        b = Billing(**data)
        db.session.add(b)
        db.session.commit()
        return jsonify({"message": "Billing created"}), 201

@app.route('/billings/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def billing_detail(id):
    b = Billing.query.get(id)
    if not b:
        return jsonify({"error": "Billing not found"}), 404

    if request.method == 'GET':
        return jsonify({
            "id": b.id,
            "customer_id": b.customer_id,
            "current_balance": float(b.current_balance) if b.current_balance else None,
            "currency": b.currency,
            "next_bill_date": str(b.next_bill_date),
            "monthly_fee": float(b.monthly_fee) if b.monthly_fee else None
        })

    if request.method == 'PUT':
        data = request.get_json()
        for field in ['customer_id', 'current_balance', 'currency', 'next_bill_date', 'monthly_fee']:
            if field in data:
                setattr(b, field, data[field])
        db.session.commit()
        return jsonify({"message": "Billing updated"})

    if request.method == 'DELETE':
        db.session.delete(b)
        db.session.commit()
        return jsonify({"message": "Billing deleted"})

# -----------------------
# CRUD Billing Payments
# -----------------------
@app.route('/billing_payments', methods=['GET', 'POST'])
def payment_list():
    if request.method == 'GET':
        payments = BillingPayment.query.all()
        return jsonify([{
            "id": p.id,
            "billing_id": p.billing_id,
            "amount": float(p.amount),
            "payment_date": str(p.payment_date),
            "method": p.method
        } for p in payments])

    if request.method == 'POST':
        data = request.get_json()
        p = BillingPayment(**data)
        db.session.add(p)
        db.session.commit()
        return jsonify({"message": "Payment created"}), 201

@app.route('/billing_payments/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def payment_detail(id):
    p = BillingPayment.query.get(id)
    if not p:
        return jsonify({"error": "Payment not found"}), 404

    if request.method == 'GET':
        return jsonify({
            "id": p.id,
            "billing_id": p.billing_id,
            "amount": float(p.amount),
            "payment_date": str(p.payment_date),
            "method": p.method
        })

    if request.method == 'PUT':
        data = request.get_json()
        for field in ['billing_id', 'amount', 'payment_date', 'method']:
            if field in data:
                setattr(p, field, data[field])
        db.session.commit()
        return jsonify({"message": "Payment updated"})

    if request.method == 'DELETE':
        db.session.delete(p)
        db.session.commit()
        return jsonify({"message": "Payment deleted"})

# -----------------------
# CRUD Services
# -----------------------
@app.route('/services', methods=['GET', 'POST'])
def service_list():
    if request.method == 'GET':
        services = Service.query.all()
        return jsonify([{
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "status": s.status
        } for s in services])

    if request.method == 'POST':
        data = request.get_json()
        s = Service(**data)
        db.session.add(s)
        db.session.commit()
        return jsonify({"message": "Service created"}), 201

@app.route('/services/<string:id>', methods=['GET', 'PUT', 'DELETE'])
def service_detail(id):
    s = Service.query.get(id)
    if not s:
        return jsonify({"error": "Service not found"}), 404

    if request.method == 'GET':
        return jsonify({
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "status": s.status
        })

    if request.method == 'PUT':
        data = request.get_json()
        for field in ['name', 'description', 'status']:
            if field in data:
                setattr(s, field, data[field])
        db.session.commit()
        return jsonify({"message": "Service updated"})

    if request.method == 'DELETE':
        db.session.delete(s)
        db.session.commit()
        return jsonify({"message": "Service deleted"})

# -----------------------
# CRUD Customer Services
# -----------------------
@app.route('/customer_services', methods=['GET', 'POST'])
def customer_service_list():
    if request.method == 'GET':
        cs_list = CustomerService.query.all()
        return jsonify([{
            "customer_id": cs.customer_id,
            "service_id": cs.service_id
        } for cs in cs_list])

    if request.method == 'POST':
        data = request.get_json()
        cs = CustomerService(**data)
        db.session.add(cs)
        db.session.commit()
        return jsonify({"message": "Service assigned to customer"}), 201

@app.route('/customer_services/<string:customer_id>/<string:service_id>', methods=['DELETE'])
def customer_service_detail(customer_id, service_id):
    cs = CustomerService.query.get((customer_id, service_id))
    if not cs:
        return jsonify({"error": "CustomerService not found"}), 404
    db.session.delete(cs)
    db.session.commit()
    return jsonify({"message": "Service unassigned from customer"})

# -----------------------
# FUNCIÓN PARA SIMULAR ACTUALIZACIONES AUTOMÁTICAS
# -----------------------
def auto_update_consumption():
    """Función que se ejecuta en background para simular actualizaciones automáticas"""
    with app.app_context():
        while True:
            try:
                # Actualizar consumo cada 30 segundos para todos los clientes activos
                customers = Customer.query.filter_by(status='active').all()
                for customer in customers:
                    consumptions = Consumption.query.filter_by(customer_id=customer.id).all()
                    
                    for consumption in consumptions:
                        if consumption.used < consumption.total:
                            if consumption.type == 'data':
                                # Incremento pequeño en datos (0.01-0.05 GB)
                                increment = round(random.uniform(0.01, 0.05), 3)
                            elif consumption.type == 'minutes':
                                # Incremento en minutos (1-3 min)
                                increment = random.randint(1, 3)
                            elif consumption.type == 'sms':
                                # Incremento en SMS (0-1 SMS)
                                increment = random.randint(0, 1)
                            else:
                                increment = 0
                            
                            new_used = min(consumption.used + increment, consumption.total)
                            consumption.used = new_used
                            consumption.percentage = round((new_used / consumption.total) * 100, 1)
                
                db.session.commit()
                print(f"[{datetime.now()}] Auto-updated consumption data")
                
            except Exception as e:
                print(f"Error in auto-update: {e}")
                db.session.rollback()
            
            time.sleep(30)  # Actualizar cada 30 segundos

# -----------------------
# Run server
# -----------------------
if __name__ == '__main__':
    # Iniciar thread para actualizaciones automáticas
    update_thread = threading.Thread(target=auto_update_consumption, daemon=True)
    update_thread.start()
    
    print("🚀 TelcoX Flask Backend iniciado con actualizaciones en tiempo real")
    print("📊 Endpoints disponibles:")
    print("   - GET /api/customer/{id}/realtime - Datos en tiempo real")
    print("   - POST /api/customer/{id}/simulate-usage - Simular uso")
    print("   - POST /api/customer/{id}/reset-consumption - Reset consumo")
    print("   - GET /api/health - Estado del sistema")
    
    app.run(debug=True, port=5000, host='0.0.0.0')