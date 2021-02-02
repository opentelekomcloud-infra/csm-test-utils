import re
import socket
from threading import Thread

import requests
from influx_line_protocol import MetricCollection
from requests import Timeout

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
