import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import datetime
import cv2
import threading
import numpy as np
from keras.models import load_model
from keras.preprocessing.image import img_to_array
from playsound import playsound
import os
from modules.database import DatabaseManager
from modules.drowsiness_detector import DrowsinessDetector
from modules.gui_styles import GUIStyles

class DriverDrowsinessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Driver Drowsiness Management System")
        
        # Get screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window size to screen size and position it at (0,0)
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Configure window to be resizable
        self.root.resizable(True, True)
        
        # Set window state to zoomed (maximized)
        self.root.state('zoomed')
        
        # Set root background color
        self.root.configure(bg='#E8F0FE')  # Light blue-gray background
        
        # Define font styles and UI component configurations
        self.header_font = ('Helvetica', 24, 'bold')
        self.label_font = ('Helvetica', 14)
        self.entry_style = {
            'font': ('Helvetica', 12),
            'width': 30,
            'bg': 'white'
        }
        self.button_style = {
            'font': ('Helvetica', 12, 'bold'),
            'width': 20,
            'height': 2,
            'cursor': 'hand2'
        }
        
        # Configure Treeview style
        style = ttk.Style()
        style.configure('Treeview', font=('Helvetica', 12), rowheight=30)
        style.configure('Treeview.Heading', font=('Helvetica', 12, 'bold'))
        
        # Create main frames with background colors
        self.login_frame = tk.Frame(root, bg='#F0F7FF')  # Light blue
        self.register_frame = tk.Frame(root, bg='#E6F3FF')  # Lighter blue
        self.main_frame = tk.Frame(root, bg='#F5F9FF')  # Very light blue
        self.admin_login_frame = tk.Frame(root, bg='#EFF6FF')  # Another light blue shade
        self.admin_frame = tk.Frame(root, bg='#F8FAFF')  # Lightest blue
        
        # Setup all frames
        self.setup_login_frame()
        self.setup_register_frame()
        self.setup_main_frame()
        self.setup_admin_login_frame()
        self.setup_admin_frame()
        
        # Show login frame initially
        self.show_login_frame()
    
    def _setup_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.resizable(True, True)
        self.root.state('zoomed')
        self.root.configure(bg=self.styles.COLORS['bg_main'])

    def get_db_connection(self):
        try:
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",  # Default XAMPP password
                database="drowsiness_db"
            )
            return connection
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Error connecting to database: {e}")
            return None
    
    def create_database(self):
        try:
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password=""
            )
            cursor = connection.cursor()

            # Create database
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

            # Insert default admin if not exists
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

    def setup_login_frame(self):
        tk.Label(self.login_frame, text="New Driver must Register to Login", 
                font=self.header_font,
                bg='#F0F7FF').pack(pady=30)
        
        tk.Label(self.login_frame, text="Driver Login", 
                font=self.header_font,
                bg='#F0F7FF').pack(pady=30)
        
        tk.Label(self.login_frame, text="Username:",
                font=self.label_font,
                bg='#F0F7FF').pack(pady=5)
        self.username_entry = tk.Entry(self.login_frame, **self.entry_style)
        self.username_entry.pack(pady=10)
        
        tk.Label(self.login_frame, text="Password:",
                font=self.label_font,
                bg='#F0F7FF').pack(pady=5)
        self.password_entry = tk.Entry(self.login_frame,
                                     show="*",
                                     **self.entry_style)
        self.password_entry.pack(pady=10)
        
        tk.Button(self.login_frame, text="Login",
                 command=self.login,
                 bg='#2E86C1', fg='white').pack(pady=10)
        tk.Button(self.login_frame, text="Register",
                 command=self.show_register_frame,
                 bg='#2E86C1', fg='white').pack(pady=5)
        tk.Button(self.login_frame, text="Admin Login",
                 command=self.show_admin_login_frame,
                 bg='#2E86C1', fg='white').pack(pady=5)

    def setup_register_frame(self):
        tk.Label(self.register_frame, text="Driver Registration", 
                font=self.header_font,
                bg='#E6F3FF').pack(pady=30)
        
        fields = ['Name', 'Age', 'Gender', 'License No', 'Place', 'Phone No', 'Username', 'Password']
        self.register_entries = {}
        
        for field in fields:
            tk.Label(self.register_frame, text=field+":",
                    font=self.label_font,
                    bg='#E6F3FF').pack(pady=5)
            if field == 'Gender':
                self.register_entries[field] = ttk.Combobox(self.register_frame,
                                                          values=['Male', 'Female', 'Other'],
                                                          font=('Helvetica', 12),
                                                          width=28)
            elif field == 'Password':
                self.register_entries[field] = tk.Entry(self.register_frame,
                                                      show="*",
                                                      **self.entry_style)
            else:
                self.register_entries[field] = tk.Entry(self.register_frame,
                                                      **self.entry_style)
            self.register_entries[field].pack(pady=5)
        
        tk.Button(self.register_frame, text="Register", 
                 command=self.register,
                 bg='#2E86C1', fg='white',
                 activebackground='#1A5276',
                 activeforeground='white').pack(pady=10)
        tk.Button(self.register_frame, text="Back to Login", 
                 command=self.show_login_frame,
                 bg='#2E86C1', fg='white',
                 activebackground='#1A5276',
                 activeforeground='white').pack()

    def setup_main_frame(self):
        """Setup the main frame with driver dashboard"""
        tk.Label(self.main_frame, text="Driver Dashboard", 
                font=self.header_font,
                bg='#F5F9FF').pack(pady=30)
        
        # Create buttons for driver actions
        self.start_button = tk.Button(self.main_frame, text="Start Journey",
                                    command=self.start_journey,
                                    bg='#27AE60', fg='white',
                                    font=('Helvetica', 12, 'bold'),
                                    width=25, height=2)
        self.start_button.pack(pady=20)
        
        self.end_button = tk.Button(self.main_frame, text="End Journey",
                                  command=self.end_journey,
                                  state='disabled',
                                  bg='#E74C3C', fg='white',
                                  font=('Helvetica', 12, 'bold'),
                                  width=25, height=2)
        self.end_button.pack(pady=20)
        
        tk.Button(self.main_frame, text="Generate Report",
                 command=self.generate_report,
                 bg='#3498DB', fg='white',
                 font=('Helvetica', 12, 'bold'),
                 width=25, height=2).pack(pady=20)
        
        tk.Button(self.main_frame, text="Logout",
                 command=self.logout,
                 bg='#95A5A6', fg='white',
                 font=('Helvetica', 12, 'bold'),
                 width=25, height=2).pack(pady=20)

    def show_main_frame(self):
        """Show main frame and hide others"""
        self.login_frame.pack_forget()
        self.register_frame.pack_forget()
        self.admin_login_frame.pack_forget()
        self.admin_frame.pack_forget()
        self.main_frame.pack(expand=True, fill='both', padx=20, pady=20)

    def setup_admin_login_frame(self):
        tk.Label(self.admin_login_frame, text="Admin Login", 
                font=('Helvetica', 24, 'bold'),  # Increased font size
                bg='#EFF6FF').pack(pady=30)  # Increased padding
        
        tk.Label(self.admin_login_frame, text="Username:",
                font=('Helvetica', 14),  # Added font size
                bg='#EFF6FF').pack(pady=10)
        self.admin_username_entry = tk.Entry(self.admin_login_frame,
                                           font=('Helvetica', 12),  # Added font size
                                           width=30,  # Increased width
                                           bg='white')
        self.admin_username_entry.pack(pady=10)
        
        tk.Label(self.admin_login_frame, text="Password:",
                font=('Helvetica', 14),  # Added font size
                bg='#EFF6FF').pack(pady=10)
        self.admin_password_entry = tk.Entry(self.admin_login_frame,
                                           font=('Helvetica', 12),  # Added font size
                                           width=30,  # Increased width
                                           show="*",
                                           bg='white')
        self.admin_password_entry.pack(pady=10)
        
        # Increased button sizes
        tk.Button(self.admin_login_frame, text="Login",
                 command=self.admin_login,
                 font=('Helvetica', 12, 'bold'),  # Added font size
                 width=20,  # Increased width
                 height=2,  # Increased height
                 bg='#2E86C1', fg='white',
                 activebackground='#1A5276',
                 activeforeground='white').pack(pady=20)
        tk.Button(self.admin_login_frame, text="Back",
                 command=self.show_login_frame,
                 font=('Helvetica', 12, 'bold'),  # Added font size
                 width=20,  # Increased width
                 height=2,  # Increased height
                 bg='#95A5A6', fg='white',
                 activebackground='#7F8C8D',
                 activeforeground='white').pack(pady=10)

    def setup_admin_frame(self):
        tk.Label(self.admin_frame, text="Admin Dashboard", 
                font=('Helvetica', 24, 'bold'),  # Increased font size
                bg='#F8FAFF').pack(pady=30)  # Increased padding
        
        # View Database button with increased size
        tk.Button(self.admin_frame, text="View Database",
                 command=self.view_database,
                 font=('Helvetica', 12, 'bold'),  # Added font size
                 width=25,  # Increased width
                 height=2,  # Added height
                 bg='#3498DB', fg='white',
                 activebackground='#2874A6',
                 activeforeground='white').pack(pady=20)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.admin_frame)
        notebook.pack(pady=20, expand=True, fill="both", padx=20)  # Added padding
        
        # Drivers tab
        drivers_frame = ttk.Frame(notebook)
        notebook.add(drivers_frame, text="Drivers")
        
        self.drivers_tree = ttk.Treeview(drivers_frame, columns=('ID', 'Name', 'Age', 'Gender', 'License', 'Place', 'Phone', 'Username'), show='headings')
        for col in self.drivers_tree['columns']:
            self.drivers_tree.heading(col, text=col)
            self.drivers_tree.column(col, width=100)
        
        # Add Delete button for drivers
        tk.Button(drivers_frame, text="Delete Selected Driver",
                 command=self.delete_driver,
                 bg='#E74C3C', fg='white',
                 activebackground='#B03A2E',
                 activeforeground='white').pack(pady=5)
        self.drivers_tree.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Journeys tab
        journeys_frame = ttk.Frame(notebook)
        notebook.add(journeys_frame, text="Journeys")
        
        self.journeys_tree = ttk.Treeview(journeys_frame, columns=('ID', 'Driver ID', 'Start Time', 'End Time', 'Drowsiness', 'Status'), show='headings')
        for col in self.journeys_tree['columns']:
            self.journeys_tree.heading(col, text=col)
            self.journeys_tree.column(col, width=130)
        
        # Add Delete button for journeys
        tk.Button(journeys_frame, text="Delete Selected Journey",
                 command=self.delete_journey,
                 bg='#E74C3C', fg='white',
                 activebackground='#B03A2E',
                 activeforeground='white').pack(pady=5)
        self.journeys_tree.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Refresh and Logout buttons with increased size
        tk.Button(self.admin_frame, text="Refresh Data",
                 command=self.refresh_admin_data,
                 font=('Helvetica', 12, 'bold'),  # Added font size
                 width=25,  # Increased width
                 height=2,  # Added height
                 bg='#27AE60', fg='white',
                 activebackground='#196F3D',
                 activeforeground='white').pack(pady=20)
        tk.Button(self.admin_frame, text="Logout",
                 command=self.admin_logout,
                 font=('Helvetica', 12, 'bold'),  # Added font size
                 width=25,  # Increased width
                 height=2,  # Added height
                 bg='#95A5A6', fg='white',
                 activebackground='#7F8C8D',
                 activeforeground='white').pack(pady=20)

    def refresh_admin_data(self):
        # Clear existing items
        for item in self.drivers_tree.get_children():
            self.drivers_tree.delete(item)
        for item in self.journeys_tree.get_children():
            self.journeys_tree.delete(item)
        
        connection = self.get_db_connection()
        if connection:
            cursor = connection.cursor()
            
            # Refresh drivers
            cursor.execute("SELECT id, name, age, gender, license_no, place, phone, username FROM drivers")
            for row in cursor.fetchall():
                self.drivers_tree.insert('', 'end', values=row)
            
            # Refresh journeys
            cursor.execute("""
                SELECT j.id, j.driver_id, j.start_time, j.end_time, j.drowsiness_count, j.journey_status 
                FROM journeys j
                ORDER BY j.start_time DESC
            """)
            for row in cursor.fetchall():
                self.journeys_tree.insert('', 'end', values=row)
            
            cursor.close()
            connection.close()

    def delete_driver(self):
        selected_item = self.drivers_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a driver to delete")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this driver and all their journeys?"):
            driver_id = self.drivers_tree.item(selected_item)['values'][0]
            
            connection = self.get_db_connection()
            if connection:
                cursor = connection.cursor()
                try:
                    # Delete related journeys first
                    cursor.execute("DELETE FROM journeys WHERE driver_id = %s", (driver_id,))
                    # Then delete the driver
                    cursor.execute("DELETE FROM drivers WHERE id = %s", (driver_id,))
                    connection.commit()
                    messagebox.showinfo("Success", "Driver and related journeys deleted successfully")
                    self.refresh_admin_data()
                except mysql.connector.Error as e:
                    messagebox.showerror("Error", f"Failed to delete driver: {str(e)}")
                finally:
                    cursor.close()
                    connection.close()

    def delete_journey(self):
        selected_item = self.journeys_tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a journey to delete")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this journey?"):
            journey_id = self.journeys_tree.item(selected_item)['values'][0]
            
            connection = self.get_db_connection()
            if connection:
                cursor = connection.cursor()
                try:
                    cursor.execute("DELETE FROM journeys WHERE id = %s", (journey_id,))
                    connection.commit()
                    messagebox.showinfo("Success", "Journey deleted successfully")
                    self.refresh_admin_data()
                except mysql.connector.Error as e:
                    messagebox.showerror("Error", f"Failed to delete journey: {str(e)}")
                finally:
                    cursor.close()
                    connection.close()

    def admin_logout(self):
        """Handle admin logout"""
        self.current_admin = None
        self.admin_username_entry.delete(0, 'end')
        self.admin_password_entry.delete(0, 'end')
        self.show_login_frame()

    def show_login_frame(self):
        """Show login frame and hide others"""
        self.register_frame.pack_forget()
        self.main_frame.pack_forget()
        self.admin_login_frame.pack_forget()
        self.admin_frame.pack_forget()
        self.login_frame.pack()

    def show_admin_login_frame(self):
        """Show admin login frame and hide others"""
        self.login_frame.pack_forget()
        self.register_frame.pack_forget()
        self.main_frame.pack_forget()
        self.admin_frame.pack_forget()
        self.admin_login_frame.pack()

    def show_admin_frame(self):
        """Show admin frame and hide others"""
        self.login_frame.pack_forget()
        self.register_frame.pack_forget()
        self.main_frame.pack_forget()
        self.admin_login_frame.pack_forget()
        self.admin_frame.pack()

    def show_register_frame(self):
        """Show register frame and hide others"""
        self.login_frame.pack_forget()
        self.main_frame.pack_forget()
        self.admin_login_frame.pack_forget()
        self.admin_frame.pack_forget()
        self.register_frame.pack()

    def register(self):
        """Handle driver registration"""
        # Get all field values
        values = {field: entry.get() for field, entry in self.register_entries.items()}
        
        # Validate all fields are filled
        if not all(values.values()):
            messagebox.showerror("Error", "All fields must be filled")
            return
        
        # Validate age is a number
        try:
            age = int(values['Age'])
            if age < 18:
                messagebox.showerror("Error", "Driver must be at least 18 years old")
                return
        except ValueError:
            messagebox.showerror("Error", "Age must be a number")
            return
        
        # Validate phone number
        if not values['Phone No'].isdigit() or len(values['Phone No']) < 10:
            messagebox.showerror("Error", "Please enter a valid phone number")
            return
        
        connection = self.get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                # Check if username already exists
                cursor.execute("SELECT * FROM drivers WHERE username = %s", (values['Username'],))
                if cursor.fetchone():
                    messagebox.showerror("Error", "Username already exists")
                    return
                
                # Insert new driver
                cursor.execute("""
                    INSERT INTO drivers (name, age, gender, license_no, place, phone, username, password)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    values['Name'],
                    age,
                    values['Gender'],
                    values['License No'],
                    values['Place'],
                    values['Phone No'],
                    values['Username'],
                    values['Password']
                ))
                connection.commit()
                
                messagebox.showinfo("Success", "Registration successful! You can now login.")
                # Clear all entries
                for entry in self.register_entries.values():
                    entry.delete(0, 'end')
                self.show_login_frame()
                
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", f"Error during registration: {str(e)}")
            finally:
                cursor.close()
                connection.close()

    def login(self):
        """Handle driver login"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        connection = self.get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT * FROM drivers WHERE username=%s AND password=%s", 
                             (username, password))
                driver = cursor.fetchone()
                
                if driver:
                    self.current_driver = driver
                    messagebox.showinfo("Success", f"Welcome {driver[1]}!")  # driver[1] is the name
                    self.username_entry.delete(0, 'end')
                    self.password_entry.delete(0, 'end')
                    self.show_main_frame()
                else:
                    messagebox.showerror("Error", "Invalid username or password")
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", f"Error during login: {str(e)}")
            finally:
                cursor.close()
                connection.close()

    def start_journey(self):
        """Start a new journey for the current driver"""
        if not hasattr(self, 'current_driver'):
            messagebox.showerror("Error", "No driver logged in")
            return
        
        try:
            model_path = os.path.join(os.path.dirname(__file__), 'drowsiness_model.h5')
            if not os.path.exists(model_path):
                messagebox.showerror("Error", "Model file not found")
                return
                
            self.detector = DrowsinessDetector(model_path)
            self.drowsiness_count = 0
            self.journey_active = True
            
            # Create journey record in database
            connection = self.get_db_connection()
            if connection:
                cursor = connection.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO journeys (driver_id, start_time, drowsiness_count, journey_status)
                        VALUES (%s, %s, %s, %s)
                    """, (self.current_driver[0], datetime.now(), 0, 'Active'))
                    connection.commit()
                    self.current_journey_id = cursor.lastrowid
                    
                    # Update UI
                    self.start_button.config(state='disabled')
                    self.end_button.config(state='normal')
                    
                    # Start detection in a separate thread
                    self.detection_thread = threading.Thread(
                        target=self.detector.run_detection,
                        args=(lambda: self.journey_active, self.update_drowsiness_count)
                    )
                    self.detection_thread.start()
                    
                except mysql.connector.Error as e:
                    messagebox.showerror("Database Error", f"Error starting journey: {str(e)}")
                finally:
                    cursor.close()
                    connection.close()
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start journey: {str(e)}")

    def update_drowsiness_count(self):
        """Update drowsiness count in database"""
        self.drowsiness_count += 1
        connection = self.get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                    UPDATE journeys 
                    SET drowsiness_count = %s 
                    WHERE id = %s
                """, (self.drowsiness_count, self.current_journey_id))
                connection.commit()
            except mysql.connector.Error as e:
                print(f"Error updating drowsiness count: {str(e)}")
            finally:
                cursor.close()
                connection.close()

    def end_journey(self):
        """End the current journey"""
        if messagebox.askyesno("Confirm", "Are you sure you want to end this journey?"):
            self.journey_active = False
            if hasattr(self, 'detection_thread'):
                self.detection_thread.join()
            
            connection = self.get_db_connection()
            if connection:
                cursor = connection.cursor()
                try:
                    cursor.execute("""
                        UPDATE journeys 
                        SET end_time = %s, journey_status = 'Completed' 
                        WHERE id = %s
                    """, (datetime.now(), self.current_journey_id))
                    connection.commit()
                    
                    # Update UI
                    self.start_button.config(state='normal')
                    self.end_button.config(state='disabled')
                    messagebox.showinfo("Success", "Journey ended successfully")
                    
                except mysql.connector.Error as e:
                    messagebox.showerror("Database Error", f"Error ending journey: {str(e)}")
                finally:
                    cursor.close()
                    connection.close()

    def generate_report(self):
        """Generate report for the current driver"""
        if not hasattr(self, 'current_driver'):
            messagebox.showerror("Error", "No driver logged in")
            return
            
        connection = self.get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                    SELECT start_time, end_time, drowsiness_count, journey_status 
                    FROM journeys 
                    WHERE driver_id = %s 
                    ORDER BY start_time DESC
                """, (self.current_driver[0],))
                journeys = cursor.fetchall()
                
                if not journeys:
                    messagebox.showinfo("Report", "No journeys found for this driver")
                    return
                
                report = f"Driver: {self.current_driver[1]}\n\nJourney History:\n"
                for journey in journeys:
                    report += f"\nStart: {journey[0]}"
                    report += f"\nEnd: {journey[1] if journey[1] else 'Ongoing'}"
                    report += f"\nDrowsiness Events: {journey[2]}"
                    report += f"\nStatus: {journey[3]}\n"
                
                messagebox.showinfo("Journey Report", report)
                
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", f"Error generating report: {str(e)}")
            finally:
                cursor.close()
                connection.close()

    def logout(self):
        """Handle driver logout"""
        if hasattr(self, 'journey_active') and self.journey_active:
            messagebox.showerror("Error", "Please end your journey before logging out")
            return
            
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?"):
            self.current_driver = None
            self.show_login_frame()

    def admin_login(self):
        """Handle admin login"""
        username = self.admin_username_entry.get()
        password = self.admin_password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        connection = self.get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT * FROM admins WHERE username=%s AND password=%s", 
                             (username, password))
                admin = cursor.fetchone()
                
                if admin:
                    self.current_admin = admin
                    messagebox.showinfo("Success", "Welcome Admin!")
                    self.admin_username_entry.delete(0, 'end')
                    self.admin_password_entry.delete(0, 'end')
                    self.show_admin_frame()
                    self.refresh_admin_data()  # Load initial data
                else:
                    messagebox.showerror("Error", "Invalid admin credentials")
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", f"Error during admin login: {str(e)}")
            finally:
                cursor.close()
                connection.close()

    def view_database(self):
        """View and manage database records"""
        # Refresh data first
        self.refresh_admin_data()
        
        # Create a new window for database view
        db_window = tk.Toplevel(self.root)
        db_window.title("Database Records")
        db_window.geometry("1200x800")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(db_window)
        notebook.pack(pady=20, expand=True, fill="both", padx=20)
        
        # Drivers Statistics
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Statistics")
        
        connection = self.get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                # Get total drivers
                cursor.execute("SELECT COUNT(*) FROM drivers")
                total_drivers = cursor.fetchone()[0]
                
                # Get total journeys
                cursor.execute("SELECT COUNT(*) FROM journeys")
                total_journeys = cursor.fetchone()[0]
                
                # Get total drowsiness events
                cursor.execute("SELECT SUM(drowsiness_count) FROM journeys")
                total_drowsiness = cursor.fetchone()[0] or 0
                
                # Get active journeys
                cursor.execute("SELECT COUNT(*) FROM journeys WHERE journey_status = 'Active'")
                active_journeys = cursor.fetchone()[0]
                
                # Display statistics
                stats_text = f"""
                Database Statistics:
                
                Total Drivers: {total_drivers}
                Total Journeys: {total_journeys}
                Total Drowsiness Events: {total_drowsiness}
                Currently Active Journeys: {active_journeys}
                """
                
                stats_label = tk.Label(stats_frame, 
                                     text=stats_text,
                                     font=('Helvetica', 14),
                                     justify=tk.LEFT,
                                     padx=20,
                                     pady=20)
                stats_label.pack(expand=True)
                
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", f"Error fetching statistics: {str(e)}")
            finally:
                cursor.close()
                connection.close()