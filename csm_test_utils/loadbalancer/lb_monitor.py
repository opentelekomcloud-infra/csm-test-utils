import logging
import socket

import requests
from ocomone.logging import setup_logger

from ..common import base_parser, sub_parsers

LB_TIMING = "lb_timing"
LB_TIMEOUT = "lb_timeout"

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

AGP = sub_parsers.add_parser("lb_load", add_help=False, parents=[base_parser])


def main():
    args, _ = AGP.parse_known_args()
    setup_logger(LOGGER, "lb_load", log_dir=args.log_dir, log_format="[%(asctime)s] %(message)s")
    timeout = 20
    try:
        res = requests.get(args.target, headers={"Connection": "close"}, timeout=timeout)
    except Exception as Ex:
        LOGGER.exception("Timeout sending request to LB")
        result = {
            "reason": LB_TIMEOUT,
            "client": socket.gethostname(),
            "timeout": timeout * 1000,
            "exception": Ex
        }
    else:
        result = {
            "reason": LB_TIMING,
            "client": socket.gethostname(),
            "server": res.headers["Server"],
            "elapsed": res.elapsed.microseconds / 1000
        }

    print(result)
    exit(0)


if __name__ == "__main__":
    main()
