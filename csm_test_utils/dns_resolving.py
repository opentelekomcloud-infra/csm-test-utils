import logging
import socket
import sys
import time

import requests
from influx_line_protocol import Metric, MetricCollection
from ocomone.logging import setup_logger

from .common import base_parser, sub_parsers

INT_DNS = "int_dns_resolve"

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

AGP = sub_parsers.add_parser("internal_dns_resolve", add_help=False, parents=[base_parser])
AGP.add_argument("--dns_name", help="dns name of server to resolve", type=str)


def report(args):
    ip_list = []
    collection = MetricCollection()
    metric = Metric(INT_DNS)
    try:
        ais = socket.getaddrinfo(args.dns_name, 0, 0, 0, 0)
    except socket.gaierror as Err:
        metric.add_value("ips", Err)
        collection.append(metric)
        res = requests.post(f"{args.telegraf}/telegraf", data=str(collection), timeout=2)
        assert res.status_code == 204, f"Status is {res.status_code}"
        LOGGER.info(f"Metric written at: {args.telegraf})")
        return
    for result in ais:
        ip_list.append(result[-1][0])
    ip_list = list(set(ip_list))
    if ip_list is not None:
        metric.add_value("ips", ip_list)
        collection.append(metric)
        res = requests.post(f"{args.telegraf}/telegraf", data=str(collection), timeout=2)
        assert res.status_code == 204, f"Status is {res.status_code}"
        LOGGER.info(f"Metric written at: {args.telegraf})")


def main():
    args, _ = AGP.parse_known_args()
    setup_logger(LOGGER, "int_dns_resolve", log_dir=args.log_dir, log_format="[%(asctime)s] %(message)s")

    LOGGER.info(f"Started monitoring of Internal DNS (telegraf at {args.telegraf})")
    while True:
        try:
            report(args)
            time.sleep(.3)
        except KeyboardInterrupt:
            LOGGER.info("Monitoring Stopped")
            sys.exit(0)


if __name__ == "__main__":
    main()
