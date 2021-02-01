import uuid

from sqlalchemy import BigInteger, Column, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TestRdsTable(Base):  # pylint: disable=too-few-public-methods
    """Class representing a model of database for ORM"""

    __tablename__ = str(uuid.uuid4())

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    content = Column(Text)

    def __init__(self, content):
        self.content = content

    def __repr__(self):
        return "<TestRds('%s','%s')>" % (self.id, self.content)
