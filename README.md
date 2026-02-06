# BroCodes
HackArena 3.0

## WKT Canvas Demo

### Run
1. Install dependencies: `pip install flask shapely`
2. Start the server: `python app.py`
3. Open `http://127.0.0.1:5000/`

## Development Progress
-step one: collect a WKT file (`data.wkt`) that contains one or more `POLYGON` geometries.
-step two: start the Flask app (`app.py`), which reads the WKT text from disk.
-step three: extract each `POLYGON` text block with a regex and parse it with Shapely into geometry objects.
-step four: pull the exterior coordinates from each polygon and flatten them into a single list of points.
-step five: compute the overall bounds (min/max X and Y) across all points to get the map extents.
-step six: compute the center point as `(min + max) / 2` for X and Y, and the overall size as the larger of width/height.
-step seven: normalize every point by subtracting the center and dividing by the overall size; this centers the map at (0,0) and scales it to fit inside a unit square.
-step eight: map normalized points into canvas pixels by scaling to canvas size and flipping Y so the map renders upright.
-step nine: render the HTML template, pass the pixel polygons into the page, and draw them on the canvas in the browser.
