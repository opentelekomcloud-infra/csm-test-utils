"""Check if server is working"""

import random
import string
import time
from threading import Thread

from influx_line_protocol import Metric, MetricCollection
from ocomone.session import BaseUrlSession
from ocomone.timer import Timer

from .common import Client
from .parsers import AGP_RDS_MONITOR


def _rand_str():
    return "".join(random.choice(string.ascii_letters) for _ in range(10))


CE_RESULT = "ce_result"


class ClientException(Exception):
    """Exception during test"""


NOT_CREATED = ClientException("not_created")
NOT_FOUND = ClientException("not_found")
INVALID_FILTER = ClientException("invalid_filter")
NOT_DELETED = ClientException("not_deleted")


class EntityClient:
    """Class for entities operations"""

    def __init__(self, base_url: str):
        self.session = BaseUrlSession(base_url)

    def create(self, data: str):
        resp = self.session.post("/entity", json={"data": data}, timeout=5)
        if resp.status_code != 201:
            raise NOT_CREATED
        return resp

    def check_exist(self, uuid, expected_data: str):
        resp = self.session.get(f"/entity/{uuid}", timeout=5)
        if (resp.status_code != 200) or (resp.json()["data"] != expected_data):
            raise NOT_CREATED

    def check_filter(self, data: str):
        s_resp = self.session.get("/entities", params={"filter": f"{data}*"}, timeout=10)
        if (s_resp.status_code != 200) or (not s_resp.json()):
            raise NOT_FOUND
        for ent in s_resp.json():
            if not ent["data"].startswith(data):
                raise INVALID_FILTER

    def delete(self, uuid):
        d_resp = self.session.delete(f"/entity/{uuid}", timeout=5)
        if d_resp.status_code != 200:
            raise NOT_DELETED

    def check_deleted(self, uuid):
        g2_resp = self.session.get(f"/entity/{uuid}", timeout=2)
        if g2_resp.status_code != 404:
            raise NOT_DELETED

    def test(self):
        """Validate if server works correctly"""
        rand_data = _rand_str()
        try:
            with Timer() as timer:
                entity_uuid = self.create(rand_data).json()["uuid"]
                self.check_exist(entity_uuid, rand_data)
                self.check_filter(rand_data)
                self.delete(entity_uuid)
                self.check_deleted(entity_uuid)
        except ClientException as err:
            return str(err), timer.elapsed_ms
        return "ok", timer.elapsed_ms


def check_and_report(client: Client):
    result, elapsed = EntityClient(client.url).test()
    collection = MetricCollection()
    metric = Metric(CE_RESULT)
    metric.add_value("elapsed", elapsed)
    metric.add_tag("client", client.host_name)
    metric.add_tag("result", result)
    collection.append(metric)
    client.report_metric(collection)


def main():
    args, _ = AGP_RDS_MONITOR.parse_known_args()
    _client = Client(args.target, args.telegraf)
    while True:
        Thread(target=check_and_report, args=(_client,)).start()
        time.sleep(1)


if __name__ == "__main__":
    main()
