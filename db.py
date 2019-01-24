import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.serializer import loads, dumps
import sqlalchemy_utils
from sqlalchemy.orm import sessionmaker
import os

host = os.environ.get("fwdbhost")
user = os.environ.get("fwdbuser")
password = os.environ.get("fwdbpass")
port = os.environ.get("fwdbport")

warehouse_conn_str = f"mssql+pymssql://{user}:{password}@{host}:{port}/Warehouse"
warehouse_engine = sql.create_engine(warehouse_conn_str)

staging_conn_str = f"mssql+pymssql://{user}:{password}@{host}:{port}/Staging"
staging_engine = sql.create_engine(staging_conn_str)

Session = sessionmaker(bind=warehouse_engine, autoflush=True)

StagingSession = sessionmaker(bind=staging_engine, autoflush=True)

WarehouseBase = declarative_base(bind=warehouse_engine)

StagingBase = declarative_base(bind=staging_engine)


class BaseTable(object):
    id = 1

    def __repr__(self):
        return f"<ID: {self.id}>"


class Business(WarehouseBase, BaseTable):
    __tablename__ = "Google_Businesses"
    id = sql.Column("id", sqlalchemy_utils.UUIDType(binary=True), primary_key=True)
    address = sql.Column("formatted_address", sql.VARCHAR)
    name = sql.Column("name", sql.VARCHAR)
    assigned = sql.Column("assigned", sql.Boolean)
    edited = sql.Column("Edited", sql.Boolean)
    priority = sql.Column("priority", sql.Integer)
    editor = sql.Column("editor", sql.VARCHAR)

    def handle_type(self, attr):
        if hasattr(getattr(self, attr), "hex"):
            return getattr(getattr(self, attr), "hex")
        else:
            return getattr(self, attr)

    def to_json(self):
        return {
            name: self.handle_type(name)
            for name in ["id", "address", "name", "edited", "priority", "assigned"]
        }

class FleetComplete(StagingBase):
    __tablename__ = 'FleetComplete'
    id = sql.Column('recordID', sql.Integer, primary_key=True)
    lat = sql.Column('Lat', sql.Float)
    long = sql.Column('Long', sql.Float)
    status = sql.Column('DutyStatus', sql.VARCHAR)