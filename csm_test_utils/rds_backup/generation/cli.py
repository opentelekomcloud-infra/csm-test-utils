from argparse import ArgumentParser, Namespace

from .pg2.db_methods import Pg2DB
from .sqla.db_methods import AlchemyDB


def parse_args(args: list = None):
    """Parse common parameters"""
    parser = ArgumentParser(prog='customer-service-monitoring',
                            description='Get data for connection string')
    parser.add_argument('--run_option', dest='run_option', required=True, choices=['pg2', 'sqla'])
    parser.add_argument('--source', required=True)
    parser.add_argument('--host', required=True)
    parser.add_argument('--port', required=True)
    parser.add_argument('--database', '-db', default='entities')
    parser.add_argument('--username', '-user', required=True)
    parser.add_argument('--password', '-pass', required=True)
    parser.add_argument('--drivername', default='postgresql+psycopg2')
    return parser.parse_known_args(args)


def get_connection_dict(args: Namespace) -> dict:
    """Create connection dict"""
    db_connect = {
        'host': args.host,
        'port': args.port,
        'password': args.password,
        'database': args.database
    }
    if args.run_option == 'pg2':
        db_connect['user'] = args.username
    if args.run_option == 'sqla':
        db_connect['username'] = args.username
        db_connect['drivername'] = args.drivername
    return db_connect


DB_DICT = {
    "pg2": Pg2DB,
    "sqla": AlchemyDB
}


def main():
    args, _ = parse_args()
    connection = get_connection_dict(args)
    db = DB_DICT[args.run_option](connection)
    db.run_test(args.source)
