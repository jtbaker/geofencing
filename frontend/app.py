import sqlalchemy as sql
import geoalchemy2 as gsql
from geoalchemy2 import func
import responder
import os

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

host = os.environ.get('fwdbhost')
user = os.environ.get('fwdbuser')
password = os.environ.get('fwdbpass')
port = os.environ.get('fwdbport')

conn_str = f"mssql+pymssql://{user}:{password}@{host}:{port}/Warehouse"
engine = sql.create_engine(conn_str)

Session = sessionmaker(bind=engine)

Base = declarative_base(bind=engine)

class Testing(Base):
    __tablename__ = 'Jason_Testing'
    id = sql.Column('id', sql.Text, primary_key=True)
    name = sql.Column('name', sql.Text)
    age = sql.Column('age', sql.Integer)
    geom = gsql.Column('geom', gsql.Geometry)
    latitude = sql.Column('latitude', sql.Numeric)
    longitude = sql.Column('longitude', sql.Numeric)