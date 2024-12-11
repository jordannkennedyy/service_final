import mysql.connector


db_conn = mysql.connector.connect(
    host="acit3855-lab06.eastus2.cloudapp.azure.com",
    user="root",
    password="password",
    database="vessel"
)

db_cursor = db_conn.cursor()

db_cursor.execute(
    '''DROP TABLE fuel_consumption, torque_reading'''
)

db_conn.commit()
db_conn.close()