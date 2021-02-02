import os
import random
import string
import time
import unittest
from contextlib import closing

import psycopg2
import yaml
from docker import from_env
from docker.models.containers import Container

from csm_test_utils.parsers import AGP_RDS_GENERATE
from csm_test_utils.rds_backup.generation.cli import DB_DICT, get_connection_dict

POSTGRES_IMAGE = 'postgres:10'
POSTGRES_ADDRESS = 'postgres:5432'
DB_CONFIG_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'rds_test_config.yaml'))


def find_db_max_size():
    with open(DB_CONFIG_FILE) as data_file:
        data = yaml.safe_load(data_file)
    return data['max_size_in_bytes']


def _rand_short_str():
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(6))


def _arg_dict_to_list(args: dict):
    return sum([[f'{k}', f'{v}'] for k, v in args.items()], [])


class TestRDS(unittest.TestCase):
    container: Container
    common_arg_dict: dict
    src_file: str
    db_name: str

    @classmethod
    def _direct_connection(cls):
        return {
            'host': cls.common_arg_dict['--host'],
            'port': cls.common_arg_dict['--port'],
            'user': cls.common_arg_dict['--username'],
            'password': cls.common_arg_dict['--password'],
        }

    @classmethod
    def _pg_wait(cls):
        connection = cls._direct_connection()
        timeout = 60
        start_time = time.monotonic()
        end_time = start_time + timeout
        while time.monotonic() < end_time:
            try:
                psycopg2.connect(**connection)
            except psycopg2.OperationalError:
                time.sleep(.5)
                continue
            time_passed = time.monotonic() - start_time
            print('Postgres is up in', round(time_passed, 3), 'seconds')
            return
        raise TimeoutError(f'Postgres is not up after {timeout} seconds')

    @classmethod
    def setUpClass(cls) -> None:
        host, port = POSTGRES_ADDRESS.split(':')
        port = int(port)
        postgres_username = 'postgres'
        postgres_password = 'Nezhachto!2020'

        cls.container = from_env().containers.run(
            POSTGRES_IMAGE,
            detach=True,
            hostname=host,
            name='postgres',
            ports={
                f'{port}/tcp': port
            },
            environment={
                'POSTGRES_USER': postgres_username,
                'POSTGRES_PASSWORD': postgres_password,
            }
        )

        cls.common_arg_dict = {
            '--host': 'localhost',
            '--port': port,
            '--username': postgres_username,
            '--password': postgres_password,
            '--source': DB_CONFIG_FILE,
        }

        cls._pg_wait()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.container.remove(force=True)

    def setUp(self) -> None:
        self.db_name = _rand_short_str()

        conn = {'dbname': 'postgres', **self._direct_connection()}
        with closing(psycopg2.connect(**conn)) as connection:
            connection.autocommit = True
            with connection.cursor() as cur:
                cur.execute(f'create DATABASE {self.db_name}')

    def tearDown(self) -> None:
        conn = {'dbname': 'postgres', **self._direct_connection()}
        with closing(psycopg2.connect(**conn)) as connection:
            connection.autocommit = True
            with connection.cursor() as cur:
                cur.execute('select pg_terminate_backend(pid) '
                            'from pg_stat_activity '
                            f'where pg_stat_activity.datname = \'{self.db_name}\'')
            with connection.cursor() as cur:
                cur.execute(f'drop DATABASE {self.db_name}')

    def _db_run(self, option):
        args_dict = {
            '--run_option': option,
            '--database': self.db_name,
            **self.common_arg_dict
        }
        try:
            args, _ = AGP_RDS_GENERATE.parse_known_args(_arg_dict_to_list(args_dict))
        except SystemExit as sys_ex:
            raise AssertionError('Failed to parse arguments') from sys_ex
        connection = get_connection_dict(args)
        db = DB_DICT[option](connection)
        db.run_test(args.source)
        self.assertTrue(db.is_database_fulfilled(db_max_size=find_db_max_size()))

    def test_pg2(self):
        self._db_run('pg2')

    def test_alchemy(self):
        self._db_run('sqla')
