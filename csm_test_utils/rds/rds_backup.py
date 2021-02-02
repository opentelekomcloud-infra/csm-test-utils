import datetime
import json
import logging
from datetime import datetime

import requests
import yaml
from influx_line_protocol import Metric, MetricCollection
from ocomone import setup_logger
from requests import HTTPError, Response

from ..common import Client
from ..parsers import AGP_RDS_BACKUP

API_VERSION = "v3"
RDS_BACKUP = "rds_backup_monitor"
CSM_EXCEPTION = "csm_exception"
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
CONTENT_TYPE = "application/json;charset=utf8"


def get_auth_token(endpoint, cloud_config, cloud_name):
    """Get auth token using data from clouds.yaml file

    Token and project_id are returned as a string
    """
    with open(cloud_config) as clouds_yaml:
        data = yaml.safe_load(clouds_yaml)
    auth_data = data["clouds"][cloud_name]["auth"]
    request_headers = {"Content-Type": CONTENT_TYPE}
    request_body = json.dumps({
        "auth": {
            "identity": {
                "methods": ["password"],
                "password": {
                    "user": {
                        "name": auth_data["username"],
                        "password": auth_data["password"],
                        "domain": {
                            "name": auth_data["domain_name"]
                        }
                    }
                }
            },
            "scope": {
                "project": {
                    "name": auth_data["project_name"]
                }
            }
        }
    })
    url = "/".join([endpoint, API_VERSION, "auth/tokens"])
    response = requests.post(url=url, data=request_body, headers=request_headers)
    token = response.headers.get("X-Subject-Token")
    project_id = response.json()["token"]["project"]["id"]
    return token, project_id


def get_rds_backup_info(endpoint: str, token: str, project_id: str, **request_params) -> Response:
    """Get full information about RDS backups"""
    url = "/".join([endpoint, API_VERSION, project_id, "backups?"])
    request_headers = {"Content-Type": CONTENT_TYPE, "X-Auth-Token": token}
    response = requests.get(url=url, params=request_params, headers=request_headers)
    return response


def get_duration(start_time: str, end_time: str):
    """Get RDS backup duration"""
    time_delta = (format_date_time(end_time) - format_date_time(start_time)).total_seconds()
    return time_delta


def format_date_time(date_time: str) -> datetime:
    """Format date and time"""
    return datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%S%z")


def get_rds_backup_status(endpoint: str, token: str, project_id: str,
                          instance_id: str, backup_type: str) -> Response:
    """Return RDS backup status"""
    request_params = {"instance_id": instance_id, "backup_type": backup_type}
    response = get_rds_backup_info(endpoint, token, project_id, **request_params)
    return response


def report(client: Client, endpoint: str, token: str, project_id: str, **request_params):
    """Send request and write metrics to telegraf"""
    collection = MetricCollection()
    try:
        influx_row = Metric(RDS_BACKUP)
        target_req = get_rds_backup_info(endpoint, token, project_id, **request_params)
        if target_req.ok:
            backups = target_req.json()["backups"]
            for backup in backups:
                influx_row.add_tag("id_backup", backup["id"])
                influx_row.add_tag("status", backup["status"])
                influx_row.add_tag("size", backup["size"])
                influx_row.add_value("backup_duration", get_duration(backup["begin_time"],
                                                                     backup["end_time"]))
                collection.append(influx_row)
        else:
            influx_row.add_tag("status", "request_failed")
            influx_row.add_tag("host", "scn6")
            influx_row.add_tag("reason", "fail")
            influx_row.add_value("elapsed", target_req.elapsed.seconds)
            collection.append(influx_row)
    except (IOError, HTTPError) as error:
        influx_row = Metric(CSM_EXCEPTION)
        influx_row.add_tag("Reporter", RDS_BACKUP)
        influx_row.add_tag("Status", "RDS Unavailable")
        influx_row.add_value("Value", error)
        collection.append(influx_row)
    client.report_metric(collection)


def main():
    args, _ = AGP_RDS_BACKUP.parse_known_args()
    request_params = {"instance_id": args.instance_id, "backup_type": "auto"}
    client = Client(args.target, args.telegraf)
    setup_logger(LOGGER, "rds_backup_monitor", log_dir=args.log_dir,
                 log_format="[%(asctime)s] %(message)s")
    LOGGER.info("Started monitoring of %d (telegraf at %d)", client.url, client.tgf_address)
    LOGGER.info("Generate token")
    token, project_id = get_auth_token(args.endpoint, args.cloud_config, args.cloud_name)
    LOGGER.info("Monitoring")
    report(client, args.endpoint, token, project_id, **request_params)




if __name__ == "__main__":
    main()
