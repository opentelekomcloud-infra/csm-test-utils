import logging
import socket
import sys
import time

import requests
from influx_line_protocol import Metric, MetricCollection
from ocomone.logging import setup_logger

from ..common import base_parser, sub_parsers, Client

INT_DNS = "int_dns_resolving"

collection = MetricCollection()

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

AGP = sub_parsers.add_parser("internal_dns_resolve", add_help=False, parents=[base_parser])
AGP.add_argument("--dns_name", help="dns name of server to resolve", type=str)


def dns_resolve(client: Client):
    metric = Metric(INT_DNS)
    try:
        socket.getaddrinfo(client.url, 0, 0, 0, 0)
    except socket.gaierror as Err:
        metric.add_value("ips", Err)
        metric.add_tag("dns_name", client.url)
        metric.add_tag("result", "Not Resolved")
        collection.append(metric)
        client.report_metric(collection)


def main():
    args, _ = AGP.parse_known_args()
    setup_logger(LOGGER, "int_dns_resolve", log_dir=args.log_dir, log_format="[%(asctime)s] %(message)s")
    client = Client(args.dns_name, args.telegraf)
    LOGGER.info(f"Started monitoring of Internal DNS (telegraf at {args.telegraf})")
    while True:
        try:
            dns_resolve(client)
            time.sleep(.3)
        except KeyboardInterrupt:
            LOGGER.info("Monitoring Stopped")
            sys.exit(0)


if __name__ == "__main__":
    main()
