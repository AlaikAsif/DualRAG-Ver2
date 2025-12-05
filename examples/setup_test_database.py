"""
Setup test database for SQL RAG pipeline demonstration.

This script creates a sample PostgreSQL database with tables for testing.
Run this once before running test_sql_rag_with_real_db.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
import psycopg2.extras

def setup_test_database():
    """Create test database with sample data."""
    
    # Connection to postgres database (default)
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="postgres",
            user="postgres",
            password="123",
            connect_timeout=5
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        print("[1/8] Creating test database...")
        # Drop existing database if it exists
        cur.execute("DROP DATABASE IF EXISTS chatbot_test;")
        cur.execute("CREATE DATABASE chatbot_test;")
        print("      [OK] Database created")
        
        cur.close()
        conn.close()
        
        # Connect to the new test database
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="chatbot_test",
            user="postgres",
            password="123"
        )
        cur = conn.cursor()
        
        # Create tables
        print("[2/8] Creating users table...")
        cur.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) NOT NULL UNIQUE,
                email VARCHAR(100) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            );
        """)
        print("      [OK] Users table created")
        
        print("[3/8] Creating products table...")
        cur.execute("""
            CREATE TABLE products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                category VARCHAR(50),
                price DECIMAL(10, 2),
                stock_quantity INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("      [OK] Products table created")
        
        print("[4/8] Creating orders table...")
        cur.execute("""
            CREATE TABLE orders (
                id SERIAL PRIMARY KEY,
                user_id INT NOT NULL REFERENCES users(id),
                total_amount DECIMAL(10, 2),
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("      [OK] Orders table created")
        
        print("[5/8] Creating order_items table...")
        cur.execute("""
            CREATE TABLE order_items (
                id SERIAL PRIMARY KEY,
                order_id INT NOT NULL REFERENCES orders(id),
                product_id INT NOT NULL REFERENCES products(id),
                quantity INT,
                unit_price DECIMAL(10, 2)
            );
        """)
        print("      [OK] Order items table created")
        
        # Insert sample data
        print("[6/8] Inserting sample users...")
        users = [
            ('alice', 'alice@example.com'),
            ('bob', 'bob@example.com'),
            ('charlie', 'charlie@example.com'),
            ('diana', 'diana@example.com'),
            ('eve', 'eve@example.com'),
        ]
        for username, email in users:
            cur.execute(
                "INSERT INTO users (username, email) VALUES (%s, %s)",
                (username, email)
            )
        print(f"      [OK] {len(users)} users inserted")
        
        print("[7/8] Inserting sample products...")
        products = [
            ('Laptop', 'Electronics', 999.99, 10),
            ('Mouse', 'Electronics', 29.99, 50),
            ('Keyboard', 'Electronics', 79.99, 25),
            ('Monitor', 'Electronics', 299.99, 15),
            ('Desk Chair', 'Furniture', 199.99, 20),
            ('Standing Desk', 'Furniture', 499.99, 8),
            ('Coffee Mug', 'Office Supplies', 9.99, 100),
            ('Notebook', 'Office Supplies', 4.99, 200),
        ]
        for name, category, price, stock in products:
            cur.execute(
                "INSERT INTO products (name, category, price, stock_quantity) VALUES (%s, %s, %s, %s)",
                (name, category, price, stock)
            )
        print(f"      [OK] {len(products)} products inserted")
        
        print("[8/8] Creating indexes...")
        cur.execute("CREATE INDEX idx_users_email ON users(email);")
        cur.execute("CREATE INDEX idx_orders_user_id ON orders(user_id);")
        cur.execute("CREATE INDEX idx_order_items_order_id ON order_items(order_id);")
        cur.execute("CREATE INDEX idx_order_items_product_id ON order_items(product_id);")
        cur.execute("CREATE INDEX idx_products_category ON products(category);")
        print("      [OK] Indexes created")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("DATABASE SETUP COMPLETE!")
        print("=" * 60)
        print("\nDatabase: chatbot_test")
        print("Tables created: 4 (users, products, orders, order_items)")
        print("Sample data: 5 users, 8 products, indexes on key columns")
        print("\nYou can now run: python examples/test_sql_rag_with_real_db.py\n")
        
    except psycopg2.Error as e:
        print(f"\n[ERROR] Database setup failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure PostgreSQL is running on localhost:5432")
        print("  2. Verify postgres user exists and password is '123'")
        print("  3. Check the password in DATABASE_CONFIG if different\n")
        sys.exit(1)

if __name__ == "__main__":
    setup_test_database()
