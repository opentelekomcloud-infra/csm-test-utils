"""Check if server is working"""

import random
import string
import time
from threading import Thread

from influx_line_protocol import Metric, MetricCollection
from ocomone.session import BaseUrlSession
from ocomone.timer import Timer
from requests import Response

from .common import Client, base_parser, sub_parsers


def _rand_str():
    return "".join(random.choice(string.ascii_letters) for _ in range(10))


CE_RESULT = "ce_result"


def check_server(session):
    """Validate if server works correctly"""
    rand_data = _rand_str()
    with Timer() as timer:
        cr_resp = session.post("/entity", json={"data": rand_data}, timeout=5)
        if cr_resp.status_code != 201:
            return "not_created", timer.elapsed_ms

        entity_uuid = cr_resp.json()["uuid"]
        g_resp = session.get(f"/entity/{entity_uuid}", timeout=5)
        if (g_resp.status_code != 200) or (g_resp.json()["data"] != rand_data):
            return "not_created", timer.elapsed_ms

        s_resp = session.get(f"/entities?filter={rand_data}*", timeout=10)  # type: Response
        not_found = "not_found", timer.elapsed_ms
        if s_resp.status_code != 200:
            return not_found
        if not s_resp.json():
            return not_found
        for ent in s_resp.json():
            if not ent["data"].startswith(rand_data):
                return "invalid_filter", not_found[1]

        d_resp = session.delete(f"/entity/{entity_uuid}", timeout=5)
        if d_resp.status_code != 200:
            return "not_deleted", timer.elapsed_ms
        g2_resp = session.get(f"/entity/{entity_uuid}", timeout=2)
        if g2_resp.status_code != 404:
            return "not_deleted", timer.elapsed_ms

    return "ok", timer.elapsed_ms


def check_and_report(client: Client):
    session = BaseUrlSession(client.url)
    result, elapsed = check_server(session)
    collection = MetricCollection()
    metric = Metric(CE_RESULT)
    metric.add_value("elapsed", elapsed)
    metric.add_tag("client", client.host_name)
    metric.add_tag("result", result)
    collection.append(metric)
    client.report_metric(collection)


AGP = sub_parsers.add_parser("rds_monitor", add_help=False, parents=[base_parser])


def main():
    args, _ = AGP.parse_known_args()
    _client = Client(args.target, args.telegraf)
    while True:
        Thread(target=check_and_report, args=(_client,)).start()
        time.sleep(1)


if __name__ == "__main__":
    main()
