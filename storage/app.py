"""storage service"""

import logging
import logging.config
import datetime
import json
from threading import Thread
import os
from pykafka import KafkaClient
from pykafka.common import OffsetType
import yaml
from torque import TorqueReading
from fuel_consumption import FuelConsumption
from base import Base
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
import connexion

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    APP_CONFIG_FILE = "/config/app_config.yaml"
    LOG_CONFIG_FILE = "/config/log_conf.yaml"
else:
    print("In Dev Environment")
    APP_CONFIG_FILE = "app_config.yaml"
    LOG_CONFIG_FILE = "log_conf.yaml"

with open (APP_CONFIG_FILE, 'r', encoding='utf-8') as config_file:
    app_config = yaml.safe_load(config_file.read())

with open(LOG_CONFIG_FILE, 'r', encoding='utf-8') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s", APP_CONFIG_FILE)
logger.info("Log Conf File: %s", LOG_CONFIG_FILE)

try:
    DB_ENGINE = create_engine(f'mysql+pymysql://{app_config["datastore"]["user"]}:{app_config["datastore"]["password"]}@{app_config["datastore"]["hostname"]}:{app_config["datastore"]["port"]}/{app_config["datastore"]["db"]}',
                              pool_pre_ping=True, pool_size=10, pool_recycle=1800)
    Base.metadata.bind = DB_ENGINE
    DB_SESSION = sessionmaker(bind=DB_ENGINE)
    logger.info(f"Connecting to Db. Hostname: {app_config['datastore']['hostname']}, Port: {app_config['datastore']['port']}")
except Exception as e:
    logger.error(f"Could not connect to {app_config['datastore']['hostname']} on Port:{app_config['datastore']['port']}")

def get_processing_stats():
    """get processing stats"""
    pass


def get_fuel_consumption(start_timestamp, end_timestamp):
    """Gets new fuel consumption reading between the start and end timestamps"""

    session = DB_SESSION()

    start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ")

    results = session.query(FuelConsumption).filter(and_(FuelConsumption.date_created >= start_timestamp_datetime,
                                                         FuelConsumption.date_created < end_timestamp_datetime)).all()
    result_list = []

    for item in results:
        result_list.append(item.to_dict())

    session.close()

    logger.info("Query for fuel consumption readings after %s returns %d results" %(start_timestamp, len(result_list)))

    if not result_list:
        return [], 404
    else:
        return result_list, 200




def get_torque(start_timestamp, end_timestamp):
    """Gets new torque reading between the start and end timestamps"""

    session = DB_SESSION()

    start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ")

    results = session.query(TorqueReading).filter(and_(TorqueReading.date_created >= start_timestamp_datetime,
                                                         TorqueReading.date_created < end_timestamp_datetime)).all()
    result_list = []
    for item in results:
        result_list.append(item.to_dict())

    session.close()

    logger.info("Query for torque readings after %s returns %d results" %
                (start_timestamp, len(result_list)))

    if not result_list:
        return [], 404
    else:
        return result_list, 200


def process_messages():
    """ Process event messages """
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    # Create a consume on a consumer group, that only reads new messages
    # (uncommitted messages) when the service re-starts (i.e., it doesn't
    # read all the old messages from the history in the message queue).

    consumer = topic.get_simple_consumer(consumer_group=b'event_group',
        reset_offset_on_start=False,
        auto_offset_reset=OffsetType.LATEST)

    # This is blocking - it will wait for a new message
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s", msg)
        payload = msg["payload"]
        if msg["type"] == "fuel":
            session = DB_SESSION()

            fuel = FuelConsumption(payload['vessel_id'],
                                payload['device_id'],
                                payload['fuel_consumed'],
                                payload['timestamp'],
                                payload['trace_id'])

            session.add(fuel)
            session.commit()
            session.close()
            logger.debug("stored event: post_fuel_consumption, UUID: %s", payload['trace_id'])

        # Store the event1 (i.e., the payload) to the DB
        elif msg["type"] == "torque":
            session = DB_SESSION()
            torque = TorqueReading(payload['vessel_id'],
                                payload['device_id'],
                                payload['torque'],
                                payload['timestamp'],
                                payload['trace_id'])

            session.add(torque)

            session.commit()
            session.close()
            logger.debug("stored event: post_torque, UUID: %s", payload['trace_id'])

        consumer.commit_offsets()


def get_event_stats():
    "get number of torque and fuel events"

    session = DB_SESSION()

    num_torque = session.query(TorqueReading).count()
    num_fuel = session.query(FuelConsumption).count()

    session.close()

    return num_torque, num_fuel


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("vessel_api.yaml", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(host='0.0.0.0', port=8090)
