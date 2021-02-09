import datetime
import json
import logging
import socket

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class Base(dict):
    """Base metric class"""

    def __init__(
        self, name: str,
        environment: str,
        zone: str,
        timestamp: str = None
    ):
        super(Base, self).__init__()
        self['name'] = name
        self['environment'] = environment
        self['zone'] = zone
        if timestamp:
            self['timestamp'] = timestamp
        else:
            self['timestamp'] = datetime.datetime.now().isoformat()

    def serialize(self):
        """Serialize data as json string"""
        try:
            return json.dumps(self, separators=(',', ':'))
        except json.JSONDecodeError:
            return

    def __bytes__(self) -> bytes:
        """Returns bytes interpretation of data"""
        data = self.serialize()
        return ('%s\n' % data).encode('utf8')


class Metric(Base):
    """Base metric"""

    def __init__(
        self,
        name: str, value: int,
        metric_type: str,
        environment: str = None,
        zone: str = None,
        **kwargs: dict
    ):
        super(Metric, self).__init__(
            name=name,
            environment=environment,
            zone=zone,
        )
        self['__type'] = 'metric'
        self['metric_type'] = metric_type
        self['value'] = value
        self.update(**kwargs)


def get_message(msg):
    """Get metric instance from dictionary or string"""
    if not isinstance(msg, dict):
        try:
            msg = json.loads(msg, encoding='utf-8')
        except json.JSONDecodeError:
            return None
    typ = msg.pop('__type')
    if typ == 'metric':
        return Metric(**msg)


def push_metric(data: Metric, message_socket_address=None):
    """push metrics to socket"""
    if message_socket_address:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as _socket:
            try:
                _socket.connect(message_socket_address)
                msg = '%s\n' % data.serialize()
                _socket.sendall(msg.encode('utf8'))
                return 'success'
            except socket.error as ex:
                LOGGER.exception('Error establising connection to socket')
                raise
            except Exception as e:
                LOGGER.exception('Error writing message to socket')
                raise
