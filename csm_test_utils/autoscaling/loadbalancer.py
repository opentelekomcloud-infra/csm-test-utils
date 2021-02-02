import logging
import sys
import time
from urllib.error import HTTPError

import requests
from influx_line_protocol import Metric
from ocomone.logging import setup_logger

from ..common import Client
from ..parsers import AGP_AS_LB

AS_LOADBALANCER = "as_loadbalancer"
CSM_EXCEPTION = "csm_exception"
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


def report(client: Client):
    """Send request and write metrics to telegraf"""
    try:
        target_req = requests.get(client.url, headers={"Connection": "close"})
        influx_row = Metric(AS_LOADBALANCER)
        if target_req.status_code == 200:
            influx_row.add_tag("state", "connected")
            influx_row.add_tag("host", "scn4")
            influx_row.add_tag("reason", "ok")
            influx_row.add_value("elapsed", target_req.elapsed.microseconds / 1000)
        else:
            influx_row.add_tag("state", "connection_lost")
            influx_row.add_tag("host", "scn4")
            influx_row.add_tag("reason", "fail")
            influx_row.add_value("elapsed", target_req.elapsed.microseconds / 1000)
    except (IOError, HTTPError) as error:
        influx_row = Metric(CSM_EXCEPTION)
        influx_row.add_tag("Reporter", AS_LOADBALANCER)
        influx_row.add_tag("Status", "Loadbalancer Unavailable")
        influx_row.add_value("Value", error)
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("Exception occured while metrics reporting")
        return
    client.report_metric(influx_row)


def main():
    """Start monitoring loadbalancer"""
    args, _ = AGP_AS_LB.parse_known_args()
    setup_logger(LOGGER, "lb_continuous", log_dir=args.log_dir,
                 log_format="[%(asctime)s] %(message)s")
    client = Client(args.target, args.telegraf)
    LOGGER.info("Started monitoring of %d (telegraf at %d)", client.url, client.tgf_address)
    while True:
        try:
            report(client)
            time.sleep(10)
        except KeyboardInterrupt:
            LOGGER.info("Monitoring \"as_load\" Stopped")
            sys.exit(0)


if __name__ == "__main__":
    main()
