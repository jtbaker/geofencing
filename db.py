import sqlalchemy as sql

# import geoalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.serializer import loads, dumps
import sqlalchemy_utils
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

# class Testing(Base):
#     __tablename__ = "Jason_Testing"
#     pk = sql.Column("pk", sql.Integer, primary_key=True)
#     name = sql.Column("name", sql.Text)
#     age = sql.Column("age", sql.Integer)
#     # geom = sql.Column("geom", geoalchemy.geometry.Geometry)
#     latitude = sql.Column("latitude", sql.Numeric)
#     longitude = sql.Column("longitude", sql.Numeric)
class BaseTable(object):
    id = 1

    def __repr__(self):
        return f"<ID: {self.id}>"


class Business(Base, BaseTable):
    __tablename__ = "Google_Businesses"
    id = sql.Column("id", sqlalchemy_utils.UUIDType(binary=True), primary_key=True)
    address = sql.Column("formatted_address", sql.VARCHAR)
    name = sql.Column("name", sql.VARCHAR)
    assigned = sql.Column('assigned', sql.Boolean)
    edited = sql.Column("Edited", sql.Boolean)
    priority = sql.Column("priority", sql.Integer)
    editor = sql.Column("editor", sql.VARCHAR)

    def handle_type(self, attr):
        if hasattr(getattr(self, attr), 'hex'):
            return getattr(getattr(self, attr), 'hex')
        else:
            return getattr(self, attr)
        

    def to_json(self):
        return {
            name: self.handle_type(name)
            for name in ["id", "address", "name", "edited", "priority","assigned"]
        }


session = Session()

res = session.query(Business).order_by(Business.priority).limit(2)
