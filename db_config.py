import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='klinikconnect',
            user='root',      
            password=''       
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error saat menghubungi MySQL: {e}")
        return None