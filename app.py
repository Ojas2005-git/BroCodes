from __future__ import annotations

import re
from pathlib import Path

import json

from flask import Flask, render_template
from shapely import wkt

app = Flask(__name__)


DATA_PATH = Path(__file__).with_name("data.wkt")
LABELS_PATH = Path(__file__).with_name("labels.json")
CANVAS_SIZE = 600


_GEOM_PATTERN = re.compile(
    r"\b(POLYGON|MULTIPOLYGON|LINESTRING|MULTILINESTRING)\b", re.IGNORECASE
)


def _extract_wkt_geometries(wkt_text: str) -> list[str]:
    geometries: list[str] = []
    for match in _GEOM_PATTERN.finditer(wkt_text):
        start = match.start()
        open_idx = wkt_text.find("(", match.end())
        if open_idx == -1:
            continue
        depth = 0
        i = open_idx
        while i < len(wkt_text):
            ch = wkt_text[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    geometries.append(wkt_text[start : i + 1])
                    break
            i += 1
    return geometries


def _bounds(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _load_normalized_shapes(
    path: Path,
) -> tuple[list[list[list[float]]], list[list[list[float]]]]:
    text = path.read_text()
    raw_geometries = _extract_wkt_geometries(text)
    if not raw_geometries:
        return [], []

    polygons: list[list[tuple[float, float]]] = []
    lines: list[list[tuple[float, float]]] = []
    for geom_text in raw_geometries:
        geom = wkt.loads(geom_text)
        if geom.geom_type == "Polygon":
            polygons.append(list(geom.exterior.coords))
        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                polygons.append(list(poly.exterior.coords))
        elif geom.geom_type == "LineString":
            lines.append(list(geom.coords))
        elif geom.geom_type == "MultiLineString":
            for line in geom.geoms:
                lines.append(list(line.coords))

    all_points = [pt for poly in polygons for pt in poly] + [
        pt for line in lines for pt in line
    ]
    if not all_points:
        return [], []
    min_x, min_y, max_x, max_y = _bounds(all_points)
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    size = max(max_x - min_x, max_y - min_y)

    normalized_polys: list[list[list[float]]] = []
    for poly in polygons:
        mapped: list[list[float]] = []
        for x, y in poly:
            nx = (x - center_x) / size
            ny = (y - center_y) / size
            mapped.append([nx, ny])
        normalized_polys.append(mapped)

    normalized_lines: list[list[list[float]]] = []
    for line in lines:
        mapped: list[list[float]] = []
        for x, y in line:
            nx = (x - center_x) / size
            ny = (y - center_y) / size
            mapped.append([nx, ny])
        normalized_lines.append(mapped)

    return normalized_polys, normalized_lines


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
    normalized_polys, normalized_lines = _load_normalized_shapes(DATA_PATH)
    pixel_polys = _to_canvas_pixels(normalized_polys, CANVAS_SIZE)
    pixel_lines = _to_canvas_pixels(normalized_lines, CANVAS_SIZE)
    label_name = "ELBE"
    if LABELS_PATH.exists():
        try:
            label_name = json.loads(LABELS_PATH.read_text()).get("name", label_name)
        except json.JSONDecodeError:
            pass
    return render_template(
        "index.html",
        polygons=pixel_polys,
        lines=pixel_lines,
        label_name=label_name,
        canvas_size=CANVAS_SIZE,
    )


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)
    