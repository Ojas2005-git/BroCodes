from __future__ import annotations

import re
from pathlib import Path

from flask import Flask, render_template
from shapely import wkt

app = Flask(__name__)


DATA_PATH = Path(__file__).with_name("data.wkt")
CANVAS_SIZE = 600


def _extract_polygons(wkt_text: str) -> list[str]:
    return re.findall(r"POLYGON\s*\(\([^)]*\)\)", wkt_text, flags=re.DOTALL)


def _bounds(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _load_normalized_polygons(path: Path) -> list[list[list[float]]]:
    text = path.read_text()
    raw_polygons = _extract_polygons(text)
    if not raw_polygons:
        return []

    coords_list: list[list[tuple[float, float]]] = []
    for poly_text in raw_polygons:
        geom = wkt.loads(poly_text)
        if geom.geom_type == "Polygon":
            coords_list.append(list(geom.exterior.coords))
        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                coords_list.append(list(poly.exterior.coords))

    if not coords_list:
        return []

    all_points = [pt for poly in coords_list for pt in poly]
    min_x, min_y, max_x, max_y = _bounds(all_points)
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    size = max(max_x - min_x, max_y - min_y)

    normalized: list[list[list[float]]] = []
    for poly in coords_list:
        mapped: list[list[float]] = []
        for x, y in poly:
            nx = (x - center_x) / size
            ny = (y - center_y) / size
            mapped.append([nx, ny])
        normalized.append(mapped)

    return normalized


def _to_canvas_pixels(polygons: list[list[list[float]]], size: int) -> list[list[list[float]]]:
    pixel_polys: list[list[list[float]]] = []
    for poly in polygons:
        mapped: list[list[float]] = []
        for x, y in poly:
            px = (x * 0.9 + 0.5) * size
            py = (-y * 0.9 + 0.5) * size
            mapped.append([px, py])
        pixel_polys.append(mapped)
    return pixel_polys


@app.route("/")
def index():
    normalized = _load_normalized_polygons(DATA_PATH)
    pixels = _to_canvas_pixels(normalized, CANVAS_SIZE)
    return render_template(
        "index.html",
        polygons=pixels,
        canvas_size=CANVAS_SIZE,
    )


if __name__ == "__main__":
    app.run(debug=True)
