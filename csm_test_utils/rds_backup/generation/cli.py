from argparse import Namespace

from .pg2.db_methods import Pg2DB
from .sqla.db_methods import AlchemyDB
from ...parsers import AGP_RDS_GENERATE


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
    'pg2': Pg2DB,
    'sqla': AlchemyDB
}


def main():
    """Main function for getting connection to database and running test"""
    args, _ = AGP_RDS_GENERATE.parse_known_args()
    connection = get_connection_dict(args)
    db = DB_DICT[args.run_option](connection)
    db.run_test(args.source)
