import requests
from requests.exceptions import Timeout, ConnectionError
import yaml
import connexion
import logging
import logging.config
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

APP_CONFIG_FILE = app_conf.yaml
LOG_CONFIG_FILE = log_conf.yml

with open (APP_CONFIG_FILE, 'r', encoding='utf-8') as config_file:
    app_config = yaml.safe_load(config_file.read())

with open(LOG_CONFIG_FILE, 'r', encoding='utf-8') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

RECEIVER_URL = app_config["eventstore2"]["url"]
STORAGE_URL = app_config["eventstore1"]["url"]
PROCESSING_URL = app_config["eventstore3"]["url"]
ANALYZER_URL = app_config["eventstore4"]["url"]
TIMEOUT = app_config['scheduler']['period_sec'] # Set to 2 seconds in your config file

default_stats_file = {
    "receiver": "Unknown",
    "storage": "Unknown",
    "processing": "Unknown",
    "analyzer": "Unknown",
}

def get_checks():
    """Called periodically"""

    receiver_status = "Unavailable"
    try:
        response = requests.get(RECEIVER_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            receiver_status = "Healthy"
            logger.info("Receiver is Healthly")
        else:
            logger.info("Receiver returning non-200 response")
    except (Timeout, ConnectionError):
        logger.info("Receiver is Not Available")

    storage_status = "Unavailable"
    try:
        response = requests.get(STORAGE_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            storage_json = response.json()
            storage_status = f"Storage has {storage_json['num_torque']} Torque and {storage_json['num_fuel']} fuel events"
            logger.info("Storage is Healthy")
        else:
            logger.info("Storage returning non-200 response")
    except (Timeout, ConnectionError):
        logger.info("Storage is Not Available")

    analyzer_status = "Unavailable"
    try:
        response = requests.get(ANALYZER_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            analyzer_json = response.json()
            analyzer_status = f"Analyzer has {analyzer_json["torque_count"]} Torque and {analyzer_json["fuel_count"]} Fuel events"
            logger.info("Analyzer is Healthy")
        else:
            logger.info("Analyzer returning non-200 response")
    except (Timeout, ConnectionError):
        logger.info("Analyzer is unavailable")

        processing_status = "Unavailable"
    try:
        response = requests.get(PROCESSING_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            processing_json = response.json()
            processing_status = f"Processing has {processing_json["num_torque_readings"]} Torque and {processing_json["num_fuel_readings"]} Fuel events"
            logger.info("Processing is Healthy")
        else:
            logger.info("Processing returning non-200 response")
    except (Timeout, ConnectionError):
        logger.info("Processing is unavailable")

    if os.path.exists(app_config['datastore']['filename']):
        try:
            with open(app_config['datastore']['filename'], "r") as f:
                stats_data = json.load(f)
            return_dict = {
                "receiver": receiver_status,
                "storage": storage_status,
                "processing": processing_status,
                "analyzer": analyzer_status,
            }
            logger.debug(f"{return_dict}")
            logger.info("request completed!")
            return return_dict, 200

        except Exception as e:
            logger.error(f"file does not exist: {e}")
            return {"Statistics do not exist"}, 404
    else:
        with open(app_config['datastore']['filename'], "w") as file:
            json.dump(default_stats_file, file, indent=4)
        return default_stats_file



app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("vessel_api.yaml", strict_validation=True, validate_responses=True)

app.add_middleware(CORSMiddleware, position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        )

def init_scheduler():
    """create scheduler"""

    sched = BackgroundScheduler(daemon=True)
    sched.add_job(get_checks, 'interval', seconds=app_config['scheduler2']['period_sec'])
    sched.start()


if __name__ == "__main__":
    init_scheduler()
    uvicorn.run(app, host="0.0.0.0", port=8130, reload=False)