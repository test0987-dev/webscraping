"""
Database connection handler for the Kenya news scraping project.
This module manages MySQL database connections and provides utility functions.
"""
import mysql.connector
from mysql.connector import Error
import logging
import sys
import os

# Add parent directory to sys.path to allow imports from sibling modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import settings from the config module
from config.settings import DB_SETTINGS

def get_connection():
    """
    Create and return a connection to the MySQL database using the settings from settings.py
    
    Returns:
        mysql.connector.connection.MySQLConnection: Database connection object if successful
        None: If connection fails
    """
    try:
        connection = mysql.connector.connect(**DB_SETTINGS)
        if connection.is_connected():
            return connection
    except Error as e:
        logging.error(f"Error connecting to MySQL database: {e}")
        return None

def test_connection():
    """
    Test the database connection and print the status.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        connection = get_connection()
        if connection and connection.is_connected():
            db_info = connection.get_server_info()
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            db_name = cursor.fetchone()[0]
            print(f"Connected to MySQL Server version {db_info}")
            print(f"Connected to database: {db_name}")
            print(f"Using credentials: {DB_SETTINGS['user']}@{DB_SETTINGS['host']}")
            cursor.close()
            connection.close()
            print("MySQL connection is closed")
            return True
        else:
            print("Failed to connect to the database")
            return False
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return False

if __name__ == "__main__":
    # Test the database connection when this file is run directly
    print("Testing database connection...")
    test_connection()