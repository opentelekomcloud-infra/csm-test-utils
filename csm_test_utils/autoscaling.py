"""Get cloud eye notifications and check that autoscaling is working"""

import random
import string
import time
from threading import Thread

from influx_line_protocol import Metric, MetricCollection
from ocomone.session import BaseUrlSession
from flask import Flask, jsonify, request
import requests
from .common import Client, base_parser, sub_parsers


def _rand_str():
    return "".join(random.choice(string.ascii_letters) for _ in range(10))


AS_RESULT = "as_result"


@app.route('/smn', methods=['POST'])
def smn():
    if request.method == 'POST':
        response = request.get_json()
        try:
            subscribe = requests.get(response['subscribe_url'])
        except:
            print(response)
            return response.status_code


def check_and_report(client: Client):
    session = BaseUrlSession(client.url)
    result, elapsed = smn(session)

    collection = MetricCollection()
    metric = Metric(AS_RESULT)
    metric.add_value("elapsed", elapsed)
    metric.add_tag("result", result)
    collection.append(metric)
    client.report_metric(collection)


AGP = sub_parsers.add_parser("as_monitor", add_help=False, parents=[base_parser])


def main():
    args, _ = AGP.parse_known_args()
    _client = Client(args.target, args.telegraf)
    while True:
        Thread(target=check_and_report, args=(_client,)).start()
        time.sleep(0.2)


if __name__ == '__main__':
    main()
