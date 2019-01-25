import sqlalchemy as sql

import responder
import json, simplejson
from shapely.geometry import shape
from sqlalchemy import text
from db import (
    Session,
    StagingSession,
    Business,
    FleetComplete,
    warehouse_engine,
    staging_engine,
)
from datetime import datetime


router = responder.API(
    title="GeoFencing Editor",
    templates_dir="frontend/templates",
    static_dir="frontend",
)

# Render the main template to the client on page load.
@router.route("/")
async def main(req, resp):
    resp.content = router.template("main.html")


@router.route("/documentation")
async def main(req, resp):
    resp.content = router.template("documentation.html")


# Take requests from the user with a polygon bounding box, and return all results from
# Location and LocationEdits that intesect the polygon, in a GeoJson FeatureCollection.
@router.route("/api/stagedpolys")
async def update_content(req, resp):
    session = Session()
    body = await req.media()
    poly_bound = body.get("polybound")
    features = session.execute(
        f"""
        SELECT LocationID, NameBrand, StoreID, Warehouse.dbo.geography2json(ShapeGeo) as geometry, timestamp, Address, 'Production' as Status
        FROM Warehouse.dbo.Location
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


# Handle incoming edits from the client. Writes to both LocationEdits and Business tables
@router.route("/api/edits")
async def receive_edits(req, resp):
    session = Session()
    body = await req.media()
    geojson = body.get("geojson")
    props = geojson.get("properties")
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
    INSERT INTO Warehouse.dbo.[LocationEdits] ("LocationID", "NameBrand", "Name", "Address", "GeoEditDate", "ShapeGeo") VALUES 
        (
            @uuid2,
            '{props.get('NameBrand').replace("'","")}',
            '{props.get('Name').replace("'","")}',
            '{props.get('Address').replace("'","")}',
            '{datetime.now().date().isoformat()}',
            geography::STGeomFromText('{s.wkt}', 4326) 
        )
    END
    """
    session.execute(text(exec_str))
    session.query(Business).filter(Business.id == props.get("id")).update(
        {"edited": True, 'editor': body.get('editor')}
    )
    session.commit()
    resp.media = {"success": True}
    session.close()


# Handle an incoming request to get the top priority geofencing needs.
@router.route("/api/workflow")
async def call_addresses(req, resp):
    session = Session()
    resp.media = [
        item.to_json()
        for item in session.query(Business)
        .filter(Business.assigned == False, Business.edited == False)
        .order_by(Business.priority.desc())
        .limit(50)
    ]
    session.close()


# Endpoint to handle task assignment.
@router.route("/api/assignments/{op}")
async def poster(req, resp, op):
    opmapper = {"assign": True, "drop": False}
    session = Session()
    params = await req.media()
    id = params.get("id")
    if opmapper.get(op) is not None and id is not None:
        session.query(Business).filter(Business.id == id).update(
            {
                "assigned": opmapper.get(op),
                "editor": params.get("editor") if op == "assign" else None,
            }
        )
        resp.media = {"success": True}
    else:
        resp.media = {"success": False}
    session.close()


def validate_latlng(val, key):
    max_bounds = {"lat":{"min": -90.0, "max": 90.0}, "long":{"min":-180.0, "max":180.0}}
    print(max_bounds[key])
    try:
        result = float(val)
        if max_bounds[key]['min'] <= result <= max_bounds[key]['max']:
            print("passing")
            # print(max_bounds[key]["min"])
            # print(max_bounds[key]['max'])
            # print(key, val)
            # print(result)
    except:
        result = None
    return result


@router.route("/api/pings")
async def return_pings(req, resp):
    session = StagingSession()
    required_bounds = ["minlat", "maxlat", "minlong", "maxlong"]
    bbox = {key: validate_latlng(req.params.get(key), key[3:]) for key in required_bounds}
    for key in required_bounds:
        if bbox.get(key) is None:
            raise ValueError("Bad Input")
    res = (
        session.query(FleetComplete.lat, FleetComplete.long)
        .filter(
            FleetComplete.lat.between(bbox.get("minlat"), bbox.get("maxlat")),
            FleetComplete.long.between(bbox.get("minlong"), bbox.get("maxlong")),
            FleetComplete.status == "OF",
        )
        .all()
    )
    resp.media = [item._asdict() for item in res]
    session.close()
