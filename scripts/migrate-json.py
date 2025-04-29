import json
from pathlib import Path
from collections import defaultdict

from utils import process_all_stations, save_json, data_dir

def migrate_json_1(file_path: Path):
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

    save_json(file_path, data)

def resolve_station_tracklist_items(data, station_id) -> dict[str, dict]:
    tracklists = []
    for tracklist_id in data["Stations"][station_id]["TrackLists"]:
        tracklists.append((tracklist_id, data["TrackLists"][tracklist_id]))
    return tracklists

def simplify_markers(marker_list: list[dict[str, object]]):
    new_list = []
    for marker in marker_list:
        new_item = {}
        index: str
        for index, value in marker.items():
            if index == "Id":
                continue
            new_item[index.lower()] = value

        new_list.append(new_item)
    return new_list


track_id_map = {"mono_beyond_insemination_part_1": "mono_beyond_insemination", "mono_beyond_insemination_part_2": "mono_zbeyond_insemination_part_2", "mono_chakra_attack_part_2": "mono_dchakra_attack_part_2"}
def migrate_json_markers(file_path: Path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    with open(data_dir.parent / "dataDumps/info_merged.json", 'r', encoding='utf-8') as file:
        dumped_data = json.load(file)

    station_id = file_path.parent.name
    
    new_data = {"id": station_id}
    if data.get("type") != None:
        new_data["type"] = data["type"]
    new_data["info"] = data["info"]
    new_data["common"] = defaultdict(list)
    new_data["fileGroups"] = data["fileGroups"]

    dumped_tracklists = resolve_station_tracklist_items(dumped_data, station_id)
    common_adverts = {"general_adverts", "country_adverts"}
    for tracklist_id, tracklist in dumped_tracklists:
        if tracklist["Category"] != "0":
            continue

        if tracklist_id in common_adverts:
            if tracklist_id not in new_data["common"]["adverts"]:
                ad_list = new_data["common"]["adverts"]
                ad_list.append(tracklist_id)
            continue
        print("COULDN'T ADD ADVERT", tracklist_id)

    for track in new_data["fileGroups"]["track"]:
        if "tag" in track:
            del track["tag"]

        track_id = track["path"].rsplit(".", 1)[0]
        if track_id in track_id_map:
            track_id = track_id_map[track_id]

        found = None
        for tracklist_id, tracklist in dumped_tracklists:
            for dumped_track in tracklist["Tracks"]:
                if Path(dumped_track["Path"]).name == track_id:
                    found = dumped_track
                    break
            if found != None:
                break

        if found == None:
            print("NOT FOUND", track_id)
            continue
        
        if "voiceovers" in track:
            track["attachments"] = {"intro": track["voiceovers"]}
            del track["voiceovers"]

        if not found["Markers"]:
            print("NO MARKERS", track_id)
            continue
        
        track["markers"] = {
            "track": simplify_markers(found["Markers"]["Track"])
        }

        if "DJ" in found["Markers"]:
            track["markers"]["dj"] = simplify_markers(found["Markers"]["DJ"])
        else:
            print("NO DJ", track_id)

    save_json(file_path, new_data)

process_all_stations(migrate_json_markers)
