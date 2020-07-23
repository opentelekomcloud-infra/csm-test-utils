import logging
import sys
import time

import requests
from influx_line_protocol import Metric, MetricCollection
from ocomone.logging import setup_logger
from requests import Timeout

from ..common import base_parser, sub_parsers

INT_DNS_TIMING = "int_dns_timing"
INT_DNS_TIMEOUT = "int_dns_timeout"
collection = MetricCollection()

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

AGP = sub_parsers.add_parser("internal_dns_host_check", add_help=False, parents=[base_parser])
AGP.add_argument("--dns_name", help="dns name of server to resolve", type=str)


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
    setup_logger(LOGGER, "int_dns_host_check", log_dir=args.log_dir, log_format="[%(asctime)s] %(message)s")

    LOGGER.info(f"Started monitoring of Internal DNS host (telegraf at {args.telegraf})")
    while True:
        try:
            get_client_response(args)
            time.sleep(0.5)
        except KeyboardInterrupt:
            LOGGER.info("Monitoring Stopped")
            sys.exit(0)


if __name__ == "__main__":
    main()
