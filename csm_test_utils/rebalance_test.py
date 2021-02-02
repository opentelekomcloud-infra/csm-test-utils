import time

import requests
from influx_line_protocol import Metric, MetricCollection
from requests.exceptions import ConnectionError  # pylint: disable=redefined-builtin

from .common import Client
from .parsers import AGP_REBALANCE

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


def _check_timeout(msg, end_time):
    if time.monotonic() > end_time:
        raise TimeoutError(msg)


def main():
    """Find unavailable node and waits until it won't be used"""
    args, _ = AGP_REBALANCE.parse_known_args()
    client = Client(args.target, args.telegraf)

    # max number of consecutive successful requests to consider downtime finished
    max_success_count = 20

    success_count = 0
    end_time = time.monotonic() + float(args.timeout)
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
        _check_timeout(f"No re-balancing is done after {args.timeout} seconds.\n"
                       f"Nodes: {nodes}{exp_nodes}", end_time)
        time.sleep(0.5)
    print(f"LB rebalanced nodes: ({nodes})")


if __name__ == "__main__":
    main()
