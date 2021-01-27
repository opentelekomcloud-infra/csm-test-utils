import logging
import os


def logging_configuration():
    """Basic configuration for logging"""
    base_dir = '/tmp/rds'
    os.makedirs(base_dir, exist_ok=True)
    return logging.basicConfig(
        filename=f'{base_dir}/rds_logs.log',
        filemode='w',
        level=logging.DEBUG,
        format='%(levelname)s:%(asctime)s:%(message)s')


class BaseDB:
    """Base database class"""

    def __init__(self, connection: dict):
        self.connection = connection
        self.database = connection["database"]

    def _execute_sql(self, sql_query):
        raise NotImplementedError

    def get_database_size(self) -> int:
        raise NotImplementedError

    def is_database_fulfilled(self, db_max_size: int) -> bool:
        """Check if database size is more than maximum size"""
        return self.get_database_size() >= db_max_size

    def run_test(self, src_file: str):
        raise NotImplementedError
