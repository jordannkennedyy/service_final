import logging
import logging.config
import json
import os
import connexion
import yaml
from pykafka import KafkaClient

# added to work around CORS
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

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


def get_fuel(index):
    "get fuel"

    hostname = "%s:%d" % (app_config["events"]["hostname"],
    app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
    consumer_timeout_ms=1000)

    logger.info("Retrieving fuel at index: %s", index)
    try:
        current_index = 0
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)

            if current_index == index and msg['type'] == 'fuel':
                logger.info(f"Found message: {msg}")
                return msg['payload'], 200
            current_index += 1
    except Exception as e:
        logger.error("No more messages found: %s", e)
    logger.error("Could not find fuel at index: %s", index)
    return { "message": "Not Found"}, 404


def get_torque(index):
    "get torque"

    hostname = "%s:%d" % (app_config["events"]["hostname"],
        app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
    consumer_timeout_ms=1000)

    logger.info("Retrieving torque at index: %s", index)
    try:
        current_index = 0
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)

            if current_index == index and msg['type'] == 'torque':
                logger.info(f"Found message: {msg}")
                return msg['payload'], 200
            current_index += 1
    except Exception as e:
        logger.error("No more messages found: %s", e)
    logger.error("Could not find torque at index: %s", index)
    return { "message": "Not Found"}, 404


def get_stats():
    "get stats"

    hostname = "%s:%d" % (app_config["events"]["hostname"],
        app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
    consumer_timeout_ms=1000)

    try:
        fuel_count = 0
        torque_count = 0
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)

            if msg['type'] == 'fuel':
                fuel_count += 1
            elif msg['type'] == 'torque':
                torque_count += 1
        return {"fuel_count": fuel_count, "torque_count": torque_count}
    except Exception as e:
        logger.error("No more messages found: %s", e)
    return { "message": "Not Found"}, 404


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("vessel_api.yaml", strict_validation=True, validate_responses=True)

# added to work around CORS
app.add_middleware(CORSMiddleware, position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        )


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8110)
