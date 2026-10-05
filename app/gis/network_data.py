import os
import json
from typing import Dict, List, Any, Optional

class TransitGISNetwork:
    def __init__(self, data_path: Optional[str] = None):
        if not data_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_path = os.path.join(base_dir, "data", "transit_network.json")
        self.data_path = data_path
        self.data: Dict[str, Any] = {}
        self.stations_by_id: Dict[str, Dict[str, Any]] = {}
        self.lines_by_id: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
                for st in self.data.get("stations", []):
                    self.stations_by_id[st["id"]] = st
                for ln in self.data.get("lines", []):
                    self.lines_by_id[ln["id"]] = ln

    def get_all_stations(self) -> List[Dict[str, Any]]:
        return self.data.get("stations", [])

    def get_all_lines(self) -> List[Dict[str, Any]]:
        return self.data.get("lines", [])

    def get_station_by_id(self, station_id: str) -> Optional[Dict[str, Any]]:
        return self.stations_by_id.get(station_id)

    def get_line_by_id(self, line_id: str) -> Optional[Dict[str, Any]]:
        return self.lines_by_id.get(line_id)

    def get_geojson(self) -> Dict[str, Any]:
        """
        Returns complete transit network as GeoJSON FeatureCollection
        """
        features = []
        # Add Stations as Points
        for st in self.get_all_stations():
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [st["lng"], st["lat"]]
                },
                "properties": {
                    "id": st["id"],
                    "name": st["name"],
                    "type": "station",
                    "modes": st["modes"],
                    "is_interchange": st["is_interchange"],
                    "zone": st.get("zone", "Zone 1")
                }
            })

        # Add Lines as LineStrings
        for ln in self.get_all_lines():
            # In GeoJSON coordinates are [longitude, latitude]
            coords = [[pt[1], pt[0]] for pt in ln["coordinates"]]
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                },
                "properties": {
                    "id": ln["id"],
                    "name": ln["name"],
                    "type": "line",
                    "mode": ln["mode"],
                    "color": ln["color"],
                    "stations": ln["stations"]
                }
            })

        return {
            "type": "FeatureCollection",
            "features": features
        }

# Global singleton
gis_network = TransitGISNetwork()
