"""Get cloud eye notifications and check that autoscaling is working"""

import requests
from flask import Flask, jsonify, request
from influx_line_protocol import Metric, MetricCollection

from .common import base_parser, sub_parsers

app = Flask("autoscaling_reports")

AS_RESULT = "as_result"


@app.route('/smn', methods=['POST'])
def smn():
    if request.method == 'POST':
        response = request.get_json()
        if response['subscribe_url']:
            requests.get(response['subscribe_url'])
        else:
            report(jsonify(response))
        return response


def report(response_body):
    time = response_body["message"]["alarmValue"][0]["time"]
    value = response_body["message"]["alarmValue"][0]["value"]
    status = response_body["message"]["alarm_status"]

    collection = MetricCollection()
    metric = Metric(AS_RESULT)
    metric.add_value("time", time)
    metric.add_value("value", value)
    metric.add_tag("status", status)
    collection.append(metric)
    res = requests.post(f"{args.telegraf}/telegraf", data=str(collection), timeout=2)
    assert res.status_code == 204, f"Status is {res.status_code}"


AGP = sub_parsers.add_parser("as_monitor", add_help=False, parents=[base_parser])
AGP.add_argument("--port", help="port to be listened", default=23456, type=int)
args, _ = AGP.parse_known_args()


def main():
    app.run(port=args.port, debug=True)


if __name__ == '__main__':
    main()
