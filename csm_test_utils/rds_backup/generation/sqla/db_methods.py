import logging
import random
import string
from contextlib import closing

import yaml
from psycopg2 import Error
from sqlalchemy import create_engine
from sqlalchemy.engine import url

from csm_test_utils.rds_backup.generation.base import BaseDB, logging_configuration
from .db_model import TestRdsTable
from .session import get_session

__all__ = ['AlchemyDB']


class AlchemyDB(BaseDB):
    """Postgres database instance"""

    def __init__(self, connection):
        super().__init__(connection)
        self.engine = create_engine(url.make_url(url.URL(**connection)), echo=False)

    def _execute_sql(self, sql_query):
        """Execute sql command which depends on db dialect"""
        try:
            with closing(self.engine.connect()) as connection:
                result = connection.execute(sql_query).fetchall()
        except Error:
            logging.exception('Error occurred')
        return result

    def get_database_size(self) -> int:
        return self._execute_sql(f"select pg_database_size('{self.database}');")[0][0]

    def run_test(self, src_file):
        logging_configuration()
        logging.info('Scripts starts')

        with open(src_file) as data_file:
            data = yaml.safe_load(data_file)
        content_str = _random_str(data['symbol_count'])
        session = get_session(self.engine)
        with closing(session):
            while not self.is_database_fulfilled(data['max_size_in_bytes']):
                TestRdsTable.metadata.create_all(self.engine)
                session.add_all([
                    TestRdsTable(content_str + str(i)) for i in range(data['record_count'])
                ])
                session.commit()
                logging.info('Commit session')
        logging.info('Script finished')


def _random_str(size) -> str:
    """Generate random string which consist of letters and digits."""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(size))
