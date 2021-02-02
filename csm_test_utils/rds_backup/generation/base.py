import logging
import os

BASE_DIR = '/tmp/rds'
LOG_PATH = f'{BASE_DIR}/rds_log.log'


def logging_configuration():
    """Basic configuration for logging"""
    os.makedirs(BASE_DIR, exist_ok=True)
    return logging.basicConfig(
        filename=LOG_PATH,
        filemode='w',
        level=logging.DEBUG,
        format='%(levelname)s:%(asctime)s:%(message)s')


class BaseDB:
    """Base database class"""

    def __init__(self, connection: dict):
        self.connection = connection
        self.database = connection['database']

    def _execute_sql(self, sql_query):
        """Execute sql query"""
        raise NotImplementedError

    def get_database_size(self) -> int:
        """Get database size"""
        raise NotImplementedError

    def is_database_fulfilled(self, db_max_size: int) -> bool:
        """Check if database size is more than maximum size"""
        return self.get_database_size() >= db_max_size

    def run_test(self, src_file: str):
        """Fill database with a data"""
        raise NotImplementedError
