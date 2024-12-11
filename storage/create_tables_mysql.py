import mysql.connector

db_conn = mysql.connector.connect(
    host="acit3855-lab06.eastus2.cloudapp.azure.com",
    user="root",
    password="password",
    database="vessel"
)


# create fuel reading table
c = db_conn.cursor()
c.execute('''
        CREATE TABLE fuel_consumption
          (id INT NOT NULL AUTO_INCREMENT,
          vessel_id VARCHAR(250) NOT NULL,
          device_id INTEGER NOT NULL,
          fuel_consumed INTEGER NOT NULL,
          timestamp VARCHAR(100) NOT NULL,
          date_created DATETIME NOT NULL,
          trace_id VARCHAR(250) NOT NULL,
          CONSTRAINT fuel_pk PRIMARY KEY (id))
        ''')


# create torque reading table
c.execute('''
        CREATE TABLE torque_reading
          (id INT NOT NULL AUTO_INCREMENT,
          vessel_id VARCHAR(250) NOT NULL,
          device_id INTEGER NOT NULL,
          torque INTEGER NOT NULL,
          timestamp VARCHAR(100) NOT NULL,
          date_created DATETIME NOT NULL,
          trace_id VARCHAR(250) NOT NULL,
          CONSTRAINT torque_pk PRIMARY KEY (id))
          ''')

db_conn.commit()
db_conn.close()