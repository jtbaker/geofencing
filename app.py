import sqlalchemy as sql
import geoalchemy2 as gsql
from geoalchemy2 import func

import responder
import json, simplejson
from shapely.geometry import shape
from sqlalchemy import text
from db import Session, engine
from datetime import datetime

router = responder.API(
    title="GeoFencing Editor",
    templates_dir="frontend/templates",
    static_dir="frontend/js",
)


@router.route("/")
async def main(req, resp):
    resp.content = router.template("main.html")


@router.route("/api/stagedpolys")
async def update_content(req, resp):
    session = Session()
    body = await req.media()
    poly_bound = body.get("polybound")
    features = session.execute(
        f"""
        SELECT t.*, Location.NameBrand FROM
            ((SELECT POLYGONID, timestamp, Warehouse.dbo.geometry2json(GeoPolygon) as "geometry", latitude, longitude, 'Staged' as [Status]
            FROM Warehouse.dbo.JASON_TESTING
            WHERE geometry::STGeomFromText('{poly_bound}', 4326).STContains(GeoPolygon)=1 AND GeoPolygon.STGeometryType()='POLYGON'
            UNION 
            SELECT POLYGONID, timestamp, Warehouse.dbo.geography2json(GeoPolygon), [lat], [long], [Status] FROM
            (SELECT POLYGONID, timestamp, GeoPolygon, [lat], [long], 'Production' as [Status], ROW_NUMBER() OVER (PARTITION BY [POLYGONID] ORDER BY [POLYGONID]) as rn
            FROM
            Warehouse.dbo.PolygonMatch
            WHERE geography::STGeomFromText('{poly_bound}', 4326).STContains(GeoPolygon)=1 AND GeoPolygon.STGeometryType()='POLYGON'
            ) as r where r.rn=1) 
            )
            as t 
        LEFT JOIN Warehouse.dbo.Location ON t.POLYGONID = Location.LocationID"""
    ).fetchall()
    collection = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": json.loads(item.__getitem__("geometry")),
                "properties": {
                    "NameBrand": item.__getitem__("NameBrand").__str__(),
                    "Timestamp": item.__getitem__("timestamp").__str__(),
                    "Status": item.__getitem__("Status").__str__(),
                },
            }
            for item in features
        ],
    }
    resp.content = simplejson.dumps(collection)
    session.close()


@router.route("/api/edits")
async def receive_edits(req, resp):
    print(req)
    session = Session()
    body = await req.media()
    geojson = body.get("geojson")
    geometry = geojson.get("geometry")
    s = shape(geometry)
    print(geometry, type(geometry))
    # print(f"""geometry::STGeomFromText('{s.wkt}', 4326), '{datetime.now().date().isoformat()}', {s.centroid().y}, {s.centroid().x})""")
    with engine.connect() as conn:
        conn.execute(
            text(
                f"""INSERT INTO Warehouse.dbo.[JASON_TESTING] (GeoPolygon, timestamp, latitude, longitude) VALUES (
            geometry::STGeomFromText('{s.wkt}', 4326), '{datetime.now().date().isoformat()}', {s.centroid.y}, {s.centroid.x})"""
            )
        )
    session.close()
    resp.media = {"success": True}


# @router.route("/api/pushes")
# async def poster(req, resp):
#     session = Session()
#     body = await req.media()


if __name__ == "__main__":
    router.run(address="192.168.1.55")
