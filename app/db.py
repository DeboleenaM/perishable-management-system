import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",        # 🔁 Replace with your MySQL username
            password="deboleena",# 🔁 Replace with your MySQL password
            database="retail_store_v2"        # ✅ Ensure this database exists
        )
        return connection
    except Error as e:
        print("Error connecting to MySQL:", e)
        return None

