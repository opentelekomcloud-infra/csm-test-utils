import logging
import sys
import time

import requests
from influx_line_protocol import Metric
from ocomone.logging import setup_logger

from ..common import Client, base_parser, sub_parsers

AS_LOADBALANCER = "as_loadbalancer"
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


def report(client: Client):
    """Send request and write metrics to telegraf"""
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
    client.report_metric(influx_row)


AGP = sub_parsers.add_parser("as_load", add_help=False, parents=[base_parser])


def main():
    """Start monitoring loadbalancer"""
    args, _ = AGP.parse_known_args()
    setup_logger(LOGGER, "lb_continuous", log_dir=args.log_dir, log_format="[%(asctime)s] %(message)s")
    client = Client(args.target, args.telegraf)
    LOGGER.info(f"Started monitoring of {client.url} (telegraf at {client.tgf_address})")
    while True:
        try:
            report(client)
            time.sleep(10)
        except KeyboardInterrupt:
            LOGGER.info("Monitoring Stopped")
            sys.exit(0)


if __name__ == "__main__":
    main()
