-- Create a test database for SQL RAG pipeline demonstration
-- Run this with: psql -U postgres -h localhost < setup_test_database.sql

-- Create test database
CREATE DATABASE chatbot_test
  WITH ENCODING 'UTF8'
  TEMPLATE template0;

-- Connect to the new database
\c chatbot_test

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10, 2),
    stock_quantity INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id),
    total_amount DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create order_items table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id),
    product_id INT NOT NULL REFERENCES products(id),
    quantity INT,
    unit_price DECIMAL(10, 2)
);

-- Insert sample users
INSERT INTO users (username, email) VALUES
('alice', 'alice@example.com'),
('bob', 'bob@example.com'),
('charlie', 'charlie@example.com'),
('diana', 'diana@example.com'),
('eve', 'eve@example.com');

-- Insert sample products
INSERT INTO products (name, category, price, stock_quantity) VALUES
('Laptop', 'Electronics', 999.99, 10),
('Mouse', 'Electronics', 29.99, 50),
('Keyboard', 'Electronics', 79.99, 25),
('Monitor', 'Electronics', 299.99, 15),
('Desk Chair', 'Furniture', 199.99, 20),
('Standing Desk', 'Furniture', 499.99, 8),
('Coffee Mug', 'Office Supplies', 9.99, 100),
('Notebook', 'Office Supplies', 4.99, 200);

-- Insert sample orders
INSERT INTO orders (user_id, total_amount, status) VALUES
(1, 1029.98, 'completed'),
(2, 299.99, 'completed'),
(3, 1549.96, 'pending'),
(1, 114.98, 'completed'),
(4, 499.99, 'shipped');

-- Insert sample order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 999.99),
(1, 2, 1, 29.99),
(2, 4, 1, 299.99),
(3, 1, 1, 999.99),
(3, 5, 1, 199.99),
(3, 6, 1, 349.98),
(4, 7, 10, 9.99),
(4, 8, 10, 4.99),
(5, 6, 1, 499.99);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_products_category ON products(category);

-- Display summary
SELECT 'Users created' as info, COUNT(*) as count FROM users
UNION ALL
SELECT 'Products created', COUNT(*) FROM products
UNION ALL
SELECT 'Orders created', COUNT(*) FROM orders
UNION ALL
SELECT 'Order items created', COUNT(*) FROM order_items;
