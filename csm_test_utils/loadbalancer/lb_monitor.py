import logging
import socket
from time import sleep

import requests
from ocomone.logging import setup_logger

from ..message import push_metric, Metric
from ..parsers import AGP_LB_LOAD

LB_TIMING = 'csm_lb_timings'
LB_TIMEOUT = 'csm_lb_timeout'

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

INSTANCES_AZ = {
    'lb-monitoring-instance0-prod': 'eu-de-01',
    'lb-monitoring-instance1-prod': 'eu-de-02',
    'lb-monitoring-instance2-prod': 'eu-de-03',
}


def main():
    args, _ = AGP_LB_LOAD.parse_known_args()
    setup_logger(LOGGER, 'lb_load', log_dir=args.log_dir, log_format='[%(asctime)s] %(message)s')
    timeout = 20
    metrics = []
    for _ in range(9):
        try:
            res = requests.get(args.target, headers={'Connection': 'close'}, timeout=timeout)
        except requests.Timeout as ex:
            LOGGER.exception('Timeout sending request to LB')
            metrics.append(Metric(
                environment=args.environment,
                zone=args.zone,
                name=LB_TIMEOUT,
                value=timeout * 1000,

                metric_attrs={
                    'metric_type': 'ms',
                    'client': socket.gethostname(),
                    'exception': ex,
                })
            )
        else:
            metrics.append(Metric(
                environment=args.environment,
                zone=args.zone,
                name=LB_TIMING,
                value=int(res.elapsed.microseconds / 1000),
                metric_attrs={
                    'metric_type': 'ms',
                    'client': socket.gethostname(),
                    'server': res.headers['Server'],
                    'az': INSTANCES_AZ.get(res.headers['Server']),
                })
            )
        sleep(2)
    for metric in metrics:
        push_metric(metric, args.socket)


if __name__ == '__main__':
    main()
