import logging
import socket
import sys
import time

import requests
from influx_line_protocol import Metric, MetricCollection
from ocomone.logging import setup_logger
from requests import Timeout

from .common import base_parser, sub_parsers

INT_DNS = "int_dns_resolve"
INT_DNS_TIMING = "int_dns_timing"
INT_DNS_TIMEOUT = "int_dns_timeout"
collection = MetricCollection()

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

AGP = sub_parsers.add_parser("internal_dns_resolve", add_help=False, parents=[base_parser])
AGP.add_argument("--dns_name", help="dns name of server to resolve", type=str)


def dns_resolve(args):
    ip_list = []
    metric = Metric(INT_DNS)
    try:
        ais = socket.getaddrinfo(args.dns_name, 0, 0, 0, 0)
    except socket.gaierror as Err:
        metric.add_value("ips", Err)
        metric.add_tag("dns_name", args.dns_name)
        metric.add_tag("result", "Not Resolved")
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
        metric.add_tag("dns_name", args.dns_name)
        metric.add_tag("result", "Resolved")
        collection.append(metric)
        res = requests.post(f"{args.telegraf}/telegraf", data=str(collection), timeout=2)
        assert res.status_code == 204, f"Status is {res.status_code}"
        LOGGER.info(f"Metric written at: {args.telegraf})")
    get_client_response(args)

def get_client_response(args):
    timeout = 5
    try:
        res = requests.get(f"http://{args.dns_name}", headers={"Connection": "close"}, timeout=timeout)
    except Timeout:
        LOGGER.exception("Timeout sending request to LB")
        lb_timeout = Metric(INT_DNS_TIMEOUT)
        lb_timeout.add_tag("client", args.dns_name)
        lb_timeout.add_value("timeout", timeout * 1000)
        collection.append(lb_timeout)
    else:
        lb_timing = Metric(INT_DNS_TIMING)
        lb_timing.add_tag("client", args.dns_name)
        lb_timing.add_tag("server", res.headers["Server"])
        lb_timing.add_value("elapsed", res.elapsed.microseconds / 1000)
        collection.append(lb_timing)
    res = requests.post(f"{args.telegraf}/telegraf", data=str(collection), timeout=2)
    assert res.status_code == 204, f"Status is {res.status_code}"
    LOGGER.info(f"Metric written at: {args.telegraf})")


def main():
    args, _ = AGP.parse_known_args()
    setup_logger(LOGGER, "int_dns_resolve", log_dir=args.log_dir, log_format="[%(asctime)s] %(message)s")

    LOGGER.info(f"Started monitoring of Internal DNS (telegraf at {args.telegraf})")
    while True:
        try:
            dns_resolve(args)
            time.sleep(.3)
        except KeyboardInterrupt:
            LOGGER.info("Monitoring Stopped")
            sys.exit(0)


if __name__ == "__main__":
    main()
