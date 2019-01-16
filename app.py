import sqlalchemy as sql

import responder
import json, simplejson
from shapely.geometry import shape
from sqlalchemy import text
from db import Session, engine, Business
from datetime import datetime


router = responder.API(
    title="GeoFencing Editor",
    templates_dir="frontend/templates",
    static_dir="frontend/js"
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
        SELECT LocationID, NameBrand, StoreID, Warehouse.dbo.geography2json(ShapeGeo) as geometry, timestamp, Address, 'Production' as Status FROM Warehouse.dbo.Location
        WHERE ShapeGeo.STGeometryType()='POLYGON'
        AND ShapeGeo.STIntersects(geography::STGeomFromText('{poly_bound}',4326))=1
        UNION
        SELECT LocationID, NameBrand, StoreID,Warehouse.dbo.geography2json(ShapeGeo) as geometry, GeoEditDate, Address, 'Staged' as Status
        FROM Warehouse.dbo.LocationEdits
        WHERE ShapeGeo.STGeometryType()='POLYGON'
        AND ShapeGeo.STIntersects(geography::STGeomFromText('{poly_bound}',4326))=1"""
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
                    "Address": item.__getitem__("Address").__str__(),
                },
            }
            for item in features
        ],
    }
    resp.content = simplejson.dumps(collection)
    session.close()


@router.route("/api/edits")
async def receive_edits(req, resp):
    session = Session()
    body = await req.media()
    geojson = body.get("geojson")
    props = geojson.get("properties")
    print(props)
    geometry = geojson.get("geometry")
    s = shape(geometry)
    exec_str = f"""
    BEGIN
    DECLARE @uuid VARCHAR(50);
	DECLARE @uuid2 UNIQUEIDENTIFIER;
    SET @uuid = '{props.get('id')}';
    SET @uuid2 = CAST(SUBSTRING(@uuid, 1, 8) + '-' + SUBSTRING(@uuid, 9, 4) + '-' + SUBSTRING(@uuid, 13, 4) + '-' +
            SUBSTRING(@uuid, 17, 4) + '-' + SUBSTRING(@uuid, 21, 12)
            AS UNIQUEIDENTIFIER);
    INSERT INTO Warehouse.dbo.[LocationEdits] ("LocationID", "NameBrand", "Address", "GeoEditDate", "ShapeGeo") VALUES 
        (
            @uuid2,
            '{props.get('NameBrand').replace("'","")}',
            '{props.get('Address').replace("'","")}',
            '{datetime.now().date().isoformat()}',
            geography::STGeomFromText('{s.wkt}', 4326) 
        )
    COMMIT
    END
    """
    # print(exec_str)
    session.execute(text(exec_str))
    session.query(Business).filter(Business.id == props.get("id")).update(
        {"edited": True}
    )
    session.commit()
    resp.media = {"success": True}
    session.close()


@router.route("/api/workflow")
async def call_addresses(req, resp):
    session = Session()
    resp.media = [
        item.to_json()
        for item in session.query(Business)
        .filter(Business.assigned == False)
        .order_by(Business.priority.desc())
        .limit(50)
    ]
    session.close()


@router.route("/api/assignments/{op}")
async def poster(req, resp, op):
    opmapper = {"assign": True, "drop": False}
    session = Session()
    params = await req.media()
    id = params.get("id")
    if opmapper.get(op) is not None and id is not None:
        session.query(Business).filter(Business.id == id).update(
            {"assigned": opmapper.get(op),"editor": params.get('editor') if op == 'assign' else None}
        )
        resp.media = {"success": True}
    else:
        resp.media = {"success": False}
    session.close()


if __name__ == "__main__":
    router.run()
