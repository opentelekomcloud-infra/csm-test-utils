from argparse import ArgumentParser, Namespace

from .pg2.db_methods import Pg2DB
from .sqla.db_methods import AlchemyDB
from csm_test_utils.common import base_parser, sub_parsers

AGP = sub_parsers.add_parser("rds_backup_generate_data", add_help=False, parents=[base_parser])
AGP.add_argument('--run_option', dest='run_option', required=True, choices=['pg2', 'sqla'])
AGP.add_argument('--source', required=True)
AGP.add_argument('--host', required=True)
AGP.add_argument('--port', required=True)
AGP.add_argument('--database', '-db', default='entities')
AGP.add_argument('--username', '-user', required=True)
AGP.add_argument('--password', '-pass', required=True)
AGP.add_argument('--drivername', default='postgresql+psycopg2')


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
    args, _ = AGP.parse_known_args()
    connection = get_connection_dict(args)
    db = DB_DICT[args.run_option](connection)
    db.run_test(args.source)
