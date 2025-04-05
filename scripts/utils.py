
from pathlib import Path

data_dir = Path(__file__).resolve().parents[1]

def process_all_stations(callback):
    for station_file in data_dir.rglob("station.json"):
        callback(station_file)
        print(f"\nProcessed: {Path(*station_file.parts[-3:])}")
    print("Batch processing complete.")

def get_stations():
    return list(data_dir.rglob("station.json"))