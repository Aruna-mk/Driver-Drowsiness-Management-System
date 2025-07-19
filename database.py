import mysql.connector
from tkinter import messagebox

class DatabaseManager:
    @staticmethod
    def get_connection():
        try:
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="drowsiness_db"
            )
            return connection
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Error connecting to database: {e}")
            return None

    @staticmethod
    def create_database():
        try:
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password=""
            )
            cursor = connection.cursor()

            # Create database and tables
            cursor.execute("CREATE DATABASE IF NOT EXISTS drowsiness_db")
            cursor.execute("USE drowsiness_db")

            # Create drivers table
            cursor.execute('''CREATE TABLE IF NOT EXISTS drivers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                age INT,
                gender VARCHAR(10),
                license_no VARCHAR(50),
                place VARCHAR(100),
                phone VARCHAR(20),
                username VARCHAR(50) UNIQUE,
                password VARCHAR(100)
            )''')

            # Create journeys table
            cursor.execute('''CREATE TABLE IF NOT EXISTS journeys (
                id INT AUTO_INCREMENT PRIMARY KEY,
                driver_id INT,
                start_time DATETIME,
                end_time DATETIME,
                drowsiness_count INT,
                journey_status VARCHAR(50),
                FOREIGN KEY (driver_id) REFERENCES drivers(id)
            )''')

            # Add admin table
            cursor.execute('''CREATE TABLE IF NOT EXISTS admins (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE,
                password VARCHAR(100)
            )''')

            # Insert default admin
            cursor.execute("SELECT * FROM admins WHERE username = 'admin'")
            if not cursor.fetchone():
                cursor.execute("INSERT INTO admins (username, password) VALUES ('admin', 'admin123')")

            connection.commit()
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Error creating database: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()