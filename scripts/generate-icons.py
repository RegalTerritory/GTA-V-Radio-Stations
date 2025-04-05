from typing import Dict, List, Tuple

import json
from pathlib import Path
import colorsys
import tempfile
import subprocess

from colorthief import ColorThief
from PIL import Image

from utils import get_stations

def batch_render_svgs_with_inkscape(input_output_pairs: List[Tuple[Path, Path]], export_height=512):
    """Render multiple svgs with inkscape.\n
    Requires inkscape to be available from commandline."""
    if not input_output_pairs:
        return
    actions = []
    for svg_path, png_path in input_output_pairs:
        actions.append(f"file-open:{svg_path}")
        actions.append(f"export-filename:{png_path}")
        actions.append("export-do")
        actions.append("file-close")
    action_string = ";".join(actions)
    dummy_file = input_output_pairs[-1][0]

    subprocess.run([
        "inkscape",
        "--batch-process",
        "--export-type=png",
        f"--export-height={export_height}",
        "--export-background-opacity=0",
        f"--actions={action_string}",
        str(dummy_file)
    ], check=True)

def get_dominant_color(png_path: Path):
    with open(png_path, "rb") as f:
        ct = ColorThief(f)
        return ct.get_color(quality=1)

def get_analogous_color(rgb, hue_shift=0.05):
    r, g, b = [x / 255 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    
    h = (h + hue_shift) % 1.0
    
    s *= 0.5  # Reduce saturation
    l = 0.75  # Lightness
    
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return tuple(int(x * 255) for x in (r2, g2, b2))

def svg_to_coverart(rendered_png_path: Path, output_path: Path, margin_x: int = 0, margin_y: int = 0):
    dominant = get_dominant_color(rendered_png_path)
    background = get_analogous_color(dominant)

    img = Image.open(rendered_png_path).convert("RGBA")

    drawable_width, drawable_height = img.size
    total_width = drawable_width + (2 * margin_x)
    total_height = drawable_height + (2 * margin_y)

    final_image = Image.new("RGBA", (total_width, total_height), background + (255,))
    final_image.paste(img, (margin_x, margin_y), mask=img)

    final_image.convert("RGB").save(output_path, "PNG")

def generate_coverart():
    target_height = 512
    padding_x = 30
    padding_y = 30

    station_files = get_stations()
    station_temp_png: Dict[str, Tuple[Path, Path]] = {}
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        input_output_pairs: List[Tuple[Path, Path]] = []

        for station_json_path in station_files:
            station_folder = station_json_path.parent
            with open(station_json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            icons = data["info"]["icon"]
            svg_path: Path = station_folder / (icons.get("full") or icons.get("color")) # get icon to use for cover art

            temp_png = tmpdir / f"{svg_path.stem}_temp.png"
            input_output_pairs.append((svg_path, temp_png))
            station_temp_png[svg_path.stem] = (station_json_path, temp_png)

        print("Collected list of svgs\nRendering...")

        drawable_height = target_height - (2 * padding_y)
        batch_render_svgs_with_inkscape(input_output_pairs, export_height=drawable_height)

        print("Batch rendered all svgs")

        for svg_name, (station_json_path, temp_png) in station_temp_png.items():
            station_folder = station_json_path.parent
            cover_art_filename = svg_name + "_cover.png"
            cover_art_path = station_folder / cover_art_filename

            svg_to_coverart(temp_png, cover_art_path, margin_x=padding_x, margin_y=padding_y)

            with open(station_json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            data["info"]["icon"]["cover"] = cover_art_filename

            with open(station_json_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)

            print(f"Saved cover art as {cover_art_filename}")

generate_coverart()
