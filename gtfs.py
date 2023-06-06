import pandas as pd
import geopandas as gpd
import json
import gpxpy
import gpxpy.gpx
from shapely.geometry import LineString, Point
import os
import sys

def read_gtfs_files(gtfs_folder):
    stops = pd.read_csv(f"{gtfs_folder}/stops.txt")
    shapes = pd.read_csv(f"{gtfs_folder}/shapes.txt")
    stop_times = pd.read_csv(f"{gtfs_folder}/stop_times.txt")
    trips = pd.read_csv(f"{gtfs_folder}/trips.txt")
    return stops, shapes, stop_times, trips

def create_linestring(group):
    lats = group["shape_pt_lat"].tolist()
    lons = group["shape_pt_lon"].tolist()
    coords = [(lon, lat) for lat, lon in zip(lats, lons)]
    linestring = LineString(coords)
    return group["shape_id"].iloc[0], linestring

gtfs_folder = sys.argv[1]
stops, shapes, stop_times, trips = read_gtfs_files(gtfs_folder)
grouped_shapes = shapes.groupby("shape_id")
shape_ids, linestrings = zip(*grouped_shapes.apply(create_linestring))
gdf = gpd.GeoDataFrame({"shape_id": shape_ids, "geometry": linestrings})

if not os.path.exists("./gpx"):
    os.makedirs("./gpx")

for shape_id, linestring in zip(shape_ids, linestrings):
    gpx = gpxpy.gpx.GPX()

    # Create a new track in the GPX
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create a new segment in the track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Add points to the segment:
    for point in linestring.coords:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(point[1], point[0]))

    trips_for_shape = trips[trips["shape_id"] == shape_id]
    stop_times_for_shape = stop_times[stop_times["trip_id"].isin(trips_for_shape["trip_id"])]
    stops_for_shape = stops[stops["stop_id"].isin(stop_times_for_shape["stop_id"])]

    for i, row in stops_for_shape.iterrows():
        gpx_wpt = gpxpy.gpx.GPXWaypoint(row["stop_lat"], row["stop_lon"], name=row["stop_name"], description=f"Stop ID: {row['stop_id']}")
        gpx.waypoints.append(gpx_wpt)

    # Save the GPX file:
    with open(f"./gpx/{shape_id}.gpx", "w") as f:
        f.write(gpx.to_xml())
#style