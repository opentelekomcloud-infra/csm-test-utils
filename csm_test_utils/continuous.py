"""Stable continuous load to of the server"""
import logging
import sys
import time

import requests
from influx_line_protocol import Metric, MetricCollection
from ocomone.logging import setup_logger
from requests import Timeout

from .common import Client, base_parser, sub_parsers

LB_TIMING = "lb_timing"
LB_TIMEOUT = "lb_timeout"

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


def get(client: Client):
    """Send request and write metrics to telegraf"""
    timeout = 20
    metrics = MetricCollection()
    try:
        res = requests.get(client.url, headers={"Connection": "close"}, timeout=timeout)
    except Exception as Ex:
        LOGGER.exception("Timeout sending request to LB")
        lb_timeout = Metric(LB_TIMEOUT)
        lb_timeout.add_tag("client", client.host_name)
        lb_timeout.add_value("timeout", timeout * 1000)
        lb_timeout.add_value("exception", Ex)
        metrics.append(lb_timeout)
    else:
        lb_timing = Metric(LB_TIMING)
        lb_timing.add_tag("client", client.host_name)
        lb_timing.add_tag("server", res.headers["Server"])
        lb_timing.add_value("elapsed", res.elapsed.microseconds / 1000)
        metrics.append(lb_timing)
    client.report_metric(metrics)


AGP = sub_parsers.add_parser("monitor", add_help=False, parents=[base_parser])


def main():
    """Start monitoring"""
    args, _ = AGP.parse_known_args()
    setup_logger(LOGGER, "continuous", log_dir=args.log_dir, log_format="[%(asctime)s] %(message)s")
    client = Client(args.target, args.telegraf)
    LOGGER.info(f"Started monitoring of {client.url} (telegraf at {client.tgf_address})")
    while True:
        try:
            get(client)
            time.sleep(0.5)
        except KeyboardInterrupt:
            LOGGER.info("Monitoring Stopped")
            sys.exit(0)


if __name__ == "__main__":
    main()
