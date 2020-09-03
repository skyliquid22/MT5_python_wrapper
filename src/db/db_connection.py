from configparser import ConfigParser

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.ext.declarative import declarative_base

import pandas as pd

# Declarative base class for mapping
Base = declarative_base()


class DBConnector:

    def __init__(self, **kwargs):
        """
        :param filename: (str) default: 'database.ini'
        :param section: (str) default: 'postgresql'
        """
        self.params = self.config(**kwargs)
        engine_string = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}".format(
            user=self.params['user'],
            password=self.params['password'],
            host=self.params['host'],
            port=self.params['port'],
            database=self.params['database'],
        )
        self.engine = create_engine(engine_string)
        self.cur = None
        self.conn = None

    def get_df_from_table(self, table_name, **kwargs):
        """ Return a pandas DataFrame of the DB table """
        with self.engine.connect() as conn:
            return pd.read_sql_table(table_name, conn, **kwargs)

    def get_df_from_query(self, query, **kwargs):
        """ Return a pandas DataFrame from query """
        with self.engine.connect() as conn:
            return pd.read_sql_query(query, conn, **kwargs)

    def execute_query(self, query):
        """ Send and executes query to DB"""
        with self.engine.connect() as conn:
            conn.execute(query)

    def create_table(self):

        meta = MetaData()
        mt5_return_codes = Table(
            'mt5_return_codes', meta,
            Column('id', Integer, primary_key=True),
            Column('Constant', String),
            Column('Description', String)
        )
        meta.create_all(self.engine)

    @staticmethod
    def config(filename='src/db/database.ini', section='postgresql'):
        # create parser
        parser = ConfigParser()
        # read config file
        parser.read(filename)

        # get section, default to postgresql
        db = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db[param[0]] = param[1]
        else:
            raise Exception('Section {0} not found in the {1} file'.format(section, filename))

        return db


class Mt5Codes(Base):
    __tablename__ = 'mt5_return_codes'

    id = Column('id', Integer, primary_key=True),
    Constant = Column('Constant', String),
    Description = Column('Description', String)

    def __repr__(self):
        return "<mt5_return_codes(Constant='%s', Description='%s')>" % (
            self.Constant, self.Description)

def create_tables():
    Mt5Codes.__table__
