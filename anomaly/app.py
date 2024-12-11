import os
import yaml
import logging
import logging.config
from pykafka import KafkaClient
import json
from pykafka.common import OffsetType
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import connexion

# added to work around CORS
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware


if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_config_file = "/config/app_config.yaml"
    log_config_file = "/config/log_conf.yaml"
else:
    print("In Dev Environment")
    app_config_file = "app_config.yaml"
    log_config_file = "log_conf.yaml"

with open (app_config_file, 'r') as config_file:
    app_config = yaml.safe_load(config_file.read())

with open(log_config_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s" % app_config_file)
logger.info("Log Conf File: %s" % log_config_file)

def find_fuel_anomaly():
    hostname = "%s:%d" % (app_config["events"]["hostname"],
    app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    consumer = topic.get_simple_consumer(consumer_group=b'event_group',
        reset_offset_on_start=False,
        auto_offset_reset=OffsetType.LATEST)
    
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        payload = msg["payload"]
        if msg["type"] == "fuel" and payload["fuel_consumed"] <= 100:
                if os.path.exists(app_config['datastore']['filename']):
                    try:
                        with open(app_config['datastore']['filename'], "r") as f:
                            anomoly_data = json.load(f)
                        anomoly_to_add = {
                            "event_id": payload["vessel_id"],
                            "trace_id": payload["trace_id"],
                            "event_type": "fuel_consumed",
                            "anomaly_type": "TooLow",
                            "description": "The value is too low (Fuel consumed of 100 is less than the Threshold of 150)",
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        }
                        if any(anomaly["trace_id"] == anomoly_to_add["trace_id"] for anomaly in anomoly_data):
                            logger.info("Anomaly already recorded. Skipping.")
                            continue

                        logger.info(anomoly_to_add)
                        anomoly_data.append(anomoly_to_add)

                        with open(app_config['datastore']['filename'], "w") as f:
                            json.dump(anomoly_data, f, indent=4)
                            logger.info("Fuel anomaly added to the database")
                        return anomoly_data, 200
                    
                    except Exception as e:
                        print (f"Error, {e}")
                else:
                    anomoly_to_add = [{
                            "event_id": payload["vessel_id"],
                            "trace_id": payload["trace_id"],
                            "event_type": "fuel_consumed",
                            "anomaly_type": "TooLow",
                            "description": "The value is too low (Fuel consumed of 100 is less than the Threshold of 150)",
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                        }]
                    with open(app_config['datastore']['filename'], "w") as file:
                        json.dump(anomoly_to_add, file, indent=4)
                        logger.info("Fuel anomaly added to the database")
                    return anomoly_to_add
                
                
def find_torque_anomaly():
    hostname = "%s:%d" % (app_config["events"]["hostname"],
    app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    consumer = topic.get_simple_consumer(consumer_group=b'event_group',
        reset_offset_on_start=False,
        auto_offset_reset=OffsetType.LATEST)
    
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        payload = msg["payload"]
        if msg["type"] == "torque" and payload["torque"] > 100000000:
            if os.path.exists(app_config['datastore']['filename']):
                try:
                    with open(app_config['datastore']['filename'], "r") as f:
                        anomoly_data = json.load(f)
                    anomoly_to_add = {
                        "event_id": payload["vessel_id"],
                        "trace_id": payload["trace_id"],
                        "event_type": "torque",
                        "anomaly_type": "TooHigh",
                        "description": "The value is too high (Torque of 100000000 is more than the Threshold of 10000000)",
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    }
                    if any(anomaly["trace_id"] == anomoly_to_add["trace_id"] for anomaly in anomoly_data):
                        logger.info("Anomaly already recorded. Skipping.")
                        continue

                    logger.info(anomoly_to_add)
                    anomoly_data.append(anomoly_to_add)

                    with open(app_config['datastore']['filename'], "w") as f:
                        json.dump(anomoly_data, f, indent=4)
                        logger.info("Torque anomaly added to the database")
                    return anomoly_data, 200
                    
                except Exception as e:
                    print (f"Error, {e}")
            else:
                anomoly_to_add = [{
                        "event_id": payload["vessel_id"],
                        "trace_id": payload["trace_id"],
                        "event_type": "Torque",
                        "anomaly_type": "TooHigh",
                        "description": "The value is too high (Torque of 100000000 is more than the Threshold of 10000000)",
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    }]
                with open(app_config['datastore']['filename'], "w") as file:
                    json.dump(anomoly_to_add, file, indent=4)
                    logger.info("Torque anomaly added to the database")
                return anomoly_to_add


def get_anomalies(anomaly_type):
    logger.info("list of anomalies has been requested")
    if os.path.exists(app_config['datastore']['filename']):
        try:
            with open(app_config['datastore']['filename'], "r") as f:
                list_of_anomolies = json.load(f)
                list_to_return = []
                for item in list_of_anomolies:
                    if item["anomaly_type"] == anomaly_type:
                        list_to_return.append(item)
                list_to_return.reverse()
                return list_to_return, 200
            
        except Exception as e:
            print(f"Error, {e}")
            return [404]
    else:
        print("No Anomolies to Report")
        return [404]




def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(find_fuel_anomaly, 'interval', seconds=6)
    sched.add_job(find_torque_anomaly, 'interval', seconds=app_config['scheduler']['period_sec'])
    sched.start()

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

# added to work around CORS
app.add_middleware(CORSMiddleware, position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        )


if __name__ == "__main__":
    init_scheduler()
    logger.info("Fuel anomaly threshold is 150")
    logger.info("Torque anomaly threshold is 10000000")
    app.run(host='0.0.0.0', port=8120)