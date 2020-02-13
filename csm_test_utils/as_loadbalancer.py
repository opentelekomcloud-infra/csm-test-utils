"""Script for new dashboard (sandbox)"""
import logging
import sys
import time

import requests
from ocomone.logging import setup_logger

from .common import base_parser, sub_parsers

tgf_address = "localhost:8080/telegraf"
MEASUREMENT = "as_loadbalancer"
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


def report(target):
    """Send request and write metrics to telegraf"""
    if requests.get(target).status_code == 200:
        result = "connected"
        reason = "ok"
        LOGGER.info("OK")
    else:
        result = "connection_lost"
        reason = "fail"
        LOGGER.info("FAIL")

    influx_row = f"${MEASUREMENT},reason=${reason} state=\"${result}\""
    res = requests.post(tgf_address, data=influx_row)
    assert res.status_code == 204, f"Status is {res.status_code}"


AGP = sub_parsers.add_parser("as_load", add_help=False, parents=[base_parser])


def main():
    """Start monitoring autoscaling loadbalancer"""
    args, _ = AGP.parse_known_args()
    setup_logger(LOGGER, "continuous", log_dir=args.log_dir, log_format="[%(asctime)s] %(message)s")
    LOGGER.info(f"Started monitoring of {args.target} (telegraf at {args.telegraf})")
    while True:
        try:
            report(args.target)
            time.sleep(10)
        except KeyboardInterrupt:
            LOGGER.info("Monitoring Stopped")
            sys.exit(0)


if __name__ == "__main__":
    main()
