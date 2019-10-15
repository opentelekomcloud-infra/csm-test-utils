import os
import re
import socket
from argparse import ArgumentParser
from threading import Thread

import requests
from influx_line_protocol import MetricCollection
from requests import Timeout

base_parser = ArgumentParser(prog="csm_test_utils", description="Multi-purpose test script")

base_parser.add_argument("--target", help="Load balancer address")
__tgf_default = os.getenv("TGF_ADDRESS", "")
base_parser.add_argument("--telegraf",
                         help=f"Address of telegraf server for reporting. "
                              f"Default is taken from TGF_ADDRESS variable ('{__tgf_default}')",
                         default=__tgf_default)
base_parser.add_argument("--log-dir", "-l", help="Directory to write log file to", default=".")

root_parser = ArgumentParser(parents=[base_parser], add_help=False)
sub_parsers = root_parser.add_subparsers(dest="test", help="Test to be run")

RE_URL = re.compile(r"^https?://.+$")


class Client:
    """Telegraf report client which knows own ip :o"""

    def __init__(self, url: str, tgf_address):

        if RE_URL.fullmatch(url) is None:
            url = f"http://{url}"
        self.url = url

        try:
            public_ip = requests.get("http://ipecho.net/plain", timeout=2).text
        except Timeout:
            public_ip = ""

        self.host_name = public_ip or socket.gethostname()
        self.tgf_address = tgf_address
        self._next_boom = 0

    def report_metric(self, metrics: MetricCollection):
        """Report metric to the server in new thread"""

        def _post_data():
            res = requests.post(f"{self.tgf_address}/telegraf", data=str(metrics), timeout=2)
            assert res.status_code == 204, f"Status is {res.status_code}"

        Thread(target=_post_data).start()
