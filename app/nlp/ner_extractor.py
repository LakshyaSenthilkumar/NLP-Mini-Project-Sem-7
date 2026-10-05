import re
import json
import os
from typing import Dict, List, Any, Optional, Tuple

class TransitNERExtractor:
    def __init__(self, network_data_path: Optional[str] = None):
        self.known_stations: Dict[str, Dict[str, Any]] = {}
        self.known_lines: Dict[str, Dict[str, Any]] = {}
        self._load_network(network_data_path)

    def _load_network(self, network_data_path: Optional[str] = None):
        if not network_data_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            network_data_path = os.path.join(base_dir, "data", "transit_network.json")

        if os.path.exists(network_data_path):
            try:
                with open(network_data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for st in data.get("stations", []):
                        self.known_stations[st["name"].lower()] = st
                        # Add aliases e.g. "Dadar", "CSMT", "Bandra", "Andheri", "Borivali"
                        main_name = st["name"].split("/")[0].split("(")[0].strip().lower()
                        self.known_stations[main_name] = st
                        if "csmt" in st["name"].lower():
                            self.known_stations["csmt"] = st
                            self.known_stations["vt"] = st
                            self.known_stations["cst"] = st
                        if "churchgate" in st["name"].lower():
                            self.known_stations["churchgate"] = st
                        if "bkc" in st["name"].lower():
                            self.known_stations["bkc"] = st
                            self.known_stations["bandra kurla complex"] = st
                        if "jacob circle" in st["name"].lower():
                            self.known_stations["jacob circle"] = st
                            self.known_stations["sant gadge maharaj chowk"] = st
                        if "weh" in st["name"].lower():
                            self.known_stations["weh"] = st
                            self.known_stations["western express highway"] = st

                    for line in data.get("lines", []):
                        self.known_lines[line["id"].lower()] = line
                        self.known_lines[line["name"].lower()] = line
                        
                        # Add common Mumbai Line aliases
                        if "western" in line["name"].lower():
                            self.known_lines["western line"] = line
                            self.known_lines["western railway"] = line
                            self.known_lines["wr"] = line
                        if "central" in line["name"].lower() and "main" in line["name"].lower():
                            self.known_lines["central line"] = line
                            self.known_lines["central railway"] = line
                            self.known_lines["cr"] = line
                            self.known_lines["main line"] = line
                        if "harbour" in line["name"].lower():
                            self.known_lines["harbour line"] = line
                            self.known_lines["harbor line"] = line
                        if "metro line 1" in line["name"].lower():
                            self.known_lines["metro line 1"] = line
                            self.known_lines["blue line metro"] = line
                            self.known_lines["versova ghatkopar metro"] = line
                            self.known_lines["metro 1"] = line
                        if "2a" in line["name"].lower():
                            self.known_lines["metro line 2a"] = line
                            self.known_lines["metro line 7"] = line
                            self.known_lines["yellow line metro"] = line
                        if "line 3" in line["name"].lower() or "aqua" in line["name"].lower():
                            self.known_lines["metro line 3"] = line
                            self.known_lines["aqua line"] = line
                            self.known_lines["underground metro"] = line
                        if "monorail" in line["name"].lower():
                            self.known_lines["monorail"] = line
                            self.known_lines["mumbai monorail"] = line
                        if "302" in line["name"].lower():
                            self.known_lines["best 302"] = line
                            self.known_lines["bus 302"] = line
                            self.known_lines["route 302"] = line
                        if "115" in line["name"].lower():
                            self.known_lines["best a115"] = line
                            self.known_lines["bus a115"] = line
                            self.known_lines["a115"] = line
                        if "105" in line["name"].lower():
                            self.known_lines["nmmt 105"] = line
                            self.known_lines["bus 105"] = line
                            self.known_lines["nmmt bus"] = line
            except Exception as e:
                print(f"Warning loading transit network: {e}")

    def extract(self, text: str) -> Dict[str, List[str]]:
        """
        Extracts Mumbai transit entities: stations, lines, directions, time mentions, aspects.
        """
        if not text:
            return {"stations": [], "lines": [], "directions": [], "time_mentions": [], "aspects": []}

        clean_text = text.lower()
        extracted_stations: List[str] = []
        extracted_lines: List[str] = []
        extracted_directions: List[str] = []
        extracted_time_mentions: List[str] = []
        extracted_aspects: List[str] = []

        # 1. Match Stations
        for name_key, st_obj in sorted(self.known_stations.items(), key=lambda x: len(x[0]), reverse=True):
            if len(name_key) >= 3 and re.search(r'\b' + re.escape(name_key) + r'\b', clean_text):
                if st_obj["name"] not in extracted_stations:
                    extracted_stations.append(st_obj["name"])

        # Fallback Station Regex pattern
        st_regexes = [
            r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+(?:Station|Terminus|Junction|Hub|Bridge|Pier|Circle|Chowk|Park|Gate))',
            r'(at\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*))'
        ]
        for rgx in st_regexes:
            matches = re.findall(rgx, text)
            for m in matches:
                candidate = m if isinstance(m, str) else m[0]
                candidate = candidate.replace("at ", "").strip()
                if len(candidate) > 3 and candidate not in extracted_stations and candidate.lower() not in ["the local", "my train", "our bus", "this metro"]:
                    if any(kw in candidate.lower() for kw in ["station", "terminus", "junction", "circle", "chowk", "road", "suburb", "nagar", "complex"]):
                        extracted_stations.append(candidate)

        # 2. Match Lines / Routes (Train, Metro, Monorail, Bus)
        line_patterns = [
            (r'\b(western\s*line|central\s*line|harbour\s*line|harbor\s*line)\b', "Train"),
            (r'\b(metro\s*(?:line\s*)?[0-9a-zA-Z]+|aqua\s*line|blue\s*line|yellow\s*line)\b', "Metro"),
            (r'\b(mumbai\s*monorail|monorail)\b', "Monorail"),
            (r'\b(best\s*(?:bus\s*)?[a-zA-Z0-9\-]+|nmmt\s*(?:bus\s*)?[a-zA-Z0-9\-]+|bus\s*(?:#|\s*)?[0-9]{1,4}[a-zA-Z]?)\b', "Bus"),
            (r'\b(ac\s*local|fast\s*local|slow\s*local|local\s*train)\b', "Train")
        ]
        for pattern, mode_hint in line_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                matched_str = match.group(0).strip()
                if matched_str.title() not in extracted_lines:
                    extracted_lines.append(matched_str.title())

        # Check known lines database
        for line_key, line_obj in self.known_lines.items():
            if re.search(r'\b' + re.escape(line_key) + r'\b', clean_text):
                if line_obj["name"] not in extracted_lines:
                    extracted_lines.append(line_obj["name"])

        # 3. Directions (Mumbai transit headings)
        direction_keywords = [
            "churchgate-bound", "csmt-bound", "virar-bound", "borivali-bound",
            "kalyan-bound", "thane-bound", "panvel-bound", "vashi-bound",
            "andheri-bound", "ghatkopar-bound", "versova-bound", "bkc-bound",
            "up line", "down line", "fast line", "slow line", "towards", "heading to"
        ]
        for dk in direction_keywords:
            if dk in clean_text:
                extracted_directions.append(dk.title())

        # 4. Time Mentions
        time_patterns = [
            r'\b(?:[01]?[0-9]|2[0-3]):[0-5][0-9]\s*(?:am|pm|AM|PM)?\b',
            r'\b(?:[1-9]|1[0-2])\s*(?:am|pm|AM|PM)\b',
            r'\b(?:morning|evening|afternoon|night)\s*rush\b',
            r'\b(?:rush\s*hour|peak\s*hour|late\s*night|midnight|mega\s*block|early\s*morning)\b',
            r'\b(?:today|yesterday|this\s*morning|tonight)\b'
        ]
        for tp in time_patterns:
            matches = re.findall(tp, text, re.IGNORECASE)
            for m in matches:
                if m not in extracted_time_mentions:
                    extracted_time_mentions.append(m)

        # 5. Mumbai Transit Aspects / Components
        aspect_keywords = [
            "fob", "foot over bridge", "uts app", "chalo card", "smart card",
            "ladies coach", "first class", "second class", "luggage compartment",
            "turnstile", "fare gate", "atvm machine", "ticket counter", "escalator",
            "lift", "elevator", "ac", "air conditioning", "fan", "platform gap",
            "indicator display", "pa speaker", "announcement", "door", "cctv",
            "security guard", "tc", "ticket checker", "handrail"
        ]
        for ak in aspect_keywords:
            if ak in clean_text:
                extracted_aspects.append(ak.title())

        return {
            "stations": list(dict.fromkeys(extracted_stations))[:4],
            "lines": list(dict.fromkeys(extracted_lines))[:3],
            "directions": list(dict.fromkeys(extracted_directions))[:2],
            "time_mentions": list(dict.fromkeys(extracted_time_mentions))[:3],
            "aspects": list(dict.fromkeys(extracted_aspects))[:4]
        }

    def resolve_location(self, extracted_stations: List[str], extracted_lines: List[str]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Resolves entity names to canonical IDs and names in the Mumbai transit GIS database.
        """
        st_id, st_name = None, None
        ln_id, ln_name = None, None

        if extracted_stations:
            first_st = extracted_stations[0].lower()
            for key, obj in self.known_stations.items():
                if key in first_st or first_st in key:
                    st_id = obj["id"]
                    st_name = obj["name"]
                    break
            if not st_name:
                st_name = extracted_stations[0]

        if extracted_lines:
            first_ln = extracted_lines[0].lower()
            for key, obj in self.known_lines.items():
                if key in first_ln or first_ln in key:
                    ln_id = obj["id"]
                    ln_name = obj["name"]
                    break
            if not ln_name:
                ln_name = extracted_lines[0]

        return ln_id, ln_name, st_id, st_name

# Global singleton
ner_extractor = TransitNERExtractor()
