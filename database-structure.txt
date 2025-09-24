CREATE DATABASE telcox;
USE telcox;
CREATE TABLE customers (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    plan VARCHAR(50),
    status ENUM('active','inactive') DEFAULT 'active'
);

INSERT INTO customers VALUES
('CUST001', 'Juan Pérez García', 'juan.perez@email.com', '+34 612 345 678', 'Plan Premium', 'active');
CREATE TABLE consumption (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(20),
    type ENUM('data','minutes','sms') NOT NULL,
    used DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    unit VARCHAR(10) NOT NULL,
    percentage DECIMAL(5,2),
    reset_date DATE,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

INSERT INTO consumption (customer_id,type,used,total,unit,percentage,reset_date) VALUES
('CUST001','data',8.5,20,'GB',42.5,'2025-02-15'),
('CUST001','minutes',245,500,'min',49,'2025-02-15'),
('CUST001','sms',28,100,'SMS',28,'2025-02-15');
CREATE TABLE billing (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id VARCHAR(20),
    current_balance DECIMAL(10,2),
    currency VARCHAR(10),
    next_bill_date DATE,
    monthly_fee DECIMAL(10,2),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

INSERT INTO billing (customer_id,current_balance,currency,next_bill_date,monthly_fee) VALUES
('CUST001',45.5,'EUR','2025-02-15',39.99);
CREATE TABLE billing_payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    billing_id INT,
    amount DECIMAL(10,2),
    payment_date DATE,
    method VARCHAR(50),
    FOREIGN KEY (billing_id) REFERENCES billing(id)
);

INSERT INTO billing_payments (billing_id,amount,payment_date,method) VALUES
(1,39.99,'2025-01-15','Tarjeta de Crédito');
CREATE TABLE services (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(255),
    status ENUM('active','inactive') DEFAULT 'active'
);

CREATE TABLE customer_services (
    customer_id VARCHAR(20),
    service_id VARCHAR(20),
    PRIMARY KEY (customer_id, service_id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

INSERT INTO services VALUES
('1','Datos Móviles','20GB de datos de alta velocidad','active'),
('2','Llamadas Nacionales','500 minutos incluidos','active'),
('3','SMS','100 SMS incluidos','active'),
('4','Roaming Internacional','Servicio de roaming desactivado','inactive');

INSERT INTO customer_services VALUES
('CUST001','1'),
('CUST001','2'),
('CUST001','3');
