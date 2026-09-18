import mysql.connector

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="marketplace_db"
    )

    return connection

if __name__ == "__main__":
    connection = get_connection()

    if connection.is_connected():
        print("Anda telah berhasil terhubung ke MySQL!")

    connection.close()