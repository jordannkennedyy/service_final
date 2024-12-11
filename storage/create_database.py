import sqlite3
conn = sqlite3.connect('vessel_sqlite.db')


# create fuel reading table
c = conn.cursor()
c.execute('''
        CREATE TABLE fuel_consumption
          (id INTEGER PRIMARY KEY ASC,
          vessel_id VARCHAR(250) NOT NULL,
          device_id INTEGER NOT NULL,
          fuel_consumed INTEGER NOT NULL,
          timestamp VARCHAR(100) NOT NULL,
          date_created DATETIME NOT NULL,
          trace_id VARCHAR(250) NOT NULL)
        ''')


# create torque reading table
c.execute('''
        CREATE TABLE torque_reading
          (id INTEGER PRIMARY KEY ASC,
          vessel_id VARCHAR(250) NOT NULL,
          device_id INTEGER NOT NULL,
          torque INTEGER NOT NULL,
          timestamp VARCHAR(100) NOT NULL,
          date_created DATETIME NOT NULL,
          trace_id VARCHAR(250) NOT NULL)
          ''')

conn.commit()
conn.close()