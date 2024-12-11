"""receiver application"""

import logging
import logging.config
from pykafka import KafkaClient
from pykafka.exceptions import SocketDisconnectedError
import json
import datetime
import time
import os
import requests
import yaml
import connexion
from connexion import NoContent

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    APP_CONFIG_FILE = "/config/app_conf.yaml"
    LOG_CONFIG_FILE = "/config/log_conf.yaml"
else:
    print("In Dev Environment")
    APP_CONFIG_FILE = "app_conf.yaml"
    LOG_CONFIG_FILE = "log_conf.yaml"

with open (APP_CONFIG_FILE, 'r', encoding='utf-8') as config_file:
    app_config = yaml.safe_load(config_file.read())

with open(LOG_CONFIG_FILE, 'r', encoding='utf-8') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s", APP_CONFIG_FILE)
logger.info("Log Conf File: %s", LOG_CONFIG_FILE)

client = None
topic = None
producer = None

def initialize_kafka_client():
    '''Initializes the Kafka client, topic, and producer with retry logic.'''

    global client, topic, producer

    max_retries = 5
    retry_interval = 2  # seconds
    retries = 0

    while retries < max_retries:
        try:
            # Initialize Kafka client
            client = KafkaClient(hosts=f'{app_config["events"]["hostname"]}:{app_config["events"]["port"]}')
            topic = client.topics[str.encode(app_config["events"]["topic"])]
            producer = topic.get_sync_producer() # Get synchronous producer
            print("Kafka client and producer initialized successfully.")
            return
        except Exception as error:
            retries += 1
            print(f"Failed to initialize Kafka client/producer (attempt {retries}/{max_retries}): {error}")
            time.sleep(retry_interval)

    # If all retries fail
    raise Exception("Failed to initialize Kafka client and producer after retries.")

initialize_kafka_client()


def post_fuel_consumption(body):
    '''receives a fuel reading event'''
    try:
        msg = {"type": "fuel",
            "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "payload": body}
        msg_str = json.dumps(msg)
        producer.produce(msg_str.encode('utf-8'))

        status_code = 201
        return f"Message produced with status code: {status_code}"
    
    except SocketDisconnectedError as error:
        print(f"Producer disconnected: {error}. Retrying...")
        initialize_kafka_client() # Reinitialize Kafka client and producer
        return post_fuel_consumption(body) # Retry the operation

    except Exception as error:
        print(f"Failed to produce message: {error}")
        status_code = 500
        return f"Failed to produce message with status code: {status_code}"


def post_torque(body):
    '''receives a torque reading event'''
    try:
        msg = {"type": "torque",
            "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "payload": body}
        msg_str = json.dumps(msg)
        producer.produce(msg_str.encode('utf-8'))

        status_code = 201
        return f"Message produced with status code: {status_code}"
    
    except SocketDisconnectedError as error:
        print(f"Producer disconnected: {error}. Retrying...")
        initialize_kafka_client() # Reinitialize Kafka client and producer
        return post_fuel_consumption(body) # Retry the operation
    
    except Exception as error:
        print(f"Failed to produce message: {error}")
        status_code = 500
        return f"Failed to produce message with status code: {status_code}"


def get_fuel_consumption(start_timestamp, end_timestamp):
    """get fuel consumption"""

    header = {"content-type": "application/json"}
    parameters = {"start_timestamp": start_timestamp, "end_timestamp": end_timestamp}
    response = requests.get(url=app_config["eventstore1"]["url"], params=parameters, headers=header)
    print(response.json)
    return response.json(), 200

def get_torque(start_timestamp, end_timestamp):
    """get torque reading"""

    header = {"content-type": "application/json"}
    parameters = {"start_timestamp": start_timestamp, "end_timestamp": end_timestamp}
    response = requests.get(url=app_config["eventstore2"]["url"], params=parameters, headers=header)
    return response.json(), 200


def get_check():
    return 200


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("vessel_api.yaml", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
