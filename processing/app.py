"""processing app"""


import logging
import logging.config
import datetime
import json
import statistics
import os
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import uvicorn
import yaml
import connexion

# added to work around CORS - test
# test 2
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

default_stats_file = {
    "num_fuel_readings": 0,
    "avg_fuel_reading": 0,
    "num_torque_readings": 0,
    "avg_torque_reading": 0,
    "last_updated": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
}

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

def get_processing_stats():
    """Get processing stats"""

    logger.info("Get stats request has begun")

    if os.path.exists(app_config['datastore']['filename']):
        try:
            with open(app_config['datastore']['filename'], "r", encoding='utf-8') as app_file:
                stats_data = json.load(app_file)
            return_dict = {
                "num_fuel_readings": int(stats_data["num_fuel_readings"]),
                "avg_fuel_reading": int(stats_data["avg_fuel_reading"]),
                "num_torque_readings": int(stats_data["num_torque_readings"]),
                "avg_torque_reading": int(stats_data["avg_torque_reading"]),
                "last_updated": stats_data["last_updated"]
            }
            logger.debug("%s", return_dict)
            logger.info("request completed!")
            return return_dict, 200

        except Exception as error:
            logger.error("file does not exist: %s", error)
            return {"Statistics do not exist"}, 404
    else:
        with open(app_config['datastore']['filename'], "w") as file:
            json.dump(default_stats_file, file, indent=4)
        return default_stats_file


def populate_stats():
    """ Periodically update stats """

    logger.info("Periodic processing has started")
    logger.info("Assignment 3")
    with open(app_config['datastore']['filename'],'r', encoding='utf-8') as app_file:
        current_stats = json.load(app_file)
        logger.info("loaded")

    last_updated_date = current_stats['last_updated']
    current_time = datetime.datetime.now()
    format_current_time = datetime.datetime.strftime(current_time, "%Y-%m-%dT%H:%M:%SZ")
    current_stats['last_updated'] = format_current_time

    header = {"content-type": "application/json"}
    parameters = {"start_timestamp": last_updated_date, "end_timestamp": format_current_time}

    # get fuel readings
    try:
        get_fuel_events = requests.get(url=app_config["eventstore1"]["url"], params=parameters, headers=header)
        if get_fuel_events.status_code != 200:
            logger.error("Error in the application: %s", get_fuel_events.status_code)
        else:
            logger.info(f"number of events received from Fuel process: {len(get_fuel_events.json())}")
    except Exception as error:
        print(error)

    ## update fuel stats
    fuel_events_data = get_fuel_events.json()
    current_stats['num_fuel_readings'] += len(get_fuel_events.json())
    calculate_fuel_average = []
    for item in fuel_events_data:
        calculate_fuel_average.append(item['fuel_consumed'])
    current_stats['avg_fuel_reading'] =  statistics.mean(calculate_fuel_average)


    # get torque readings
    get_torque_events = requests.get(url=app_config["eventstore2"]["url"], params=parameters, headers=header)
    if get_torque_events.status_code != 200:
        logger.error("Error in the application: %s", get_torque_events.status_code)
    else:
        logger.info(f"number of events received from Fuel process: {len(get_torque_events.json())}")

    ## update torque stats
    torque_events_data = get_torque_events.json()
    current_stats['num_torque_readings'] += len(get_torque_events.json())
    calculate_torque_average = []
    for item in torque_events_data:
        calculate_torque_average.append(item['torque'])
    current_stats['avg_torque_reading'] = statistics.mean(calculate_torque_average)

    with open(app_config['datastore']['filename'], "w", encoding='utf-8') as app_file:
        json.dump(current_stats, app_file, indent=4)


    logger.debug(f"Current Stats: num_fuel_readings - {current_stats['num_fuel_readings']}, avg_fuel_reading - {current_stats['avg_fuel_reading']}, num_torque_reading - {current_stats['num_torque_readings']}, avg_torque_reading - {current_stats['avg_torque_reading']}")
    logger.info("period processing has ended!")

def init_scheduler():
    """create scheduler"""

    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats, 'interval', seconds=app_config['scheduler']['period_sec'])
    sched.start()



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
    init_scheduler()
    # populate_stats()
    # get_processing_stats()
    uvicorn.run(app, host="0.0.0.0", port=8100, reload=False)
