import json
from pathlib import Path

def migrate_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    data.pop("playlist", None)
    data.pop("tag", None)

    info = data["info"]
    logo = info.pop("logo", None)
    if logo:
        info["icon"] = { "color": logo }

    for track_type in data.pop("fileGroups"):
        files = track_type["files"]

        for file in files:
            if "attaches" in file:
                file["voiceovers"] = file["attaches"]["files"]
                file.pop("attaches")

        data["fileGroups"][track_type["tag"]] = track_type["files"]

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def process_all_stations(root_dir):
    for station_file in root_dir.rglob("station.json"):
        migrate_json(station_file)
        print(f"Processed: {station_file}")
    print("Batch processing complete.")

script_dir = Path(__file__).resolve().parent
process_all_stations(script_dir.parents[1])
