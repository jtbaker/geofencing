import sqlalchemy as sql
import geoalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

host = os.environ.get("fwdbhost")
user = os.environ.get("fwdbuser")
password = os.environ.get("fwdbpass")
port = os.environ.get("fwdbport")

conn_str = f"mssql+pymssql://{user}:{password}@{host}:{port}/Warehouse"
engine = sql.create_engine(conn_str)

Session = sessionmaker(bind=engine, autoflush=True)

Base = declarative_base(bind=engine)

class Testing(Base):
    __tablename__ = "Jason_Testing"
    pk = sql.Column("pk", sql.Integer, primary_key=True)
    name = sql.Column("name", sql.Text)
    age = sql.Column("age", sql.Integer)
    geom = sql.Column("geom", geoalchemy.geometry.Geometry)
    latitude = sql.Column("latitude", sql.Numeric)
    longitude = sql.Column("longitude", sql.Numeric)