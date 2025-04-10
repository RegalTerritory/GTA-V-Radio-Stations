import json
import subprocess
import re
from pathlib import Path

from utils import data_dir, save_json

def get_total_duration(path: Path) -> float:
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(result.stdout.strip())

def get_audible_duration(file_path: Path, total_duration: float, silence_threshold="-14dB", silence_duration="0.5", analysis_tail=8) -> float:
    try:
        start_time = max(0, total_duration - analysis_tail)

        command = [
            "ffmpeg", "-ss", str(start_time), "-i", file_path,
            "-af", f"silencedetect=noise={silence_threshold}:d={silence_duration}",
            "-f", "null", "-"
        ]

        result = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        output = result.stderr

        silence_start_matches = re.findall(r"silence_start: (\d+\.?\d*)", output)
        if not silence_start_matches:
            return 0.0
        print(output)

        silence_start = float(silence_start_matches[-1])
        audible_duration = start_time + silence_start
        return min(audible_duration, total_duration)

    except Exception as e:
        print(f"Error: {e}")
        return -1.0

def setTrackDurations(station_name):
    station_json_path = data_dir / station_name / "station.json"

    with open(station_json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    for track in data["fileGroups"]["track"]:
        audio_file = station_json_path.parent / track["path"]
        length = round(get_total_duration(audio_file), 3)
        audible = round(get_audible_duration(audio_file, length), 3)

        track["duration"] = length

        if "audibleDuration" in track:
            del track["audibleDuration"]
        if audible > 0:
            dif = length - audible
            print(f"len: {length} | audible: {audible} | dif {dif} | path: {track["path"]}")
            if dif > 0.2:
                track["audibleDuration"] = audible

    save_json(station_json_path, data)

setTrackDurations("dlc_thelab")