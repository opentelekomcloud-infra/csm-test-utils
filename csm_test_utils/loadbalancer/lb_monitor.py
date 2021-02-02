import logging
import socket

import requests
from ocomone.logging import setup_logger

from ..parsers import AGP_LB_LOAD

LB_TIMING = "lb_timing"
LB_TIMEOUT = "lb_timeout"

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


def main():
    args, _ = AGP_LB_LOAD.parse_known_args()
    setup_logger(LOGGER, "lb_load", log_dir=args.log_dir, log_format="[%(asctime)s] %(message)s")
    timeout = 20
    try:
        res = requests.get(args.target, headers={"Connection": "close"}, timeout=timeout)
    except requests.Timeout as ex:
        LOGGER.exception("Timeout sending request to LB")
        result = {
            "reason": LB_TIMEOUT,
            "client": socket.gethostname(),
            "timeout": timeout * 1000,
            "exception": ex
        }
    else:
        result = {
            "reason": LB_TIMING,
            "client": socket.gethostname(),
            "server": res.headers["Server"],
            "elapsed": res.elapsed.microseconds / 1000
        }

    print(result)


if __name__ == "__main__":
    main()
