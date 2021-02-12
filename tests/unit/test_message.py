import unittest
from unittest import mock

from csm_test_utils import message
from csm_test_utils.message import get_message

test_metrics = [
    message.Metric(
        environment='prod',
        zone='eu-de',
        name='lb_load',
        value=25,
        metric_type='ms',
        az='eu-de-01',
    )
]


class TestMessage(unittest.TestCase):
    def test_metric_serialize(self):
        for metric in test_metrics:
            msg = '%s\n' % metric.serialize()
            assert isinstance(msg, str), f'{metric["name"]} at {metric["timestamp"]} not serialized'

    def test_metric_deserialize(self):
        metric = '{"name":"lb_load","environment":"prod",' \
                 '"zone":"eu-de","timestamp":"2021-02-12T11:27:11.157452",' \
                 '"__type":"metric","metric_type":"ms","value":25,"az":"eu-de-01"}'
        instance = get_message(metric)

        assert isinstance(instance, message.Metric), 'not deserialized'

    def test_push_message_to_socket(self):
        server_address = './comm_socket'
        with mock.patch('socket.socket'):
            for metric in test_metrics:
                res = message.push_metric(metric, server_address)
                assert res == 'success'


if __name__ == "__main__":
    unittest.main()
