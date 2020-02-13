import time

import requests
from influx_line_protocol import Metric, MetricCollection
from requests.exceptions import ConnectionError

from .common import Client, base_parser, sub_parsers

LB_DOWNTIME = "lb_down"


def report(client: Client, ok, server=None):
    metrics = MetricCollection()
    lb_down = Metric(LB_DOWNTIME)
    lb_down.add_tag("ok", ok)
    if server is not None:
        lb_down.add_tag("server", server)
    lb_down.add_value("requests", 1)
    metrics.append(lb_down)
    client.report_metric(metrics)


AGP = sub_parsers.add_parser("rebalance", add_help=False, parents=[base_parser])
AGP.add_argument("--nodes", type=int, default=None, help="Expected number of nodes")


def main(timeout: float):
    """Find unavailable node and waits until it won't be used"""
    args, _ = AGP.parse_known_args()
    client = Client(args.target, args.telegraf)

    end_time = time.monotonic() + 3

    def _check_timeout(msg):
        if time.monotonic() > end_time:
            raise TimeoutError(msg)

    max_success_count = 20  # max number of consecutive successful requests to consider downtime finished
    success_count = 0
    end_time = time.monotonic() + timeout
    print("Started waiting for loadbalancer to re-balance nodes")
    nodes = set()

    if args.nodes is None:
        exp_nodes = ""

        def _should_continue():
            return success_count < max_success_count

    else:
        exp_nodes = f" ({args.nodes} expected)"

        def _should_continue():
            return len(nodes) < args.nodes

    while _should_continue():
        try:
            resp = requests.get(client.url, headers={"Connection": "close"}, timeout=1)
        except ConnectionError:  # one node is down
            success_count = 0
            report(client, ok=False)
        else:
            if resp.status_code == 200:
                server = resp.headers["Server"]
                success_count += 1
                nodes.add(server)
                report(client, ok=True, server=server)
        _check_timeout(f"No re-balancing is done after {timeout} seconds. Nodes: {nodes}{exp_nodes}")
        time.sleep(0.5)
    print(f"LB rebalanced nodes: ({nodes})")


if __name__ == "__main__":
    main(60)
