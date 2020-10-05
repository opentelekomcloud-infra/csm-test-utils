import datetime
import logging
import sys
import time

import requests
import os
import yaml
import json

from influx_line_protocol import Metric, MetricCollection
from ocomone import setup_logger
from requests import Response, HTTPError
from datetime import datetime
from ..common import Client, base_parser, sub_parsers


BASE_URL = "https://rds.eu-de.otc.t-systems.com/v3"
RDS_BACKUP = "rds_backup_monitor"
CSM_EXCEPTION = "csm_exception"
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


def get_auth_token() -> str:
    """Get auth token using data from clouds.yaml file. Token and project_id are returned as a string"""
    cloud_name = os.getenv("TF_VAR_cloud")
    cloud_file = os.getenv("OS_CLIENT_CONFIG_FILE")
    with open(cloud_file) as clouds_yaml:
        data = yaml.safe_load(clouds_yaml)
    request_headers = {'Content-Type': 'application/json;charset=utf8'}
    request_body = json.dumps({
                       'auth': {
                         'identity': {
                           'methods': ['password'],
                           'password': {
                             'user': {
                               'name': data['clouds'][cloud_name]['auth']['username'],
                               'password': data['clouds'][cloud_name]['auth']['password'],
                               'domain': {
                                 'name': data['clouds'][cloud_name]['auth']['user_domain_name']
                               }
                             }
                           }
                         },
                         'scope': {
                           'project': {
                             'name': data['clouds'][cloud_name]['auth']['project_name']
                           }
                         }
                       }
        })
    url = "/".join([BASE_URL, "auth/tokens"])
    response = requests.post(url = url, data = request_body, headers = request_headers)
    token = response.headers.get('X-Subject-Token')
    project_id = response.json()['token']['project']['id']
    return token, project_id


def get_rds_backup_info(token: str, project_id: str, **request_params) -> Response:
    url = "/".join([BASE_URL, project_id, "backups?"])
    request_headers = {'Content-Type': 'application/json;charset=utf8', 'X-Auth-Token': token}
    response = requests.get(url = url, params = request_params, headers = request_headers)
    return response


def get_duration(start_time: str, end_time: str):
    time_delta = (format_date_time(end_time) - format_date_time(start_time)).total_seconds()
    return time_delta


def format_date_time(date_time: str):
    return datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%S%z")


def get_rds_backup_status(token: str, project_id: str, instance_id: str, backup_type: str) -> str:
    request_params = {'instance_id': instance_id, 'backup_type': backup_type}
    response = get_rds_backup_info(token, project_id, **request_params)
    return response


def report(client: Client, token: str, project_id: str, **request_params):
    """Send request and write metrics to telegraf"""
    influx_row = Metric(RDS_BACKUP)
    collection = MetricCollection()
    try:
        target_req = get_rds_backup_info(token, project_id, **request_params)
        if target_req.ok:
            backups = target_req.json()["backups"]
            for backup in backups:
                influx_row.add_tag("id_backup", backup["id"])
                influx_row.add_tag("name", backup["name"])
                influx_row.add_tag("type", backup["type"])
                influx_row.add_tag("status", backup["status"])
                influx_row.add_tag("size", backup["size"])
                influx_row.add_tag("begin_time", backup["begin_time"])
                influx_row.add_tag("end_time", backup["end_time"])
                influx_row.add_tag("duration (sec)", get_duration(backup["begin_time"], backup["end_time"]))
                collection.append(influx_row)
        else:
            influx_row.add_tag("state", "connection_lost")
            influx_row.add_tag("host", "scn6")
            influx_row.add_tag("reason", "fail")
            influx_row.add_value("elapsed", target_req.elapsed.seconds)
            collection.append(influx_row)
    except (IOError, HTTPError) as Error:
        influx_row = Metric(CSM_EXCEPTION)
        influx_row.add_tag("Reporter", RDS_BACKUP)
        influx_row.add_tag("Status", "RDS Unavailable")
        influx_row.add_value("Value", Error)
        collection.append(influx_row)
    except Exception as Ex:
        return LOGGER.exception(Ex)
    client.report_metric(collection)


AGP = sub_parsers.add_parser(RDS_BACKUP, add_help=False, parents=[base_parser])
AGP.add_argument("--instance_id", help = "RDS instance ID")


def main():
    args, _ = AGP.parse_known_args()
    token, project_id = get_auth_token()
    instance_id = args.instance_id
    request_params = {'instance_id': instance_id, 'backup_type': 'auto'}
    report(token, project_id, **request_params)
    setup_logger(LOGGER, "rds_backup_monitor", log_dir = args.log_dir, log_format = "[%(asctime)s] %(message)s")
    client = Client(args.target, args.telegraf)
    LOGGER.info(f"Started monitoring of {client.url} (telegraf at {client.tgf_address})")
    while True:
        try:
            report(client, token, project_id, **request_params)
            time.sleep(360)
        except KeyboardInterrupt:
            LOGGER.info("Monitoring Stopped")
            sys.exit(0)


if __name__ == "__main__":
    main()
