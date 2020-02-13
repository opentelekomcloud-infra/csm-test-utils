"""Script for new dashboard (sandbox)"""
import logging
import sys
import time

import requests
from ocomone.logging import setup_logger

from .common import Client, base_parser, sub_parsers

telegraf = "localhost:8080/telegraf"
MEASUREMENT = "as_loadbalancer"
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


# TODO: setup_telegraf_local на вмку запустить скрипт указать адрес телеграфа и селектом смотреть *requests*
# kappelmeister delatore start daemon


def get(client: Client):
    """Send request and write metrics to telegraf"""
    if requests.get("http://localhost:8080/").status_code == 200:
        result = "connected"
        reason = "ok"
    else:
        result = "connection_lost"
        reason = "fail"

    influx_row = f"${MEASUREMENT},reason=${reason} state=\"${result}\""
    client.report_metric(influx_row)


AGP = sub_parsers.add_parser("monitor", add_help=False, parents=[base_parser])


def main():
    """Start monitoring autoscaling's loadbalancer"""
    args, _ = AGP.parse_known_args()
    setup_logger(LOGGER, "continuous", log_dir=args.log_dir, log_format="[%(asctime)s] %(message)s")
    client = Client(args.target, args.telegraf)
    LOGGER.info(f"Started monitoring of {client.url} (telegraf at {client.tgf_address})")
    while True:
        try:
            get(client)
            time.sleep(10)
        except KeyboardInterrupt:
            LOGGER.info("Monitoring Stopped")
            sys.exit(0)


if __name__ == "__main__":
    main()
