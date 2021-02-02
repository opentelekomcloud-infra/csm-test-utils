from sqlalchemy import engine
from sqlalchemy.orm import sessionmaker


def get_session(db_engine: engine):
    """Create session object"""
    return sessionmaker(db_engine)()
